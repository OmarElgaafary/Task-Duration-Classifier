from fastapi import FastAPI
import joblib
import pandas as pd
from pathlib import Path
from pydantic import BaseModel, Field

app = FastAPI(title="Task Time Predictor API", description="API for predicting task duration categories based on task details.", version="1.0")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "duration_classifier.joblib"

try:
    model = joblib.load(MODEL_PATH)
except Exception as e:
    raise RuntimeError(f"Failed to load model file: {e}")

class TaskInput(BaseModel):
    summary: str = Field(default="")
    description: str = Field(default="")
    issuetype_name: str = Field(default="unknown")
    priority_name: str = Field(default="unknown")


@app.get("/")
async def root():
    return {"message": "Welcome to the Task Time Predictor API!"}

@app.post("/predict")
async def predict_task_time(task: TaskInput):
    summary = task.summary or ""
    description = task.description or ""

    features = pd.DataFrame([{
        "total_text": f"{summary} {description}",
        "priority_name": task.priority_name,
        "issuetype_name": task.issuetype_name,
        "summary_char_count": len(summary),
        "summary_word_count": len(summary.split()),
        "description_char_count": len(description),
        "description_word_count": len(description.split()),
    }])

    prediction = model.predict(features)[0]

    return {"duration_category": prediction}    
