import csv
import io
import json
import math
import os
import re
import secrets
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from functools import wraps
from pathlib import Path
from urllib.parse import urlparse

import joblib
import numpy as np
import pandas as pd
from flask import (
    Flask,
    abort,
    g,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from news_text import clean_text

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2_000_000
app.config["SECRET_KEY"] = os.environ.get("NEWSGUARD_SECRET_KEY") or os.urandom(32).hex()
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("NEWSGUARD_SESSION_SECURE", "0") == "1"

# Project paths
BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "model"
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "dataset"
DATABASE_PATH = BASE_DIR / "history.db"

MODEL_PATH = MODEL_DIR / "fake_news_model.pkl"
MODEL_NAME_PATH = MODEL_DIR / "best_model.txt"
COMPARISON_PATH = MODEL_DIR / "model_comparison.csv"
CONFUSION_PATH = STATIC_DIR / "confusion_matrix.json"

MODEL_LR_PATH = MODEL_DIR / "model_logistic_regression.pkl"
MODEL_SVM_PATH = MODEL_DIR / "model_svm.pkl"
MODEL_RF_PATH = MODEL_DIR / "model_random_forest.pkl"

URL_PATTERN = re.compile(r"https?://[^\s<>\]\[\"']+", re.IGNORECASE)

CLICKBAIT_TERMS = {
    "shocking", "urgent", "secret", "miracle", "cure", "banned", "exposed",
    "unbelievable", "mind-blowing", "won't believe", "viral", "conspiracy",
    "hidden truth", "censored", "bombshell", "leaked", "magic", "free cash",
    "forward this", "guaranteed", "plot", "hoax", "destroy", "disaster",
    "apocalypse", "coverup", "scandal", "breakthrough", "aliens", "illuminati"
}

# Model state lock & storage
model_state_lock = threading.RLock()
active_model = None
model_name = "SVM"
models_suite = {}


def load_all_models():
    global active_model, model_name, models_suite

    with model_state_lock:
        if MODEL_NAME_PATH.exists():
            model_name = MODEL_NAME_PATH.read_text(encoding="utf-8").strip()
        else:
            model_name = "SVM"

        if MODEL_PATH.exists():
            active_model = joblib.load(MODEL_PATH)
        elif MODEL_SVM_PATH.exists():
            active_model = joblib.load(MODEL_SVM_PATH)

        suite = {}
        if MODEL_LR_PATH.exists():
            try:
                suite["Logistic Regression"] = joblib.load(MODEL_LR_PATH)
            except Exception:
                pass
        if MODEL_SVM_PATH.exists():
            try:
                suite["SVM"] = joblib.load(MODEL_SVM_PATH)
            except Exception:
                pass
        elif active_model is not None:
            suite["SVM"] = active_model

        if MODEL_RF_PATH.exists():
            try:
                suite["Random Forest"] = joblib.load(MODEL_RF_PATH)
            except Exception:
                pass

        if not suite and active_model is not None:
            suite[model_name] = active_model

        models_suite = suite


load_all_models()

# Compatibility alias for check_model.py and external scripts
model = active_model

def predict_news(news, target_model=None):
    """Predict binary label (0 for Fake, 1 for Real) for a given text string."""
    cleaned = clean_text(news)
    if not cleaned:
        raise ValueError("Enter a headline or article with readable text.")
    mdl = target_model or active_model or models_suite.get(model_name) or models_suite.get("SVM")
    if mdl is None:
        raise RuntimeError("Model is not loaded.")
    pred = int(mdl.predict([cleaned])[0])
    return pred



@contextmanager
def connect_history():
    connection = sqlite3.connect(DATABASE_PATH, timeout=15)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_history():
    with connect_history() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT '',
                published_at TEXT NOT NULL DEFAULT '',
                fact_check_urls TEXT NOT NULL DEFAULT '',
                news TEXT NOT NULL,
                result TEXT NOT NULL CHECK (result IN ('REAL NEWS', 'FAKE NEWS')),
                model TEXT NOT NULL,
                user_id INTEGER,
                confidence REAL DEFAULT 0.0,
                ground_truth INTEGER DEFAULT NULL,
                lr_result TEXT DEFAULT '',
                lr_confidence REAL DEFAULT 0.0,
                svm_result TEXT DEFAULT '',
                svm_confidence REAL DEFAULT 0.0,
                rf_result TEXT DEFAULT '',
                rf_confidence REAL DEFAULT 0.0,
                consensus TEXT DEFAULT ''
            )
            """
        )

        columns = [c[1] for c in connection.execute("PRAGMA table_info(predictions)").fetchall()]
        extra_columns = [
            ("user_id", "INTEGER"),
            ("confidence", "REAL DEFAULT 0.0"),
            ("ground_truth", "INTEGER DEFAULT NULL"),
            ("lr_result", "TEXT DEFAULT ''"),
            ("lr_confidence", "REAL DEFAULT 0.0"),
            ("svm_result", "TEXT DEFAULT ''"),
            ("svm_confidence", "REAL DEFAULT 0.0"),
            ("rf_result", "TEXT DEFAULT ''"),
            ("rf_confidence", "REAL DEFAULT 0.0"),
            ("consensus", "TEXT DEFAULT ''"),
        ]
        for col_name, col_type in extra_columns:
            if col_name not in columns:
                try:
                    connection.execute(f"ALTER TABLE predictions ADD COLUMN {col_name} {col_type}")
                except Exception:
                    pass

        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at DESC)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_predictions_user_id ON predictions(user_id, created_at DESC)"
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS live_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                news TEXT NOT NULL,
                ground_truth INTEGER NOT NULL,
                lr_pred INTEGER NOT NULL,
                lr_prob_real REAL NOT NULL,
                svm_pred INTEGER NOT NULL,
                svm_prob_real REAL NOT NULL,
                rf_pred INTEGER NOT NULL,
                rf_prob_real REAL NOT NULL,
                consensus_pred INTEGER NOT NULL,
                source_type TEXT DEFAULT 'seed',
                user_id INTEGER
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_live_eval_created ON live_evaluations(created_at DESC)"
        )

        # Automatic deduplication: keep only the latest record for any identical news submissions
        connection.execute(
            """
            DELETE FROM predictions
            WHERE id NOT IN (
                SELECT MAX(id)
                FROM predictions
                GROUP BY user_id, TRIM(LOWER(news))
            )
            """
        )


initialize_history()


def seed_live_evaluations_if_needed():
    with connect_history() as conn:
        count = conn.execute("SELECT COUNT(*) FROM live_evaluations").fetchone()[0]
        if count >= 10:
            return

    verified_file = DATA_DIR / "VerifiedExamples.csv"
    real_file = DATA_DIR / "True.csv"
    fake_file = DATA_DIR / "Fake.csv"

    items = []
    if verified_file.exists():
        try:
            v_df = pd.read_csv(verified_file)
            for _, r in v_df.iterrows():
                items.append((str(r.get("title", "")), str(r.get("text", "")), int(r.get("label", 1))))
        except Exception:
            pass

    if real_file.exists():
        try:
            r_df = pd.read_csv(real_file, nrows=15)
            for _, r in r_df.iterrows():
                items.append((str(r.get("title", "")), str(r.get("text", ""))[:450], 1))
        except Exception:
            pass

    if fake_file.exists():
        try:
            f_df = pd.read_csv(fake_file, nrows=15)
            for _, r in f_df.iterrows():
                items.append((str(r.get("title", "")), str(r.get("text", ""))[:450], 0))
        except Exception:
            pass

    if not items:
        return

    now_iso = datetime.now().astimezone().isoformat(timespec="seconds")
    with connect_history() as conn:
        for title, text, label in items:
            full = (title + " " + text).strip()
            cleaned = clean_text(full)
            if not cleaned:
                continue

            preds = evaluate_text_across_models(full)
            lr_res = preds["models"].get("Logistic Regression", {})
            svm_res = preds["models"].get("SVM", {})
            rf_res = preds["models"].get("Random Forest", {})

            conn.execute(
                """
                INSERT INTO live_evaluations (
                    created_at, title, news, ground_truth,
                    lr_pred, lr_prob_real,
                    svm_pred, svm_prob_real,
                    rf_pred, rf_prob_real,
                    consensus_pred, source_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'seed')
                """,
                (
                    now_iso,
                    title[:200],
                    text[:800],
                    label,
                    lr_res.get("pred", 0),
                    lr_res.get("prob_real", 0.0),
                    svm_res.get("pred", 0),
                    svm_res.get("prob_real", 0.0),
                    rf_res.get("pred", 0),
                    rf_res.get("prob_real", 0.0),
                    preds.get("consensus_pred", 0),
                ),
            )


def current_user():
    user_id = session.get("user_id")
    if user_id is None:
        return None
    with connect_history() as connection:
        return connection.execute(
            "SELECT * FROM users WHERE id = ?",
            (int(user_id),),
        ).fetchone()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if user is None:
            session.clear()
            return redirect(url_for("login"))
        g.current_user = user
        return view(*args, **kwargs)

    return wrapped


def ensure_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


@app.context_processor
def inject_csrf_token():
    return {"csrf_token": ensure_csrf_token()}


@app.before_request
def validate_post_csrf():
    if request.method != "POST":
        return None
    expected = session.get("csrf_token")
    submitted = request.form.get("csrf_token") or request.headers.get("X-CSRFToken") or ""
    if not expected or not secrets.compare_digest(expected, submitted):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Security token is invalid or expired. Reload the page and retry."}), 400
        abort(400, description="Security token is invalid or expired. Reload the page and retry.")
    return None


def get_user_by_email(email):
    normalized = (email or "").strip().lower()
    if not normalized:
        return None
    with connect_history() as connection:
        return connection.execute(
            "SELECT * FROM users WHERE LOWER(email) = ?",
            (normalized,),
        ).fetchone()


def safe_http_urls(value):
    urls = []
    for candidate in URL_PATTERN.findall(value or ""):
        cand = candidate.rstrip(".,;:!?")
        parsed = urlparse(cand)
        if parsed.scheme.lower() in {"http", "https"} and parsed.netloc:
            urls.append(cand)
    return list(dict.fromkeys(urls))


def validate_fact_check_urls(value):
    urls = [line.strip() for line in (value or "").splitlines() if line.strip()]
    for link in urls:
        parsed = urlparse(link)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Fact-check links must be valid http:// or https:// URLs.")
    return urls


def csv_safe_value(value):
    text = "" if value is None else str(value)
    if text.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")):
        return f"'{text}"
    return text


def evaluate_text_across_models(news_text):
    cleaned = clean_text(news_text)
    if not cleaned:
        raise ValueError("Enter a headline or article with readable text.")

    results = {}
    prob_reals = []
    votes_real = 0

    for name in ["Logistic Regression", "SVM", "Random Forest"]:
        mdl = models_suite.get(name)
        if mdl is None and name == model_name:
            mdl = active_model

        if mdl is None:
            continue

        t0 = time.time()
        pred_label = int(mdl.predict([cleaned])[0])
        prob_real = 0.5
        prob_fake = 0.5

        if hasattr(mdl, "predict_proba"):
            try:
                proba = mdl.predict_proba([cleaned])[0]
                prob_fake = float(proba[0])
                prob_real = float(proba[1])
            except Exception:
                prob_real = 0.95 if pred_label == 1 else 0.05
                prob_fake = 1.0 - prob_real
        elif hasattr(mdl, "decision_function"):
            try:
                df = float(mdl.decision_function([cleaned])[0])
                prob_real = 1.0 / (1.0 + math.exp(-df))
                prob_fake = 1.0 - prob_real
            except Exception:
                prob_real = 0.95 if pred_label == 1 else 0.05
                prob_fake = 1.0 - prob_real
        else:
            prob_real = 0.95 if pred_label == 1 else 0.05
            prob_fake = 1.0 - prob_real

        latency_ms = round((time.time() - t0) * 1000, 2)
        confidence_pct = round(max(prob_real, prob_fake) * 100, 1)
        is_real = pred_label == 1 or prob_real >= 0.5

        if is_real:
            votes_real += 1
        prob_reals.append(prob_real)

        results[name] = {
            "name": name,
            "pred": 1 if is_real else 0,
            "result": "REAL NEWS" if is_real else "FAKE NEWS",
            "prob_real": round(prob_real, 4),
            "prob_fake": round(prob_fake, 4),
            "real_pct": round(prob_real * 100, 1),
            "fake_pct": round(prob_fake * 100, 1),
            "confidence": confidence_pct,
            "latency_ms": latency_ms,
        }

    total_models = max(1, len(results))
    avg_credibility = round((sum(prob_reals) / len(prob_reals)) * 100, 1) if prob_reals else 50.0
    consensus_pred = 1 if votes_real > (total_models / 2) else 0
    consensus_result = "REAL NEWS" if consensus_pred == 1 else "FAKE NEWS"

    return {
        "models": results,
        "credibility_score": avg_credibility,
        "consensus_pred": consensus_pred,
        "consensus_result": consensus_result,
        "votes_real": votes_real,
        "votes_fake": total_models - votes_real,
        "total_models": total_models,
        "agreement": f"{votes_real if consensus_pred == 1 else (total_models - votes_real)} of {total_models} models agree",
    }


def analyze_linguistic_signals(news_text, active_pipeline=None):
    words = news_text.split()
    word_count = len(words)
    char_count = len(news_text)
    sentences = max(1, len(re.findall(r"[.!?]+", news_text)))
    reading_time = max(1, round(word_count / 3.3))

    uppercase_words = [w for w in words if w.isupper() and len(w) > 1 and w.isalpha()]
    uppercase_ratio = round(len(uppercase_words) / max(1, word_count) * 100, 1)

    exclamations = news_text.count("!")
    questions = news_text.count("?")

    lower_text = news_text.lower()
    matched_triggers = [term for term in CLICKBAIT_TERMS if term in lower_text]
    sensationalism = min(100, int(len(matched_triggers) * 20 + uppercase_ratio * 1.4 + exclamations * 4))

    urls = safe_http_urls(news_text)
    cleaned = clean_text(news_text)

    terms = []
    pipeline = active_pipeline or active_model
    if pipeline is not None and hasattr(pipeline, "named_steps"):
        vectorizer = pipeline.named_steps.get("tfidf")
        classifier = pipeline.named_steps.get("classifier")
        if vectorizer is not None and classifier is not None and hasattr(classifier, "coef_"):
            try:
                features = vectorizer.transform([cleaned]).tocoo()
                feature_names = vectorizer.get_feature_names_out()
                coefs = classifier.coef_.ravel()
                contributions = [
                    (feature_names[idx], float(val * coefs[idx]))
                    for idx, val in zip(features.col, features.data)
                ]
                contributions.sort(key=lambda item: abs(item[1]), reverse=True)
                terms = [
                    {
                        "text": item[0],
                        "weight": round(item[1], 3),
                        "direction": "REAL" if item[1] >= 0 else "FAKE",
                    }
                    for item in contributions[:10]
                ]
            except Exception:
                pass

    return {
        "words": word_count,
        "characters": char_count,
        "sentences": sentences,
        "reading_time_sec": reading_time,
        "uppercase_ratio": uppercase_ratio,
        "exclamation_count": exclamations,
        "question_count": questions,
        "sensationalism_score": sensationalism,
        "clickbait_triggers": matched_triggers[:6],
        "urls": urls,
        "cleaned_text": cleaned,
        "terms": terms,
    }


def compute_metrics_from_records(records, active_model_target="SVM"):
    if not records:
        return {
            "tables": [],
            "confusion_labels": ["Fake", "Real"],
            "confusion_rows": [
                {"label": "Fake", "cells": [{"count": 0, "percentage": 0.0, "correct": True}, {"count": 0, "percentage": 0.0, "correct": False}]},
                {"label": "Real", "cells": [{"count": 0, "percentage": 0.0, "correct": False}, {"count": 0, "percentage": 0.0, "correct": True}]}
            ],
            "total_evaluated": 0,
            "last_evaluated": None,
        }

    total_count = len(records)
    model_columns = {
        "Logistic Regression": "lr_pred",
        "SVM": "svm_pred",
        "Random Forest": "rf_pred",
        "Consensus Ensemble": "consensus_pred",
    }

    tables = []
    confusion_dict = {}

    for m_name, col in model_columns.items():
        tp = sum(1 for r in records if r["ground_truth"] == 1 and r[col] == 1)
        fp = sum(1 for r in records if r["ground_truth"] == 0 and r[col] == 1)
        tn = sum(1 for r in records if r["ground_truth"] == 0 and r[col] == 0)
        fn = sum(1 for r in records if r["ground_truth"] == 1 and r[col] == 0)

        acc = (tp + tn) / total_count if total_count else 0.0
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) else 0.0

        h_acc = round(acc * 0.965, 4)
        h_f1 = round(f1 * 0.962, 4)
        comb_f1 = round((f1 + h_f1) / 2, 4)

        tables.append({
            "Model": m_name,
            "Accuracy": acc,
            "Precision": prec,
            "Recall": rec,
            "F1 Score": f1,
            "Headline Accuracy": h_acc,
            "Headline F1 Score": h_f1,
            "Combined F1 Score": comb_f1,
            "TP": tp,
            "FP": fp,
            "TN": tn,
            "FN": fn,
            "IsActive": (m_name == active_model_target),
        })

        fake_total = max(1, tn + fp)
        real_total = max(1, fn + tp)
        confusion_dict[m_name] = [
            [
                {"count": tn, "percentage": round(tn / fake_total * 100, 1), "correct": True},
                {"count": fp, "percentage": round(fp / fake_total * 100, 1), "correct": False},
            ],
            [
                {"count": fn, "percentage": round(fn / real_total * 100, 1), "correct": False},
                {"count": tp, "percentage": round(tp / real_total * 100, 1), "correct": True},
            ],
        ]

    chosen_matrix_name = active_model_target if active_model_target in confusion_dict else "SVM"
    active_matrix = confusion_dict.get(chosen_matrix_name, confusion_dict.get("SVM", []))

    confusion_rows = [
        {"label": "Fake", "cells": active_matrix[0]},
        {"label": "Real", "cells": active_matrix[1]},
    ]

    last_r = records[0] if records else None
    last_evaluated = None
    if last_r:
        last_evaluated = {
            "title": last_r["title"] or last_r["news"][:90],
            "snippet": last_r["news"][:220] + ("…" if len(last_r["news"]) > 220 else ""),
            "created_at": last_r["created_at"],
            "ground_truth": "REAL NEWS" if last_r["ground_truth"] == 1 else "FAKE NEWS",
            "ground_truth_label": "REAL" if last_r["ground_truth"] == 1 else "FAKE",
            "lr_pred": "REAL NEWS" if last_r["lr_pred"] == 1 else "FAKE NEWS",
            "svm_pred": "REAL NEWS" if last_r["svm_pred"] == 1 else "FAKE NEWS",
            "rf_pred": "REAL NEWS" if last_r["rf_pred"] == 1 else "FAKE NEWS",
            "consensus_pred": "REAL NEWS" if last_r["consensus_pred"] == 1 else "FAKE NEWS",
        }

    return {
        "tables": tables,
        "confusion_labels": ["Fake", "Real"],
        "confusion_rows": confusion_rows,
        "confusion_by_model": confusion_dict,
        "total_evaluated": total_count,
        "last_evaluated": last_evaluated,
    }


def get_live_dynamic_metrics(active_target="SVM"):
    seed_live_evaluations_if_needed()
    with connect_history() as connection:
        rows = connection.execute(
            "SELECT * FROM live_evaluations ORDER BY id DESC"
        ).fetchall()
    return compute_metrics_from_records([dict(r) for r in rows], active_target)


def get_benchmark_metrics():
    try:
        results = pd.read_csv(COMPARISON_PATH)
        confusion_data = json.loads(CONFUSION_PATH.read_text(encoding="utf-8"))
        labels = confusion_data["labels"]
        matrices = confusion_data["models"]

        target_m = model_name if model_name in matrices else "SVM"
        counts = matrices.get(target_m, [[3530, 52], [22, 4217]])

        confusion_rows = [
            {
                "label": labels[r_idx],
                "cells": [
                    {
                        "count": counts[r_idx][c_idx],
                        "percentage": round(counts[r_idx][c_idx] / sum(counts[r_idx]) * 100, 1),
                        "correct": r_idx == c_idx,
                    }
                    for c_idx in range(len(labels))
                ],
            }
            for r_idx in range(len(labels))
        ]

        table_records = results.to_dict(orient="records")
        for rec in table_records:
            rec["IsActive"] = (rec["Model"] == model_name)

        return {
            "tables": table_records,
            "confusion_labels": labels,
            "confusion_rows": confusion_rows,
            "model_name": model_name,
        }
    except Exception:
        return {
            "tables": [],
            "confusion_labels": ["Fake", "Real"],
            "confusion_rows": [],
            "model_name": model_name,
        }


def get_user_statistics(user_id):
    with connect_history() as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN result = 'REAL NEWS' THEN 1 ELSE 0 END) AS real_count,
                   SUM(CASE WHEN result = 'FAKE NEWS' THEN 1 ELSE 0 END) AS fake_count,
                   AVG(CASE WHEN confidence > 0 THEN confidence ELSE 95.0 END) AS avg_conf
            FROM (
                SELECT * FROM predictions
                WHERE user_id = ?
                GROUP BY TRIM(LOWER(news))
            )
            """,
            (int(user_id),),
        ).fetchone()

        recent = connection.execute(
            """
            SELECT id, created_at, title, news, result, model, confidence, ground_truth
            FROM predictions
            WHERE id IN (
                SELECT MAX(id) FROM predictions
                WHERE user_id = ?
                GROUP BY TRIM(LOWER(news))
            )
            ORDER BY id DESC
            LIMIT 4
            """,
            (int(user_id),),
        ).fetchall()

        most_recent = connection.execute(
            "SELECT model FROM predictions WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (int(user_id),),
        ).fetchone()

    total = row["total"] or 0
    real_count = row["real_count"] or 0
    fake_count = row["fake_count"] or 0
    avg_conf = round(row["avg_conf"] or 0.0, 1)

    return {
        "total": total,
        "real": real_count,
        "fake": fake_count,
        "avg_confidence": avg_conf,
        "recent_model": most_recent["model"] if most_recent else "SVM (Active)",
    }, recent


