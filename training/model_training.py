import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path

from sklearn.compose import ColumnTransformer
from sklearn.decomposition import TruncatedSVD
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.pipeline import Pipeline

from xgboost import XGBClassifier


# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "final_cleaned_sample.csv"
MODEL_TESTS_DIR = PROJECT_ROOT / "model_tests"
MODELS_DIR = PROJECT_ROOT / "models"

MODEL_TESTS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)


# Load data
tasks_final_df = pd.read_csv(DATA_PATH)

task_df = tasks_final_df.copy()

# Remove leakage column
task_df = task_df.drop(columns=["duration_days"])

# Create combined text feature
task_df["total_text"] = (
    task_df["summary"].fillna("").astype(str) + " " +
    task_df["description"].fillna("").astype(str)
)


# Feature groups
categorical_cols = [
    "priority_name",
    "issuetype_name",
]

numeric_cols = [
    "summary_char_count",
    "summary_word_count",
    "description_char_count",
    "description_word_count",
]

text_col = "total_text"
target_col = "duration_category"


# X and y
X = task_df[[text_col] + categorical_cols + numeric_cols]
y = task_df[target_col]


# Encode target labels for XGBoost
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)


# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y_encoded,
    test_size=0.2,
    stratify=y_encoded,
    random_state=42,
)


# Text pipeline: TF-IDF -> SVD
text_pipeline = Pipeline(
    steps=[
        (
            "tfidf",
            TfidfVectorizer(
                max_features=50000,
                stop_words="english",
                ngram_range=(1, 2),
                min_df=3,
                max_df=0.9,
                sublinear_tf=True,
                dtype=np.float32,
            ),
        ),
        (
            "svd",
            TruncatedSVD(
                n_components=300,
                random_state=42,
            ),
        ),
    ]
)


# Categorical pipeline
categorical_pipeline = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="constant", fill_value="unknown")),
        (
            "encoder",
            OneHotEncoder(
                handle_unknown="ignore",
                sparse_output=False,
                dtype=np.float32,
            ),
        ),
    ]
)


# Numeric pipeline
numeric_pipeline = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="constant", fill_value=0)),
    ]
)


# Full preprocessing
preprocessor = ColumnTransformer(
    transformers=[
        ("text", text_pipeline, text_col),
        ("cat", categorical_pipeline, categorical_cols),
        ("num", numeric_pipeline, numeric_cols),
    ],
    sparse_threshold=0,
)


# XGBoost model pipeline
xgb_pipeline = Pipeline(
    steps=[
        ("features", preprocessor),
        (
            "clf",
            XGBClassifier(
                objective="multi:softprob",
                num_class=len(label_encoder.classes_),
                eval_metric="mlogloss",
                tree_method="hist",
                n_estimators=800,
                learning_rate=0.03,
                max_depth=6,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_lambda=1.0,
                random_state=42,
                n_jobs=-1,
            ),
        ),
    ]
)


# Train
xgb_pipeline.fit(X_train, y_train)


# Predict
y_pred_encoded = xgb_pipeline.predict(X_test)

y_pred = label_encoder.inverse_transform(y_pred_encoded)
y_test_labels = label_encoder.inverse_transform(y_test)


# Evaluate
accuracy = accuracy_score(y_test_labels, y_pred)
macro_f1 = f1_score(y_test_labels, y_pred, average="macro")
report = classification_report(y_test_labels, y_pred)

print("Accuracy:", accuracy)
print("Macro F1:", macro_f1)
print(report)


# Save classification report
report_path = MODEL_TESTS_DIR / "xgboost_classification_report.txt"

with open(report_path, "w") as f:
    f.write(f"Accuracy: {accuracy:.4f}\n")
    f.write(f"Macro F1: {macro_f1:.4f}\n\n")
    f.write(report)


# Save confusion matrix
ConfusionMatrixDisplay.from_predictions(
    y_test_labels,
    y_pred,
    xticks_rotation=45,
)

plt.title("XGBoost Confusion Matrix")
plt.tight_layout()

confusion_matrix_path = MODEL_TESTS_DIR / "xgboost_confusion_matrix.png"
plt.savefig(confusion_matrix_path)
plt.close()


# Save model pipeline and label encoder together
model_bundle = {
    "model": xgb_pipeline,
    "label_encoder": label_encoder,
}

model_path = MODELS_DIR / "xgboost_duration_classifier.joblib"

joblib.dump(model_bundle, model_path, compress=3)

print(f"Model saved to: {model_path}")
print(f"Report saved to: {report_path}")
print(f"Confusion matrix saved to: {confusion_matrix_path}")
