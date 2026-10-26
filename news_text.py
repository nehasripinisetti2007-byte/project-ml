import re

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS


STOP_WORDS = ENGLISH_STOP_WORDS.difference({"no", "nor", "not", "never"})


def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[^\w\s]", " ", text)

    return " ".join(
        word for word in text.split()
        if word not in STOP_WORDS
    )