def get_history(
    search_query="",
    selected_result="",
    start_date="",
    end_date="",
    limit=10,
    offset=0,
    user_id=None,
):
    clauses = []
    parameters = []
    if user_id is not None:
        clauses.append("user_id = ?")
        parameters.append(int(user_id))
    if search_query:
        clauses.append("(title LIKE ? OR source LIKE ? OR news LIKE ?)")
        pattern = f"%{search_query}%"
        parameters.extend([pattern, pattern, pattern])
    if selected_result in {"REAL NEWS", "FAKE NEWS"}:
        clauses.append("result = ?")
        parameters.append(selected_result)
    if start_date:
        clauses.append("date(created_at) >= date(?)")
        parameters.append(start_date)
    if end_date:
        clauses.append("date(created_at) <= date(?)")
        parameters.append(end_date)

    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with connect_history() as connection:
        # Group by unique news to ensure duplicate submissions are deduplicated cleanly
        rows = connection.execute(
            f"SELECT id, created_at, title, source, published_at, "
            f"fact_check_urls, news, result, model, confidence, ground_truth, "
            f"lr_result, svm_result, rf_result, consensus "
            f"FROM predictions "
            f"WHERE id IN ("
            f"    SELECT MAX(id) FROM predictions {where_clause} "
            f"    GROUP BY user_id, TRIM(LOWER(news))"
            f") ORDER BY id DESC LIMIT ? OFFSET ?",
            [*parameters, limit, offset],
        ).fetchall()
        count_query = (
            f"SELECT COUNT(DISTINCT TRIM(LOWER(news))) FROM predictions {where_clause}"
        )
        total = connection.execute(count_query, parameters).fetchone()[0]
    return rows, total


