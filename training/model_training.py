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


df = pd.read_csv("data/processed/final_cleaned.csv")

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

# Model pipeline
model = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        (
            "classifier",
            LogisticRegression(
                max_iter=1000,
                class_weight="balanced",
                n_jobs=-1,
            ),
        ),
    ]
)

# Model training 

model.fit(x_train, y_train)

y_pred = model.predict(x_test)

report = classification_report(y_test, y_pred)
print(report)

# Save report
with open("../reports/classification_report.txt", "w") as f:
    f.write(report)

# Confusion matrix
ConfusionMatrixDisplay.from_predictions(
    y_test,
    y_pred,
    xticks_rotation=45
)

plt.title("Confusion Matrix")
plt.tight_layout()
plt.savefig("../reports/confusion_matrix.png")
plt.show()

# Save full pipeline
joblib.dump(
    model,
    "../models/duration_classifier.joblib",
    compress=3
)

print("Model saved.")