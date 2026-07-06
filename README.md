# Task Time Predictor (Beta Version)

> Predict whether a software issue is likely to be **Short**, **Standard**, or **Long-running** based on its summary, description, priority, and issue type.

![Python](https://img.shields.io/badge/Python-3.14-blue)
![FastAPI](https://img.shields.io/badge/API-FastAPI-green)
![Model](https://img.shields.io/badge/Model-Logistic%20Regression-purple)
![Docker](https://img.shields.io/badge/Deploy-Docker-informational)
![HuggingFace](https://img.shields.io/badge/-HuggingFace-3B4252?style=flat&logo=huggingface&logoColor=)

🤗 **Hugging Face:** https://huggingface.co/omaradly/jira-task-duration-classifier

📊 **Kaggle Dataset:** https://www.kaggle.com/datasets/tedlozzo/apaches-jira-issues

## Project Goal

This project turns cleaned Jira-style issue data into a deployed FastAPI service that predicts task duration categories. The goal is not exact day prediction, but a useful ordinal estimate:

```text
Short -> Standard -> Long-running
```

Because the target is ordinal, even an incorrect prediction is often only one neighboring category away.

## Folder Structure

```text
Task-Time-Predictor/
├── api/
│   └── main.py                         # FastAPI app and /predict endpoint
├── data/
│   └── processed/                      # Cleaned/sample datasets
├── models/
│   └── duration_logistic_regression_classifier.joblib
├── model_tests/
│   ├── classification_report.txt
│   └── confusion_matrix.png
├── notebooks/
│   ├── 01-exploratory-data-analysis.ipynb
│   ├── 02-data-cleaning.ipynb
│   └── 03-feature-engineering.ipynb
├── training/
│   └── model_training.py
├── Dockerfile
├── requirements.txt
└── .dockerignore
```

## Installation

Clone or update the repository:

```powershell
git clone https://github.com/OmarElgaafary/Task-Duration-Classifier
cd Task-Duration-Classifier
git pull
```

Build the Docker image:

```powershell
docker build -t task-duration-classifier .
```

Run the API container:

```powershell
docker run --rm -p 8000:8000 task-duration-classifier
```

Open the interactive API docs:

```text
http://localhost:8000/docs
```

## Workflow

1. **01 - Exploratory Data Analysis**
   - Inspect raw issue fields, missing values, text length patterns, and duration distribution.

2. **02 - Data Cleaning**
   - Remove unusable rows, normalize key fields, and prepare reliable issue records.

3. **03 - Feature Engineering**
   - Create model-ready fields such as text length counts, word counts, and duration categories.

4. **Model Training**
   - Train a classification pipeline in `training/model_training.py`.
   - Save the trained model to `models/`.
   - Save evaluation outputs to `model_tests/`.

5. **API Deployment**
   - `api/main.py` loads the saved `.joblib` model.
   - FastAPI exposes `POST /predict` for user requests.

## Model Design

The API builds the same core features expected by the trained pipeline:

- `total_text`: summary + description
- categorical fields: `priority_name`, `issuetype_name`
- numeric fields: summary/description character and word counts

The deployed model is Logistic Regression, which is a strong baseline for sparse text classification. It is fast to load, lightweight for Docker deployment, and easy to interpret compared with heavier tree or neural models.

## API Example

Request:

```json
{
  "summary": " Fix Cross-Origin Resource Sharing (CORS) error on /api/v2/users endpoint",
  "description": "Frontend requests to /api/v2/users are currently failing in the production environment due to a missing Access-Control-Allow-Origin header in the API response.",
  "issuetype_name": "Bug",
  "priority_name": "High"
}
```

Response:

```json
{
  "duration_category": "Standard"
}
```

## Metrics

Current evaluation output is stored in:

```text
model_tests/classification_report.txt
model_tests/confusion_matrix.png
```

Current test accuracy is approximately:

```text
Accuracy: 0.65
```

The confusion matrix is especially useful here because the classes are ordered. A wrong prediction may still be operationally useful if it lands one step away, such as `Short` predicted as `Standard`.

<img width="1920" height="1440" alt="confusion_matrix" src="https://github.com/user-attachments/assets/73cbfae4-805d-4a8c-80c6-119612b6bca3" />

## Future Improvements

Next commits can improve accuracy by:

- preserving richer Jira fields such as project, component, labels, assignee, or created-date features
- tuning Logistic Regression `C`, `penalty`, `solver`, and `max_iter`
- comparing calibrated linear models with XGBoost or LightGBM
- adding ordinal-aware evaluation, such as one-category-off accuracy
- separating production inference dependencies from training-only dependencies

## Production Notes

The Docker image should include only what the API needs:

```text
api/
models/
requirements.txt
```

Large raw and processed datasets are excluded through `.dockerignore` to keep the image smaller and reduce memory/storage overhead.