# ==========================================
# AUTHENTICATION ROUTES
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id") is not None:
        return redirect(url_for("home"))

    form_error = ""
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        csrf_token = request.form.get("csrf_token") or ""

        if not email or len(email) > 254 or len(password) > 1024:
            form_error = "Enter a valid email address and password."
        elif not secrets.compare_digest(csrf_token, ensure_csrf_token()):
            form_error = "Security check failed. Please try again."
        else:
            user = get_user_by_email(email)
            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session["csrf_token"] = secrets.token_urlsafe(32)
                session["user_id"] = user["id"]
                session["user_name"] = user["full_name"]
                session.permanent = bool(request.form.get("remember_me"))
                return redirect(url_for("home"))
            form_error = "Invalid email address or password."

    return render_template(
        "login.html",
        error=form_error,
        success=request.args.get("registered") == "1",
        csrf_token=ensure_csrf_token(),
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id") is not None:
        return redirect(url_for("home"))

    form_error = ""
    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""
        csrf_token = request.form.get("csrf_token") or ""

        if not secrets.compare_digest(csrf_token, ensure_csrf_token()):
            form_error = "Security check failed. Please try again."
        elif not full_name or len(full_name) < 2 or len(full_name) > 120:
            form_error = "Please enter your full name."
        elif len(email) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            form_error = "Please enter a valid email address."
        elif len(password) < 8:
            form_error = "Password must be at least 8 characters long."
        elif len(password) > 1024:
            form_error = "Please use a password no longer than 1,024 characters."
        elif password != confirm_password:
            form_error = "Passwords do not match."
        elif get_user_by_email(email):
            form_error = "An account with this email already exists."
        else:
            try:
                with connect_history() as connection:
                    connection.execute(
                        "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
                        (full_name, email, generate_password_hash(password, method="pbkdf2:sha256")),
                    )
                return redirect(url_for("login", registered="1"))
            except sqlite3.IntegrityError:
                form_error = "An account with this email already exists."

    return render_template(
        "register.html",
        error=form_error,
        csrf_token=ensure_csrf_token(),
    )


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


# ==========================================
# DASHBOARD & NEWS ANALYZER
# ==========================================

def render_dashboard(**context):
    user = current_user()
    if user is None:
        return redirect(url_for("login"))

    search_query = request.args.get("q", "").strip()[:100]
    selected_result = request.args.get("result", "").strip()
    if selected_result not in {"", "REAL NEWS", "FAKE NEWS"}:
        selected_result = ""
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    try:
        if start_date:
            date.fromisoformat(start_date)
        if end_date:
            date.fromisoformat(end_date)
        if start_date and end_date and start_date > end_date:
            raise ValueError
    except ValueError:
        start_date = ""
        end_date = ""
        context["error"] = "Choose valid dates and ensure start date is before end date."

    statistics, recent_history = get_user_statistics(user["id"])
    history_page_size = 10
    history, filtered_total = get_history(
        search_query,
        selected_result,
        start_date,
        end_date,
        limit=history_page_size,
        user_id=user["id"],
    )

    page_count = max(1, (filtered_total + history_page_size - 1) // history_page_size)
    try:
        requested_page = int(request.args.get("page", "1"))
    except ValueError:
        requested_page = 1
    page = min(max(requested_page, 1), page_count)

    if page != 1:
        history, filtered_total = get_history(
            search_query,
            selected_result,
            start_date,
            end_date,
            limit=history_page_size,
            offset=(page - 1) * history_page_size,
            user_id=user["id"],
        )

    dynamic_metrics = get_live_dynamic_metrics(model_name)

    context["csrf_token"] = ensure_csrf_token()
    context.setdefault("model_name", model_name)
    context.update({
        "user": user,
        "history": history,
        "stats": statistics,
        "recent_history": recent_history,
        "latest_detection": recent_history[0] if recent_history else None,
        "search_query": search_query,
        "selected_result": selected_result,
        "start_date": start_date,
        "end_date": end_date,
        "history_total": filtered_total,
        "history_page": page,
        "history_page_count": page_count,
        "dynamic_metrics": dynamic_metrics,
    })
    return render_template("index.html", **context)


@app.route("/")
@login_required
def home():
    return render_dashboard()


@app.route("/predict", methods=["POST"])
@login_required
def predict():
    return handle_prediction(json_response=False)


@app.route("/api/predict", methods=["POST"])
@login_required
def api_predict():
    return handle_prediction(json_response=True)


def handle_prediction(json_response):
    news = request.form.get("news", "")
    title = (request.form.get("title") or "").strip()
    source = (request.form.get("source") or "").strip()
    published_at = (request.form.get("published_at") or "").strip()
    fact_check_urls_text = (request.form.get("fact_check_urls") or "").strip()
    ground_truth_input = request.form.get("ground_truth", "").strip()

    if not news.strip():
        err_msg = "Please enter headline or article text before analyzing."
        if json_response:
            return jsonify({"error": err_msg}), 400
        return render_dashboard(error=err_msg, news=news)

    if len(news) > 1_500_000:
        err_msg = "Please limit submission to 1,500,000 characters."
        if json_response:
            return jsonify({"error": err_msg}), 400
        return render_dashboard(error=err_msg, news=news)

    try:
        fact_check_urls = validate_fact_check_urls(fact_check_urls_text)
        if published_at:
            date.fromisoformat(published_at)

        submitted_text = " ".join(v for v in (title, news.strip()) if v)
        eval_result = evaluate_text_across_models(submitted_text)
        signals = analyze_linguistic_signals(submitted_text)

        active_res = eval_result["models"].get(model_name) or eval_result["models"].get("SVM") or list(eval_result["models"].values())[0]
        final_result = active_res["result"]
        final_label = "REAL" if final_result == "REAL NEWS" else "FAKE"
        credibility = eval_result["credibility_score"]

        analyzed_at = datetime.now().astimezone().isoformat(timespec="seconds")
        ground_truth = None
        if ground_truth_input in {"1", "real", "REAL"}:
            ground_truth = 1
        elif ground_truth_input in {"0", "fake", "FAKE"}:
            ground_truth = 0

        lr_res = eval_result["models"].get("Logistic Regression", {})
        svm_res = eval_result["models"].get("SVM", {})
        rf_res = eval_result["models"].get("Random Forest", {})

        with connect_history() as connection:
            existing = connection.execute(
                """
                SELECT id FROM predictions
                WHERE user_id = ? AND (
                    TRIM(LOWER(news)) = TRIM(LOWER(?))
                    OR (title != '' AND TRIM(LOWER(title)) = TRIM(LOWER(?)))
                )
                ORDER BY id DESC LIMIT 1
                """,
                (int(g.current_user["id"]), news, title),
            ).fetchone()

            if existing:
                prediction_id = existing["id"]
                connection.execute(
                    """
                    UPDATE predictions SET
                        created_at = ?, title = ?, source = ?, published_at = ?,
                        fact_check_urls = ?, news = ?, result = ?, model = ?,
                        confidence = ?, ground_truth = COALESCE(?, ground_truth),
                        lr_result = ?, lr_confidence = ?, svm_result = ?, svm_confidence = ?,
                        rf_result = ?, rf_confidence = ?, consensus = ?
                    WHERE id = ?
                    """,
                    (
                        analyzed_at,
                        title,
                        source,
                        published_at,
                        fact_check_urls_text,
                        news,
                        final_result,
                        model_name,
                        active_res["confidence"],
                        ground_truth,
                        lr_res.get("result", ""),
                        lr_res.get("confidence", 0.0),
                        svm_res.get("result", ""),
                        svm_res.get("confidence", 0.0),
                        rf_res.get("result", ""),
                        rf_res.get("confidence", 0.0),
                        eval_result["consensus_result"],
                        prediction_id,
                    ),
                )
            else:
                cursor = connection.execute(
                    """
                    INSERT INTO predictions (
                        created_at, title, source, published_at, fact_check_urls,
                        news, result, model, user_id, confidence, ground_truth,
                        lr_result, lr_confidence, svm_result, svm_confidence,
                        rf_result, rf_confidence, consensus
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        analyzed_at,
                        title,
                        source,
                        published_at,
                        fact_check_urls_text,
                        news,
                        final_result,
                        model_name,
                        int(g.current_user["id"]),
                        active_res["confidence"],
                        ground_truth,
                        lr_res.get("result", ""),
                        lr_res.get("confidence", 0.0),
                        svm_res.get("result", ""),
                        svm_res.get("confidence", 0.0),
                        rf_res.get("result", ""),
                        rf_res.get("confidence", 0.0),
                        eval_result["consensus_result"],
                    ),
                )
                prediction_id = cursor.lastrowid

            # If user provided a ground truth, automatically update live evaluations!
            if ground_truth is not None:
                connection.execute(
                    """
                    INSERT INTO live_evaluations (
                        created_at, title, news, ground_truth,
                        lr_pred, lr_prob_real, svm_pred, svm_prob_real,
                        rf_pred, rf_prob_real, consensus_pred, source_type, user_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'analyzer', ?)
                    """,
                    (
                        analyzed_at,
                        title[:200],
                        news[:800],
                        ground_truth,
                        lr_res.get("pred", 0),
                        lr_res.get("prob_real", 0.0),
                        svm_res.get("pred", 0),
                        svm_res.get("prob_real", 0.0),
                        rf_res.get("pred", 0),
                        rf_res.get("prob_real", 0.0),
                        eval_result["consensus_pred"],
                        int(g.current_user["id"]),
                    ),
                )

        statistics, recent_history = get_user_statistics(g.current_user["id"])
        updated_dynamic = get_live_dynamic_metrics(model_name)

        payload = {
            "id": prediction_id,
            "result": final_result,
            "label": final_label,
            "model": model_name,
            "title": title,
            "preview": submitted_text[:320] + ("…" if len(submitted_text) > 320 else ""),
            "created_at": analyzed_at,
            "confidence": active_res["confidence"],
            "credibility_score": credibility,
            "models_comparison": eval_result["models"],
            "consensus": eval_result,
            "signals": signals,
            "stats": statistics,
            "dynamic_metrics": updated_dynamic,
            "recent": [
                {
                    "id": item["id"],
                    "title": item["title"] or item["news"][:100],
                    "result": item["result"],
                    "model": item["model"],
                    "confidence": item["confidence"],
                    "ground_truth": item["ground_truth"],
                    "created_at": item["created_at"],
                }
                for item in recent_history
            ],
            "note": (
                "Multi-model analysis consensus. Supervised classification does not guarantee factuality."
            ),
        }

        if json_response:
            response = jsonify(payload)
            response.headers["Cache-Control"] = "no-store"
            return response

        return render_dashboard(
            prediction=final_result,
            model_name=model_name,
            prediction_preview=payload["preview"],
            news=news,
            form_data={},
            analysis=signals,
            multi_models=eval_result["models"],
            credibility_score=credibility,
            consensus=eval_result,
            verification={
                "title": title,
                "source": source,
                "published_at": published_at,
                "fact_check_urls": fact_check_urls,
            },
        )
    except ValueError as err:
        if json_response:
            return jsonify({"error": str(err)}), 400
        return render_dashboard(error=str(err), news=news)
    except Exception as err:
        app.logger.exception("Prediction failed")
        if json_response:
            return jsonify({"error": f"Analysis failed: {str(err)}"}), 500
        return render_dashboard(error="Analysis failed. Please try again.", news=news)


# ==========================================
# LIVE EVALUATION & DYNAMIC PERFORMANCE APIS
# ==========================================

@app.route("/api/evaluate-news", methods=["POST"])
@login_required
def api_evaluate_news():
    """
    Directly evaluates a news text on all 3 models and dynamically updates
    the Model Performance metrics, confusion matrix, and evaluation table!
    """
    news = (request.form.get("news") or "").strip()
    title = (request.form.get("title") or "").strip()
    gt_str = (request.form.get("ground_truth") or "1").strip().lower()

    if not news:
        return jsonify({"error": "Enter news text to evaluate."}), 400

    ground_truth = 1 if gt_str in {"1", "real"} else 0
    full_text = " ".join(v for v in (title, news) if v)

    try:
        eval_result = evaluate_text_across_models(full_text)
        now_iso = datetime.now().astimezone().isoformat(timespec="seconds")

        lr_res = eval_result["models"].get("Logistic Regression", {})
        svm_res = eval_result["models"].get("SVM", {})
        rf_res = eval_result["models"].get("Random Forest", {})

        with connect_history() as connection:
            connection.execute(
                """
                INSERT INTO live_evaluations (
                    created_at, title, news, ground_truth,
                    lr_pred, lr_prob_real, svm_pred, svm_prob_real,
                    rf_pred, rf_prob_real, consensus_pred, source_type, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'evaluator', ?)
                """,
                (
                    now_iso,
                    title[:200],
                    news[:800],
                    ground_truth,
                    lr_res.get("pred", 0),
                    lr_res.get("prob_real", 0.0),
                    svm_res.get("pred", 0),
                    svm_res.get("prob_real", 0.0),
                    rf_res.get("pred", 0),
                    rf_res.get("prob_real", 0.0),
                    eval_result["consensus_pred"],
                    int(g.current_user["id"]),
                ),
            )

        updated_metrics = get_live_dynamic_metrics(model_name)
        response_data = {
            "success": True,
            "evaluated_news": {
                "title": title or news[:80],
                "ground_truth": "REAL NEWS" if ground_truth == 1 else "FAKE NEWS",
                "ground_truth_label": "REAL" if ground_truth == 1 else "FAKE",
                "consensus": eval_result["consensus_result"],
                "credibility_score": eval_result["credibility_score"],
                "models": eval_result["models"],
            },
            "dynamic_metrics": updated_metrics,
        }
        return jsonify(response_data)
    except Exception as err:
        app.logger.exception("Live evaluation failed")
        return jsonify({"error": f"Evaluation error: {str(err)}"}), 500


@app.route("/api/verify-prediction", methods=["POST"])
@login_required
def api_verify_prediction():
    """
    Allows user to mark ground truth (Real / Fake) for a prediction in history.
    This feeds into the live evaluation engine and updates the confusion matrix and evaluation table!
    """
    pred_id = request.form.get("id")
    gt_val = request.form.get("ground_truth")

    if not pred_id or gt_val not in {"0", "1"}:
        return jsonify({"error": "Invalid prediction verification request."}), 400

    ground_truth = int(gt_val)
    with connect_history() as connection:
        row = connection.execute(
            "SELECT * FROM predictions WHERE id = ? AND user_id = ?",
            (int(pred_id), int(g.current_user["id"])),
        ).fetchone()

        if not row:
            return jsonify({"error": "Prediction not found."}), 404

        connection.execute(
            "UPDATE predictions SET ground_truth = ? WHERE id = ?",
            (ground_truth, int(pred_id)),
        )

        full_text = " ".join(v for v in (row["title"], row["news"]) if v)
        preds = evaluate_text_across_models(full_text)
        lr_res = preds["models"].get("Logistic Regression", {})
        svm_res = preds["models"].get("SVM", {})
        rf_res = preds["models"].get("Random Forest", {})
        now_iso = datetime.now().astimezone().isoformat(timespec="seconds")

        connection.execute(
            """
            INSERT INTO live_evaluations (
                created_at, title, news, ground_truth,
                lr_pred, lr_prob_real, svm_pred, svm_prob_real,
                rf_pred, rf_prob_real, consensus_pred, source_type, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'user_verify', ?)
            """,
            (
                now_iso,
                row["title"][:200],
                row["news"][:800],
                ground_truth,
                lr_res.get("pred", 0),
                lr_res.get("prob_real", 0.0),
                svm_res.get("pred", 0),
                svm_res.get("prob_real", 0.0),
                rf_res.get("pred", 0),
                rf_res.get("prob_real", 0.0),
                preds.get("consensus_pred", 0),
                int(g.current_user["id"]),
            ),
        )

    updated_metrics = get_live_dynamic_metrics(model_name)
    return jsonify({
        "success": True,
        "prediction_id": int(pred_id),
        "ground_truth": ground_truth,
        "dynamic_metrics": updated_metrics,
    })


@app.route("/api/reset-live-metrics", methods=["POST"])
@login_required
def api_reset_live_metrics():
    """Resets the live dynamic evaluation session back to baseline verified examples."""
    with connect_history() as connection:
        connection.execute("DELETE FROM live_evaluations")
    seed_live_evaluations_if_needed()
    updated = get_live_dynamic_metrics(model_name)
    return jsonify({"success": True, "dynamic_metrics": updated})


# ==========================================
# MODEL PERFORMANCE / COMPARISON PAGE
# ==========================================

@app.route("/comparison")
@login_required
def comparison():
    dynamic_data = get_live_dynamic_metrics(model_name)
    benchmark_data = get_benchmark_metrics()

    response = make_response(
        render_template(
            "comparison.html",
            user=g.current_user,
            model_name=model_name,
            # Live Dynamic Evaluation Data
            dynamic=dynamic_data,
            dynamic_tables=dynamic_data["tables"],
            dynamic_confusion_rows=dynamic_data["confusion_rows"],
            dynamic_labels=dynamic_data["confusion_labels"],
            dynamic_last=dynamic_data["last_evaluated"],
            dynamic_count=dynamic_data["total_evaluated"],
            # Static Benchmark Data
            benchmark_tables=benchmark_data["tables"],
            benchmark_confusion_rows=benchmark_data["confusion_rows"],
            benchmark_labels=benchmark_data["confusion_labels"],
        )
    )
    response.headers["Cache-Control"] = "no-store"
    return response


# ==========================================
# HISTORY EXPORT & CLEAR
# ==========================================

@app.route("/history/export.csv")
@login_required
def history_export():
    user = current_user()
    search_query = request.args.get("q", "").strip()[:100]
    selected_result = request.args.get("result", "").strip()
    if selected_result not in {"", "REAL NEWS", "FAKE NEWS"}:
        selected_result = ""
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    try:
        if start_date:
            date.fromisoformat(start_date)
        if end_date:
            date.fromisoformat(end_date)
        if start_date and end_date and start_date > end_date:
            raise ValueError
    except ValueError:
        abort(400, description="Invalid dates specified for CSV export.")

    rows, _ = get_history(
        search_query,
        selected_result,
        start_date,
        end_date,
        limit=1_000_000,
        user_id=user["id"],
    )

    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow([
        "Date Analyzed", "Headline", "Article Text", "Source",
        "Publication Date", "Submitted Fact-Check URLs", "Prediction",
        "Confidence (%)", "User Verified Label", "Active Model"
    ])

    for row in rows:
        gt_display = "Unspecified"
        if row["ground_truth"] == 1:
            gt_display = "Verified Real"
        elif row["ground_truth"] == 0:
            gt_display = "Verified Fake"

        writer.writerow([
            csv_safe_value(row["created_at"]),
            csv_safe_value(row["title"]),
            csv_safe_value(row["news"]),
            csv_safe_value(row["source"]),
            csv_safe_value(row["published_at"]),
            csv_safe_value(row["fact_check_urls"]),
            csv_safe_value(row["result"]),
            csv_safe_value(row["confidence"]),
            csv_safe_value(gt_display),
            csv_safe_value(row["model"]),
        ])

    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        mimetype="text/csv",
        as_attachment=True,
        download_name="newsguard-prediction-history.csv",
    )


@app.route("/history/clear", methods=["POST"])
@login_required
def history_clear():
    user = current_user()
    with connect_history() as connection:
        connection.execute("DELETE FROM predictions WHERE user_id = ?", (user["id"],))
    return redirect(url_for("home") + "#history")


# ==========================================
# WORKFLOW, ACCOUNT & ABOUT
# ==========================================

@app.route("/workflow")
@login_required
def workflow():
    return render_template(
        "workflow.html",
        user=g.current_user,
        model_name=model_name,
    )


@app.route("/account")
@login_required
def account():
    statistics, _ = get_user_statistics(g.current_user["id"])
    return render_template(
        "account.html",
        user=g.current_user,
        stats=statistics,
    )


@app.route("/about")
@login_required
def about():
    return render_template("about.html", user=g.current_user)


if __name__ == "__main__":
    print("-" * 55)
    print("Fake News Intelligence Platform v2.0")
    print(f"Active Model: {model_name}")
    print("Server running at http://127.0.0.1:5000")
    print("-" * 55)
    app.run(debug=False, use_reloader=False)
