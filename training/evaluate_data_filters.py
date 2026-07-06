from pathlib import Path
import time

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLEANED_PATH = PROJECT_ROOT / "data" / "processed" / "jira_issues_cleaned.csv"
DURATION_ORDER = ["Short", "Standard", "Long-running"]


def duration_category(days):
    if days <= 3:
        return "Short"
    if days <= 15:
        return "Standard"
    return "Long-running"


def load_base_data():
    df = pd.read_csv(CLEANED_PATH)
    for column in ["created", "resolutiondate"]:
        df[column] = pd.to_datetime(df[column], errors="coerce")

    df["duration_days"] = (
        df["resolutiondate"] - df["created"]
    ).dt.total_seconds() / 86400
    df = df[
        df["duration_days"].notna()
        & (df["duration_days"] >= (2 / 24))
        & (df["duration_days"] <= 90)
    ].copy()
    df["duration_category"] = df["duration_days"].apply(duration_category)
    df["created_year"] = df["created"].dt.year
    df["created_month"] = df["created"].dt.month
    df["total_text"] = (
        df["summary"].fillna("").astype(str)
        + " "
        + df["description"].fillna("").astype(str)
    )
    return df


def apply_duration_windows(df, short_max, standard_min, standard_max, long_min):
    return df[
        ((df["duration_category"].eq("Short")) & (df["duration_days"] <= short_max))
        | (
            (df["duration_category"].eq("Standard"))
            & (df["duration_days"] >= standard_min)
            & (df["duration_days"] <= standard_max)
        )
        | (
            (df["duration_category"].eq("Long-running"))
            & (df["duration_days"] >= long_min)
        )
    ].copy()


def apply_group_consistency(df, group_columns, min_group_size, min_category_share):
    group_counts = (
        df.groupby(group_columns + ["duration_category"], observed=True)
        .size()
        .rename("category_count")
        .reset_index()
    )
    totals = (
        group_counts.groupby(group_columns, observed=True)["category_count"]
        .sum()
        .rename("group_count")
        .reset_index()
    )
    group_counts = group_counts.merge(totals, on=group_columns)
    group_counts["category_share"] = (
        group_counts["category_count"] / group_counts["group_count"]
    )
    keep_groups = group_counts[
        (group_counts["group_count"] >= min_group_size)
        & (group_counts["category_share"] >= min_category_share)
    ][group_columns + ["duration_category"]]

    return df.merge(keep_groups, on=group_columns + ["duration_category"], how="inner")


def balance_classes(df, max_rows_per_project_class, random_state=42):
    capped_parts = []
    for _, project_class_df in df.groupby(
        ["project_key", "duration_category"],
        observed=True,
    ):
        capped_parts.append(
            project_class_df.sample(
                n=min(len(project_class_df), max_rows_per_project_class),
                random_state=random_state,
            )
        )

    capped = pd.concat(capped_parts, ignore_index=True)

    class_counts = capped["duration_category"].value_counts()
    target_size = int(class_counts.min())
    balanced = pd.concat(
        [
            capped.loc[capped["duration_category"].eq(category)].sample(
                n=target_size,
                random_state=random_state,
            )
            for category in DURATION_ORDER
        ],
        ignore_index=True,
    )
    return balanced.sample(frac=1, random_state=random_state).reset_index(drop=True)


def evaluate(df, max_eval_rows=60_000):
    if len(df) > max_eval_rows:
        per_class = max_eval_rows // len(DURATION_ORDER)
        df = pd.concat(
            [
                df.loc[df["duration_category"].eq(category)].sample(
                    n=min(per_class, df["duration_category"].eq(category).sum()),
                    random_state=42,
                )
                for category in DURATION_ORDER
            ],
            ignore_index=True,
        ).sample(frac=1, random_state=42)

    categorical_features = [
        "priority_name",
        "issuetype_name",
        "project_key",
        "project_category_name",
        "created_year",
        "created_month",
    ]
    numeric_features = [
        "summary_char_count",
        "summary_word_count",
        "description_char_count",
        "description_word_count",
        "has_description",
        "labels_count",
        "has_assignee",
        "votes_votes",
        "watches_watch_count",
    ]

    x = df[["total_text"] + numeric_features + categorical_features]
    y = df["duration_category"]

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "text",
                TfidfVectorizer(
                    max_features=8000,
                    stop_words="english",
                    ngram_range=(1, 2),
                    min_df=5,
                    max_df=0.9,
                    sublinear_tf=True,
                ),
                "total_text",
            ),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_features,
            ),
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                LogisticRegression(
                    C=1.0,
                    solver="saga",
                    penalty="l2",
                    max_iter=600,
                    class_weight=None,
                    n_jobs=-1,
                    random_state=42,
                ),
            ),
        ]
    )

    started = time.time()
    model.fit(x_train, y_train)
    y_pred = model.predict(x_test)
    return accuracy_score(y_test, y_pred), classification_report(y_test, y_pred), time.time() - started


def main():
    base_df = load_base_data()
    configs = [
        {
            "name": "project_issue_share_33_100k",
            "windows": (2.25, 4, 14, 20),
            "group": (["project_key", "issuetype_name"], 20, 0.33),
            "project_cap": 3_000,
        },
        {
            "name": "project_issue_share_38",
            "windows": (2.25, 4, 14, 20),
            "group": (["project_key", "issuetype_name"], 25, 0.38),
            "project_cap": 1_500,
        },
        {
            "name": "project_issue_priority_share_35",
            "windows": (2.25, 4, 14, 20),
            "group": (["project_key", "issuetype_name", "priority_name"], 10, 0.35),
            "project_cap": 1_500,
        },
        {
            "name": "project_issue_priority_share_38",
            "windows": (2.25, 4, 14, 20),
            "group": (["project_key", "issuetype_name", "priority_name"], 10, 0.38),
            "project_cap": 1_500,
        },
        {
            "name": "project_category_issue_share_35",
            "windows": (2.25, 4, 14, 20),
            "group": (["project_category_name", "issuetype_name", "priority_name"], 25, 0.35),
            "project_cap": 1_500,
        },
    ]

    for config in configs:
        df = apply_duration_windows(base_df, *config["windows"])
        if config["group"]:
            df = apply_group_consistency(df, *config["group"])
        df = balance_classes(df, max_rows_per_project_class=config["project_cap"])
        print("=" * 80)
        print(config["name"])
        print(df.shape)
        print(df["duration_category"].value_counts().reindex(DURATION_ORDER).to_string())
        accuracy, report, seconds = evaluate(df)
        print(f"accuracy={accuracy:.4f} fit_seconds={seconds:.1f}")
        print(report)


if __name__ == "__main__":
    main()
