from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd
from pathlib import Path
from pydantic import BaseModel, Field

app = FastAPI(title="Task Time Predictor API", description="API for predicting task duration categories based on task details.", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "duration_logistic_regression_classifier.joblib"

try:
    model = joblib.load(MODEL_PATH)
except Exception as e:
    raise RuntimeError(f"Failed to load model file: {e}")

class TaskInput(BaseModel):
    summary: str = Field(default="")
    description: str = Field(default="")
    issuetype_name: str = Field(default="unknown")
    priority_name: str = Field(default="unknown")
    project_key: str = Field(default="unknown")
    project_category_name: str = Field(default="unknown")
    created_year: int = Field(default=0)
    created_month: int = Field(default=0)
    labels_count: int = Field(default=0)
    has_assignee: int = Field(default=0)
    votes_votes: float = Field(default=0)
    watches_watch_count: float = Field(default=0)


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

@app.post("/predict")
async def predict_task_time(task: TaskInput):
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

    prediction = model.predict(features)[0]
    probabilities = model.predict_proba(features)[0]

    class_probabilities = {
        str(class_name): float(probability)
        for class_name, probability in zip(model.classes_, probabilities)
    }

    return {
        "duration_category": prediction,
        "probabilities": class_probabilities,
    }

