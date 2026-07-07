import logging
import os
import time
from collections import defaultdict
from functools import lru_cache
from fastapi import FastAPI
from fastapi import HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
from starlette.concurrency import run_in_threadpool
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Task Time Predictor API",
    description="API for predicting task duration categories based on task details.",
    version="1.0",
)


def parse_allowed_origins():
    configured_origins = {
        origin.strip().rstrip("/")
        for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    }

    vercel_url = os.getenv("VERCEL_URL", "").strip().rstrip("/")
    if vercel_url:
        configured_origins.add(
            vercel_url if vercel_url.startswith("http") else f"https://{vercel_url}"
        )

    local_origins = {
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    }

    return configured_origins | local_origins


ALLOWED_ORIGINS = parse_allowed_origins()
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "20"))
RATE_LIMIT_MAX_CLIENTS = int(os.getenv("RATE_LIMIT_MAX_CLIENTS", "2000"))
MAX_PREDICT_CONTENT_LENGTH = int(os.getenv("MAX_PREDICT_CONTENT_LENGTH", "8000"))
REQUEST_LOG = defaultdict(list)

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(ALLOWED_ORIGINS),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "duration_logistic_regression_classifier.joblib"


@lru_cache(maxsize=1)
def load_model():
    if not MODEL_PATH.exists():
        raise RuntimeError(f"Model file not found at {MODEL_PATH}")
    return joblib.load(MODEL_PATH)


class TaskInput(BaseModel):
    summary: str = Field(..., min_length=1, max_length=300)
    description: str = Field(default="", max_length=3000)
    issuetype_name: str = Field(default="unknown", max_length=80)
    priority_name: str = Field(default="unknown", max_length=80)
    project_key: str = Field(default="unknown", max_length=40)
    project_category_name: str = Field(default="unknown", max_length=120)
    created_year: int = Field(default=0, ge=0, le=2100)
    created_month: int = Field(default=0, ge=0, le=12)
    labels_count: int = Field(default=0, ge=0, le=100)
    has_assignee: int = Field(default=0, ge=0, le=1)
    votes_votes: float = Field(default=0, ge=0, le=1_000_000)
    watches_watch_count: float = Field(default=0, ge=0, le=1_000_000)

    @field_validator(
        "summary",
        "description",
        "issuetype_name",
        "priority_name",
        "project_key",
        "project_category_name",
        mode="before",
    )
    @classmethod
    def strip_text_fields(cls, value):
        return value.strip() if isinstance(value, str) else value


def origin_from_url(url):
    if not url:
        return None
    parsed_url = urlsplit(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        return None
    return f"{parsed_url.scheme}://{parsed_url.netloc}"


def request_origin(request):
    origin = request.headers.get("origin")
    if origin:
        return origin.rstrip("/")
    return origin_from_url(request.headers.get("referer"))


def client_key(request):
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_predict_security(request):
    content_length = request.headers.get("content-length")
    try:
        content_length_value = int(content_length) if content_length else 0
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Content-Length header.")

    if content_length_value > MAX_PREDICT_CONTENT_LENGTH:
        raise HTTPException(status_code=413, detail="Prediction request is too large.")

    origin = request_origin(request)
    if not origin or origin not in ALLOWED_ORIGINS:
        raise HTTPException(
            status_code=403,
            detail="Use the deployed app or its Swagger docs page to submit predictions.",
        )

    now = time.monotonic()
    key = client_key(request)
    if len(REQUEST_LOG) > RATE_LIMIT_MAX_CLIENTS:
        expired_keys = [
            request_key
            for request_key, timestamps in REQUEST_LOG.items()
            if not timestamps or now - max(timestamps) >= RATE_LIMIT_WINDOW_SECONDS
        ]
        for request_key in expired_keys:
            REQUEST_LOG.pop(request_key, None)
        if len(REQUEST_LOG) > RATE_LIMIT_MAX_CLIENTS:
            REQUEST_LOG.clear()

    recent_requests = [
        timestamp
        for timestamp in REQUEST_LOG[key]
        if now - timestamp < RATE_LIMIT_WINDOW_SECONDS
    ]
    if len(recent_requests) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Too many prediction requests. Please wait before trying again.",
        )
    recent_requests.append(now)
    REQUEST_LOG[key] = recent_requests


def api_metadata():
    return {
        "name": "Task Time Predictor API",
        "description": "API for predicting task duration categories based on task details.",
        "status": "Running",
        "model": {
            "type": "Logistic Regression",
            "classes": ["Short", "Standard", "Long-running"],
        },
        "endpoints": {
            "root": "/",
            "health": "/health",
            "predict": "/predict",
        },
    }


@app.get("/")
async def root():
    return api_metadata()


@app.get("/health")
async def health():
    return api_metadata()


def run_prediction(features):
    model = load_model()
    prediction = model.predict(features)[0]
    probabilities = model.predict_proba(features)[0]
    class_probabilities = {
        str(class_name): float(probability)
        for class_name, probability in zip(model.classes_, probabilities)
    }
    return str(prediction), class_probabilities


@app.post("/predict")
async def predict_task_time(task: TaskInput, request: Request):
    enforce_predict_security(request)

    summary = task.summary or ""
    description = task.description or ""
    summary_word_count = len(summary.split())
    description_word_count = len(description.split())
    summary_to_description_word_ratio = (
        summary_word_count / description_word_count
        if description_word_count
        else summary_word_count
    )
    issue_priority = f"{task.issuetype_name}__{task.priority_name}"

    features = pd.DataFrame([{
        "summary_text": summary,
        "description_text": description,
        "total_text": f"{summary} {description}",
        "priority_name": task.priority_name,
        "issuetype_name": task.issuetype_name,
        "project_key": task.project_key,
        "project_category_name": task.project_category_name,
        "created_year": task.created_year,
        "created_month": task.created_month,
        "issue_priority": issue_priority,
        "summary_char_count": len(summary),
        "summary_word_count": summary_word_count,
        "description_char_count": len(description),
        "description_word_count": description_word_count,
        "has_description": int(description_word_count > 0),
        "labels_count": task.labels_count,
        "has_assignee": task.has_assignee,
        "votes_votes": task.votes_votes,
        "watches_watch_count": task.watches_watch_count,
        "summary_to_description_word_ratio": summary_to_description_word_ratio,
    }])

    try:
        prediction, class_probabilities = await run_in_threadpool(
            run_prediction,
            features,
        )
    except Exception as e:
        logger.exception("Prediction failed")
        raise HTTPException(
            status_code=503,
            detail="Prediction service is temporarily unavailable.",
        ) from e

    return {
        "duration_category": prediction,
        "probabilities": class_probabilities,
    }

