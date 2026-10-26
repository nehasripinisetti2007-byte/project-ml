
import joblib
import json
import pandas as pd

from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay
)
import matplotlib.pyplot as plt

from news_text import clean_text


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "dataset"
MODEL_DIR = BASE_DIR / "model"
STATIC_DIR = BASE_DIR / "static"
MODEL_DIR.mkdir(exist_ok=True)


# ==========================================
# 4. LOAD DATASETS
# ==========================================

print("\nLoading datasets...")

fake = pd.read_csv(DATA_DIR / "Fake.csv")
real = pd.read_csv(DATA_DIR / "True.csv")

for dataset_name, dataset in (("Fake.csv", fake), ("True.csv", real)):
    missing_columns = {"title", "text"}.difference(dataset.columns)
    if missing_columns:
        raise ValueError(
            f"{dataset_name} is missing required columns: "
            f"{', '.join(sorted(missing_columns))}"
        )

fake["label"] = 0
real["label"] = 1

data = pd.concat([fake, real], ignore_index=True)

for col in ["title", "text"]:
    if col not in data.columns:
        data[col] = ""
    data[col] = data[col].fillna("").astype(str)

data["content"] = data["title"] + " " + data["text"]
data = data[data["content"].str.strip().str.len() > 20]
data = data.drop_duplicates(subset=["content"])
data = data.sample(frac=1, random_state=42).reset_index(drop=True)

print("Fake articles:", (data["label"] == 0).sum())
print("Real articles:", (data["label"] == 1).sum())
print("Total articles:", len(data))


# ==========================================
# 5. PREPARE INPUT AND LABELS
# ==========================================

X = data["content"].apply(clean_text)
y = data["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

# Train on headlines as well as full articles without using held-out rows.
title_examples = data.loc[X_train.index, ["title", "label"]].copy()
title_examples["title"] = title_examples["title"].str.strip()
title_examples = title_examples[title_examples["title"] != ""]
X_train = pd.concat(
    [X_train, title_examples["title"].apply(clean_text)],
    ignore_index=True
)
y_train = pd.concat(
    [y_train, title_examples["label"].reset_index(drop=True)],
    ignore_index=True
)

verified_path = DATA_DIR / "VerifiedExamples.csv"
verified = pd.DataFrame(columns=["title", "text", "label", "content"])
if verified_path.exists():
    verified = pd.read_csv(verified_path)
    required_columns = {"title", "text", "label"}
    missing_columns = required_columns.difference(verified.columns)
    if missing_columns:
        raise ValueError(
            f"{verified_path} is missing required columns: "
            f"{', '.join(sorted(missing_columns))}"
        )

    if not verified["label"].isin([0, 1]).all():
        raise ValueError(f"{verified_path} labels must be 0 (fake) or 1 (real).")

    verified["content"] = (
        verified["title"].fillna("").astype(str)
        + " "
        + verified["text"].fillna("").astype(str)
    )
    verified["title"] = verified["title"].fillna("").astype(str).str.strip()
    verified = verified[
        verified["content"].str.strip().str.len() > 20
    ]
    # Weight verified examples against 60,000 baseline articles
    v_rep = pd.concat([verified] * 150, ignore_index=True)
    X_train = pd.concat(
        [X_train, v_rep["content"].apply(clean_text)],
        ignore_index=True
    )
    y_train = pd.concat(
        [y_train, v_rep["label"].astype(int)],
        ignore_index=True
    )
    verified_titles = v_rep[v_rep["title"] != ""]
    X_train = pd.concat(
        [X_train, verified_titles["title"].apply(clean_text)],
        ignore_index=True
    )
    y_train = pd.concat(
        [y_train, verified_titles["label"].astype(int).reset_index(drop=True)],
        ignore_index=True
    )
    print("Verified training examples (weighted):", len(v_rep))


print("Training records:", len(X_train))
print("Testing records:", len(X_test))


# ==========================================
# 6. DEFINE THREE MODELS
# ==========================================

models = {
    "Logistic Regression": LogisticRegression(
        max_iter=1000
    ),

    "SVM": LinearSVC(),

    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        n_jobs=-1
    )
}


# ==========================================
# 7. TRAIN AND EVALUATE
# ==========================================

results = []
trained_models = {}
confusion_matrices = {}
test_predictions_by_model = {}

