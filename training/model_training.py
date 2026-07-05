from pathlib import Path

import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, ConfusionMatrixDisplay
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

dataset_path = PROJECT_ROOT / "data" / "processed" / "final_cleaned.csv"
model_metric_test_path = PROJECT_ROOT / "model_tests"
models_dir = PROJECT_ROOT / "models"

model_metric_test_path.mkdir(parents=True, exist_ok=True)
models_dir.mkdir(parents=True, exist_ok=True)

if not dataset_path.exists():
    raise FileNotFoundError("Dataset not found.")

dataset_path = PROJECT_ROOT / "data" / "processed" / "final_cleaned.csv"

df = pd.read_csv(dataset_path)

df["total_text"] = (df["summary"].fillna("").astype(str) + " " + df["description"].fillna("").astype(str))

categorical_features = [
    "priority_name",
    "issuetype_name",
]

numeric_features = [
    "summary_char_count",
    "summary_word_count",
    "description_char_count",
    "description_word_count",
]

target_col = "duration_category"

# X -> Independent Variables (all except duration_category), y -> Dependent Variable (duration_category)

x = df[["total_text"] + numeric_features + categorical_features]
y = df[target_col]

# Split data
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42, stratify=y)

# Preprocessing pipeline
preprocessor = ColumnTransformer(
    transformers=[
        (
            "text",
            TfidfVectorizer(
                max_features=10000,
                stop_words="english",
                ngram_range=(1, 2),
                min_df=5,
                max_df=0.9,
            ),
            "total_text",
        ),
        (
            "cat",
            OneHotEncoder(handle_unknown="ignore"),
            categorical_features,
        ),
        (
            "num",
            StandardScaler(),
            numeric_features,
        ),
    ]
)

# class_weight={
#     "Short": 1.0,
#     "Standard": 1.0,
#     "Long-running": 1.5,
# }

# Model pipeline
model = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        (
            "classifier",
            LogisticRegression(
                C=1.0,
                solver="saga",
                penalty="l2",
                max_iter=3000,
                class_weight=None,
                random_state=42,
            )
        ),
    ]
)

# Train
model.fit(x_train, y_train)

# Evaluate
y_pred = model.predict(x_test)

report = classification_report(y_test, y_pred)
print(report)

with open(model_metric_test_path / "classification_report.txt", "w", encoding="utf-8") as f:
    f.write(report)

ConfusionMatrixDisplay.from_predictions(y_test, y_pred, xticks_rotation=45)

plt.title("Confusion Matrix")
plt.tight_layout()
plt.savefig(model_metric_test_path / "confusion_matrix.png", dpi=300)
plt.close()

# Save model
joblib.dump(model, models_dir / "duration_logistic_regression_classifier.joblib", compress=3)

print("Model saved.")