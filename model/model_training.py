import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import StandardScaler

tasks_final_df = pd.read_csv("../data/processed/final_cleaned.csv")

task_df = tasks_final_df.copy()
task_df = task_df.drop(columns="duration_days")

task_df.head()

x = task_df.drop(columns=["duration_category"])
y = task_df["duration_category"]

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2)

# 1 - Apply TF-IDF vectorization to text-based features (summary, description) 

vectorizor = TfidfVectorizer()

x_train_text = vectorizor.fit_transform(x_train)
x_test_text = vectorizor.transform(x_test)

# 2 - Apply One Hot Encoder to categorical features (issuetype_name, priority_name)

ohenc = OneHotEncoder()

x_train_cat = ohenc.fit_transform(x_train[["issuetype_name", "priority_name"]])
x_test_cat = ohenc.transform(x_test[["issuetype_name", "priority_name"]])

# 3 - Apply Standard Scaler to numerical features (summary_length, description_length, summary_word_count, description_word_count)

num_features = ["summary_word_count", "description_word_count", "summary_char_count", "description_char_count"]

scaler = StandardScaler()

x_train_num = scaler.fit_transform(x_train[num_features])
x_test_num = scaler.transform(x_test[num_features])

