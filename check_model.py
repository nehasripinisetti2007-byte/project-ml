
import pandas as pd
from pathlib import Path
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split

from app import model, predict_news
from news_text import clean_text

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "dataset"

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
for column in ("title", "text"):
    data[column] = data[column].fillna("").astype(str)

data["content"] = data["title"] + " " + data["text"]
data = data[data["content"].str.strip().str.len() > 20]
data = data.drop_duplicates(subset=["content"])
data = data.sample(frac=1, random_state=42).reset_index(drop=True)
_, test_data = train_test_split(
    data,
    test_size=0.20,
    random_state=42,
    stratify=data["label"]
)

for input_name, texts in (
    ("full articles", test_data["content"]),
    ("headlines", test_data["title"]),
):
    cleaned_texts = texts.apply(clean_text)
    predictions = model.predict(cleaned_texts)
    labels = test_data["label"].to_numpy()
    accuracy = accuracy_score(labels, predictions)
    matrix = confusion_matrix(labels, predictions, labels=[0, 1])
    fake_recall = matrix[0, 0] / matrix[0].sum()
    real_recall = matrix[1, 1] / matrix[1].sum()

    print(
        f"{input_name}: accuracy={accuracy:.4f}, "
        f"fake recall={fake_recall:.4f}, real recall={real_recall:.4f}"
    )

    if min(fake_recall, real_recall) < 0.80:
        raise SystemExit(
            f"FAIL: {input_name} recall for one class is below 0.80."
        )

verified_path = DATA_DIR / "VerifiedExamples.csv"
if verified_path.exists():
    verified_examples = pd.read_csv(verified_path).fillna("")
    required_columns = {"title", "text", "label"}
    missing_columns = required_columns.difference(verified_examples.columns)
    if missing_columns:
        raise ValueError(
            f"VerifiedExamples.csv is missing required columns: "
            f"{', '.join(sorted(missing_columns))}"
        )
    if not verified_examples["label"].isin([0, 1]).all():
        raise ValueError("VerifiedExamples.csv labels must be 0 (fake) or 1 (real).")

    for _, row in verified_examples.iterrows():
        label = int(row["label"])
        for input_name, news in (
            ("article", f"{row['title']} {row['text']}"),
            ("headline", str(row["title"])),
        ):
            prediction = predict_news(news)
            if prediction != label:
                expected = "REAL NEWS" if label == 1 else "FAKE NEWS"
                actual = "REAL NEWS" if prediction == 1 else "FAKE NEWS"
                raise SystemExit(
                    f"FAIL: verified {input_name} {row['title']!r}: "
                    f"expected {expected}, got {actual}."
                )

print("PASS: held-out class-balance and verified-example checks passed.")