for name, classifier in models.items():

    print("\nTraining:", name)

    # Keep TF-IDF and classifier together so
    # prediction uses the same vectorizer.
    pipeline = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                max_features=50000,
                ngram_range=(1, 2),
                min_df=2,
                sublinear_tf=True
            )
        ),
        ("classifier", classifier)
    ])

    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)
    title_predictions = pipeline.predict(
        data.loc[X_test.index, "title"].apply(clean_text)
    )
    test_predictions_by_model[name] = predictions
    confusion_matrices[name] = confusion_matrix(
        y_test,
        predictions,
        labels=[0, 1]
    ).tolist()

    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(
        y_test, predictions, zero_division=0
    )
    recall = recall_score(
        y_test, predictions, zero_division=0
    )
    f1 = f1_score(
        y_test, predictions, zero_division=0
    )
    headline_accuracy = accuracy_score(y_test, title_predictions)
    headline_f1 = f1_score(
        y_test, title_predictions, zero_division=0
    )
    selection_f1 = (f1 + headline_f1) / 2

    print("Accuracy :", round(accuracy, 4))
    print("Precision:", round(precision, 4))
    print("Recall   :", round(recall, 4))
    print("F1 Score :", round(f1, 4))
    print("Headline accuracy:", round(headline_accuracy, 4))
    print("Headline F1 Score:", round(headline_f1, 4))
    print("Combined F1 Score:", round(selection_f1, 4))

    print(classification_report(
        y_test,
        predictions,
        labels=[0, 1],
        target_names=["Fake", "Real"],
        zero_division=0
    ))

    results.append({
        "Model": name,
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1 Score": f1,
        "Headline Accuracy": headline_accuracy,
        "Headline F1 Score": headline_f1,
        "Combined F1 Score": selection_f1
    })

    trained_models[name] = pipeline


# ==========================================
# 8. COMPARE MODELS
# ==========================================

results_df = pd.DataFrame(results)

print("\nMODEL COMPARISON")
print(results_df.to_string(index=False))

STATIC_DIR.mkdir(exist_ok=True)
results_df.to_csv(MODEL_DIR / "model_comparison.csv", index=False)

# Balance full-article and headline performance when selecting the model.
best_name = results_df.loc[
    results_df["Combined F1 Score"].idxmax(),
    "Model"
]

best_model = trained_models[best_name]

print("\nSelected model:", best_name)

for _, row in verified.iterrows():
    news = clean_text(row["content"])
    prediction = int(best_model.predict([news])[0])
    if prediction != int(row["label"]):
        raise RuntimeError(
            f"Selected model misclassified verified example: {row['title']}"
        )


# ==========================================
# 9. SAVE MODEL AND MODEL NAME
# ==========================================

joblib.dump(best_model, MODEL_DIR / "fake_news_model.pkl")

# Save all three models for concurrent multi-model inference
if "Logistic Regression" in trained_models:
    joblib.dump(trained_models["Logistic Regression"], MODEL_DIR / "model_logistic_regression.pkl")
if "SVM" in trained_models:
    joblib.dump(trained_models["SVM"], MODEL_DIR / "model_svm.pkl")
if "Random Forest" in trained_models:
    joblib.dump(trained_models["Random Forest"], MODEL_DIR / "model_random_forest.pkl")

# The pipeline already includes TF-IDF.
# Save the vectorizer separately for compatibility.
joblib.dump(
    best_model.named_steps["tfidf"],
    MODEL_DIR / "tfidf_vectorizer.pkl"
)

with open(MODEL_DIR / "best_model.txt", "w", encoding="utf-8") as file:
    file.write(best_name)

print("Saved model and vectorizer.")


# ==========================================
# 10. CONFUSION MATRICES
# ==========================================

cm = confusion_matrix(
    y_test,
    test_predictions_by_model[best_name],
    labels=[0, 1]
)

with open(STATIC_DIR / "confusion_matrix.json", "w", encoding="utf-8") as file:
    json.dump({
        "labels": ["Fake", "Real"],
        "models": confusion_matrices
    }, file, indent=2)

disp = ConfusionMatrixDisplay(
    confusion_matrix=cm,
    display_labels=["Fake", "Real"]
)

disp.plot()
plt.title("Confusion Matrix - " + best_name)
plt.tight_layout()
plt.savefig(MODEL_DIR / "confusion_matrix.png")
plt.savefig(STATIC_DIR / "confusion_matrix.png")
plt.close()


# ==========================================
# 11. MODEL COMPARISON GRAPH
# ==========================================

results_df.set_index("Model")[
    [
        "Accuracy",
        "Precision",
        "Recall",
        "F1 Score",
        "Headline Accuracy",
        "Headline F1 Score"
    ]
].plot(kind="bar", figsize=(10, 6))

plt.title("Machine Learning Model Comparison")
plt.ylabel("Score")
plt.ylim(0, 1)
plt.xticks(rotation=0, ha="center")
plt.tight_layout()
plt.savefig(MODEL_DIR / "model_comparison.png")
plt.savefig(STATIC_DIR / "model_comparison.png")
plt.close()


# ==========================================
# 12. TEST SAMPLE NEWS
# ==========================================

test_news = [
    "NASA launched a scientific mission to study the Sun.",
    "The Earth revolves around the Sun.",
    "A magical drink can cure every disease in five minutes.",
    "Forward this message to ten people to receive one crore rupees."
]

print("\nSAMPLE PREDICTIONS")
print("These are model predictions, not verified facts.")

for news in test_news:
    cleaned = clean_text(news)
    prediction = int(best_model.predict([cleaned])[0])

    label = "REAL NEWS" if prediction == 1 else "FAKE NEWS"

    print("\nNews:", news)
    print("Prediction:", label)


# ==========================================
# 13. FINISH
# ==========================================

print("\n================================")
print("TRAINING COMPLETED")
print("Best model:", best_name)
print("Saved files inside the model folder.")
print("================================")
