import json
from pathlib import Path


NOTEBOOK_META = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    },
    "language_info": {
        "codemirror_mode": {"name": "ipython", "version": 3},
        "file_extension": ".py",
        "mimetype": "text/x-python",
        "name": "python",
        "nbconvert_exporter": "python",
        "pygments_lexer": "ipython3",
        "version": "3.13.5",
    },
}


def markdown_cell(source):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source.splitlines(keepends=True),
    }


def code_cell(source):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


def write_notebook(path, cells):
    notebook = {
        "cells": cells,
        "metadata": NOTEBOOK_META,
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.write_text(json.dumps(notebook, indent=1), encoding="utf-8")


root = Path(__file__).resolve().parents[1]

data_cleaning_cells = [
    markdown_cell(
        """# 02 - Data Cleaning

Create `data/processed/jira_issues_cleaned.csv` from the raw Jira export. This keeps only fields known before resolution, plus dates needed by the next notebook to create `duration_days`."""
    ),
    code_cell(
        """from pathlib import Path

import pandas as pd"""
    ),
    code_cell(
        """PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
RAW_PATH = PROJECT_ROOT / "jira_ticket_dataset.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RAW_COLUMNS = [
    "summary",
    "description",
    "priority.name",
    "issuetype.name",
    "project.key",
    "projectCategory.name",
    "votes.votes",
    "watches.watchCount",
    "labels",
    "assignee",
    "statusCategory.name",
    "created",
    "resolutiondate",
]

ticket_df = pd.read_csv(RAW_PATH, usecols=RAW_COLUMNS)

print(f"Raw rows loaded: {ticket_df.shape[0]:,}")
print(f"Raw columns loaded: {ticket_df.shape[1]:,}")"""
    ),
    code_cell(
        """created_dates = pd.to_datetime(ticket_df["created"], errors="coerce")
resolution_dates = pd.to_datetime(ticket_df["resolutiondate"], errors="coerce")

completed_issue_mask = (
    ticket_df["statusCategory.name"].eq("Done")
    & created_dates.notna()
    & resolution_dates.notna()
    & (resolution_dates >= created_dates)
)

rows_before = len(ticket_df)
clean_df = ticket_df.loc[completed_issue_mask].copy()

print(f"Rows before completed issue filtering: {rows_before:,}")
print(f"Rows after completed issue filtering: {len(clean_df):,}")
print(f"Rows removed: {rows_before - len(clean_df):,}")"""
    ),
    code_cell(
        """text_columns = ["summary", "description"]

for column in text_columns:
    clean_df[column] = (
        clean_df[column]
        .fillna("")
        .astype(str)
        .str.replace(r"\\s+", " ", regex=True)
        .str.strip()
    )

categorical_mappings = {
    "priority.name": "priority_name",
    "issuetype.name": "issuetype_name",
    "project.key": "project_key",
    "projectCategory.name": "project_category_name",
}

for source_column, clean_column in categorical_mappings.items():
    clean_df[clean_column] = (
        clean_df[source_column]
        .fillna("Unknown")
        .astype(str)
        .str.replace(r"\\s+", " ", regex=True)
        .str.strip()
        .replace("", "Unknown")
    )

clean_df["summary_char_count"] = clean_df["summary"].str.len()
clean_df["summary_word_count"] = clean_df["summary"].str.split().str.len()
clean_df["description_char_count"] = clean_df["description"].str.len()
clean_df["description_word_count"] = clean_df["description"].str.split().str.len()
clean_df["has_description"] = (clean_df["description_word_count"] > 0).astype(int)

labels_text = clean_df["labels"].fillna("[]").astype(str).str.strip()
clean_df["labels_count"] = labels_text.str.count(",") + labels_text.ne("[]").astype(int)
clean_df["has_assignee"] = clean_df["assignee"].notna().astype(int)
clean_df["votes_votes"] = pd.to_numeric(clean_df["votes.votes"], errors="coerce").fillna(0).clip(lower=0)
clean_df["watches_watch_count"] = pd.to_numeric(clean_df["watches.watchCount"], errors="coerce").fillna(0).clip(lower=0)

for column in ["created", "resolutiondate"]:
    clean_df[column] = pd.to_datetime(clean_df[column], errors="coerce")"""
    ),
    code_cell(
        """cleaned_model_columns = [
    "summary",
    "description",
    "priority_name",
    "issuetype_name",
    "project_key",
    "project_category_name",
    "summary_char_count",
    "summary_word_count",
    "description_char_count",
    "description_word_count",
    "has_description",
    "labels_count",
    "has_assignee",
    "votes_votes",
    "watches_watch_count",
    "created",
    "resolutiondate",
]

rows_before = len(clean_df)
model_df = clean_df[cleaned_model_columns].drop_duplicates().copy()

print(f"Rows before duplicate removal: {rows_before:,}")
print(f"Rows after duplicate removal: {len(model_df):,}")
print(f"Duplicate rows removed: {rows_before - len(model_df):,}")

missing_summary = pd.DataFrame({
    "missing_count": model_df.isna().sum(),
    "missing_percent": model_df.isna().mean().mul(100).round(2),
})
missing_summary.sort_values("missing_percent", ascending=False)"""
    ),
    code_cell(
        """csv_path = OUTPUT_DIR / "jira_issues_cleaned.csv"
sample_path = OUTPUT_DIR / "jira_issues_cleaned_sample.csv"

model_df.to_csv(csv_path, index=False)
model_df.sample(n=min(100, len(model_df)), random_state=42).to_csv(sample_path, index=False)

print(f"Saved cleaned CSV file to: {csv_path}")
print(f"Saved sample CSV file to: {sample_path}")
print(f"Final cleaned rows: {model_df.shape[0]:,}")
print(f"Final cleaned columns: {model_df.shape[1]:,}")"""
    ),
]

feature_engineering_cells = [
    markdown_cell(
        """# 03 - Feature Engineering

Build the modeling dataset from `jira_issues_cleaned.csv`. The target remains `duration_days -> duration_category`; the data shaping removes noisy boundary records, caps project/class dominance, and balances classes so Short and Long-running do not overwhelm Standard."""
    ),
    code_cell(
        """from pathlib import Path

import numpy as np
import pandas as pd"""
    ),
    code_cell(
        """PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "jira_issues_cleaned.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

jira_df = pd.read_csv(INPUT_PATH)
task_df = jira_df.copy()

for column in ["created", "resolutiondate"]:
    task_df[column] = pd.to_datetime(task_df[column], errors="coerce")

print(f"Cleaned source rows: {task_df.shape[0]:,}")
print(f"Cleaned source columns: {task_df.shape[1]:,}")"""
    ),
    code_cell(
        """task_df["duration_days"] = (
    task_df["resolutiondate"] - task_df["created"]
).dt.total_seconds() / (60 * 60 * 24)

rows_before = len(task_df)
task_df = task_df[
    task_df["duration_days"].notna()
    & (task_df["duration_days"] >= (2 / 24))
    & (task_df["duration_days"] <= 90)
].copy()

print(f"Rows before duration filtering: {rows_before:,}")
print(f"Rows after duration filtering: {len(task_df):,}")
task_df["duration_days"].describe(percentiles=[0.25, 0.5, 0.75, 0.9, 0.95, 0.99])"""
    ),
    code_cell(
        """def duration_category(days):
    if days <= 3:
        return "Short"
    if days <= 15:
        return "Standard"
    return "Long-running"


duration_order = ["Short", "Standard", "Long-running"]
task_df["duration_category"] = task_df["duration_days"].apply(duration_category)

class_summary = pd.DataFrame({
    "count": task_df["duration_category"].value_counts().reindex(duration_order),
    "percent": task_df["duration_category"]
        .value_counts(normalize=True)
        .reindex(duration_order)
        .mul(100)
        .round(2),
})

class_summary"""
    ),
    code_cell(
        """# Keep examples far enough from class boundaries that labels are more learnable.
# The target is still created from duration_days; this step removes noisy edge cases.
duration_window_mask = (
    (task_df["duration_category"].eq("Short") & (task_df["duration_days"] <= 2.25))
    | (
        task_df["duration_category"].eq("Standard")
        & task_df["duration_days"].between(4, 14, inclusive="both")
    )
    | (
        task_df["duration_category"].eq("Long-running")
        & (task_df["duration_days"] >= 20)
    )
)

rows_before = len(task_df)
task_df = task_df.loc[duration_window_mask].copy()

print(f"Rows removed outside stable duration windows: {rows_before - len(task_df):,}")
print(f"Rows after duration-window cleanup: {len(task_df):,}")"""
    ),
    code_cell(
        """# Keep project/issue-type combinations where duration class has historical signal.
# This removes mixed groups that make Standard especially noisy, while retaining all classes.
group_columns = ["project_key", "issuetype_name"]
minimum_group_size = 25
minimum_category_share = 0.35

group_counts = (
    task_df
    .groupby(group_columns + ["duration_category"], observed=True)
    .size()
    .rename("category_count")
    .reset_index()
)
group_totals = (
    group_counts
    .groupby(group_columns, observed=True)["category_count"]
    .sum()
    .rename("group_count")
    .reset_index()
)
group_counts = group_counts.merge(group_totals, on=group_columns)
group_counts["category_share"] = group_counts["category_count"] / group_counts["group_count"]

consistent_groups = group_counts.loc[
    (group_counts["group_count"] >= minimum_group_size)
    & (group_counts["category_share"] >= minimum_category_share),
    group_columns + ["duration_category"],
]

rows_before = len(task_df)
task_df = task_df.merge(
    consistent_groups,
    on=group_columns + ["duration_category"],
    how="inner",
)

print(f"Rows removed from low-signal project/issue groups: {rows_before - len(task_df):,}")
print(f"Rows after consistency filtering: {len(task_df):,}")
task_df["duration_category"].value_counts().reindex(duration_order)"""
    ),
    code_cell(
        """# Prevent a few large projects from dominating the classifier.
max_rows_per_project_class = 1_500

task_df = (
    task_df
    .groupby(["project_key", "duration_category"], group_keys=False, observed=True)
    .apply(
        lambda group: group.sample(
            n=min(len(group), max_rows_per_project_class),
            random_state=42,
        )
    )
    .reset_index(drop=True)
)


print(f"Rows after project/class cap: {len(task_df):,}")
task_df["duration_category"].value_counts().reindex(duration_order)"""
    ),
    code_cell(
        """# Balance classes without duplicating rows. Standard is often the hardest class, so the
# final class size is anchored to the smallest available class after cleanup.
class_counts = task_df["duration_category"].value_counts()
target_class_size = int(class_counts.min())

balanced_parts = []
for category in duration_order:
    category_df = task_df.loc[task_df["duration_category"].eq(category)]
    balanced_parts.append(
        category_df.sample(n=target_class_size, random_state=42)
    )

task_df = (
    pd.concat(balanced_parts, ignore_index=True)
    .sample(frac=1, random_state=42)
    .reset_index(drop=True)
)

balanced_summary = pd.DataFrame({
    "count": task_df["duration_category"].value_counts().reindex(duration_order),
    "percent": task_df["duration_category"]
        .value_counts(normalize=True)
        .reindex(duration_order)
        .mul(100)
        .round(2),
})

print(f"Target rows per class: {target_class_size:,}")
balanced_summary"""
    ),
    code_cell(
        """task_df["created_year"] = task_df["created"].dt.year
task_df["created_month"] = task_df["created"].dt.month

final_cleaned_columns = [
    "summary",
    "description",
    "priority_name",
    "issuetype_name",
    "project_key",
    "project_category_name",
    "summary_char_count",
    "summary_word_count",
    "description_char_count",
    "description_word_count",
    "has_description",
    "labels_count",
    "has_assignee",
    "votes_votes",
    "watches_watch_count",
    "created_year",
    "created_month",
    "duration_category",
]

final_cleaned_df = task_df[final_cleaned_columns].copy()

final_cleaned_path = OUTPUT_DIR / "final_cleaned.csv"
sample_path = OUTPUT_DIR / "final_cleaned_sample.csv"

final_cleaned_df.to_csv(final_cleaned_path, index=False)
final_cleaned_df.sample(n=min(100, len(final_cleaned_df)), random_state=42).to_csv(sample_path, index=False)

print(f"Saved final cleaned CSV file to: {final_cleaned_path}")
print(f"Saved sample CSV file to: {sample_path}")
print(f"Final modeling rows: {final_cleaned_df.shape[0]:,}")
print(f"Final modeling columns: {final_cleaned_df.shape[1]:,}")"""
    ),
]

write_notebook(root / "notebooks" / "02-data-cleaning.ipynb", data_cleaning_cells)
write_notebook(root / "notebooks" / "03-feature-engineering.ipynb", feature_engineering_cells)

print("Rebuilt data cleaning and feature engineering notebooks.")
