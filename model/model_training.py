import pandas as pd
from sklearn.model_selection import train_test_split

tasks_final_df = pd.read_csv("../data/processed/final_cleaned.csv")

task_df = tasks_final_df.copy()
task_df = task_df.drop(columns="duration_days")

x = task_df.drop(columns=["duration_days", "duration_category"])
y = task_df["duration_category"]

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2)