# NewsGuard AI — Advanced Fake News Intelligence Platform

NewsGuard AI is an advanced, production-grade Natural Language Processing (NLP) intelligence platform that classifies news articles and viral claims as **REAL NEWS** or **FAKE NEWS** using a multi-model ensemble pipeline (**Linear Support Vector Machine**, **Logistic Regression**, and **Random Forest**).

It features a modern cyber-glassmorphic UI, real-time Credibility Speedometer scoring, deep linguistic/disinformation signal analysis, an interactive **Live News Evaluator**, and a **Dynamic Performance Engine** that continuously updates confusion matrices and evaluation metrics as news is analyzed and verified.

> **Disclaimer:** Statistical machine-learning text classification indicates linguistic probability and style patterns. It is not an automated fact-checking authority. Always cross-verify critical claims with independent primary sources.

---

## Key Features

1. **Multi-Model Concurrent Classification:**
   - Evaluates text across **Linear SVM**, **Logistic Regression**, and **Random Forest** simultaneously.
   - Computes weighted ensemble consensus, individual probability bars, and sub-40ms latency metrics.

2. **Continuous Dynamic Performance & Live Confusion Matrix:**
   - **Live Dynamic Evaluation:** The confusion matrix (True Positives, False Positives, True Negatives, False Negatives) and the detailed evaluation table (Accuracy, Precision, Recall, F1 Score) dynamically update when articles are tested or verified.
   - **Interactive Live News Evaluator:** Dedicated test bench on the Model Performance page allowing one-click evaluation of any news with chosen ground truth, updating charts and tables in real time without reloading.
   - **Dual-Mode View:** Seamlessly toggle between **Live Evaluated News** and the **Held-Out Benchmark Split (44,898+ articles)**.

3. **Credibility Speedometer & Linguistic Signal Inspector:**
   - Radial SVG gauge visualizing the calibrated Credibility Index (0–100%).
   - Sensationalism & Clickbait Index with trigger term detection.
   - Capitalization (SHOUTING) ratio and emotional punctuation intensity (! and ?).
   - Top predictive feature vocabulary chips showing positive (Real) and negative (Fake) mathematical weights.

4. **User Verification & Ground Truth Calibration:**
   - One-click ground-truth verification on predictions (`✓ Confirm Real` / `! Mark Fake`) directly feeding into the live evaluation engine.

5. **Security, Privacy & Data Management:**
   - Secure authentication with Werkzeug PBKDF2 SHA-256 password hashing.
   - SQLite concurrency with user-isolated prediction history and ground truth tracking.
   - Filterable prediction history with instant search, date ranges, and formatted CSV export.

---

## Quickstart Guide

### 1. Open Terminal in the Project Directory

```powershell
cd "C:\Users\nehas\OneDrive\Desktop\Fake-News-Detection"
```

### 2. Activate Virtual Environment (if configured) or run with Python 3.13

```powershell
python -m pip install -r requirements.txt
```

### 3. Start the Application

```powershell
python app.py
```

The terminal will cleanly display:
```
-------------------------------------------------------
Fake News Intelligence Platform v2.0
Active Model: SVM
Server running at http://127.0.0.1:5000
-------------------------------------------------------
```

### 4. Open in Browser

Navigate to:
- **`http://127.0.0.1:5000/login`**
- Register an account or sign in to enter the AI Intelligence Workspace.

---

## Application Routes

- **`/`** — Intelligence Workspace: News Analyzer, Credibility Speedometer, Multi-Model Consensus, Linguistic Signals, and Filterable Prediction History.
- **`/comparison`** — Multi-Model Performance Dashboard: Interactive Live News Evaluator, Dynamic Confusion Matrix, Dynamic Evaluation Table, and Held-Out Benchmark comparisons.
- **`/api/predict`** — Concurrent multi-model inference API returning predictions, probabilities, credibility index, and NLP signals.
- **`/api/evaluate-news`** — Live news testing endpoint updating dynamic confusion matrices and evaluation metrics in real time.
- **`/api/verify-prediction`** — Endpoint for user ground-truth labeling and metric calibration.
- **`/api/reset-live-metrics`** — Endpoint to reset the live evaluation session back to verified baseline records.
- **`/history/export.csv`** — Filtered prediction history export with UTF-8 BOM encoding.
- **`/history/clear`** — Secure history purge scoped to the authenticated user.
- **`/workflow`** — End-to-end NLP architecture, preprocessing, TF-IDF engineering, and inference workflow visualizer.
- **`/about`** — Project background, dataset specifications, algorithms, and responsible AI documentation.
- **`/account`** — Profile details, session lifetime, personal prediction statistics, and accuracy tracking.

---

## Project Structure

```
Fake-News-Detection/
├── dataset/
│   ├── Fake.csv                       # Documented disinformation corpus
│   ├── True.csv                       # Authentic news reporting corpus
│   └── VerifiedExamples.csv           # Ground-truth verified benchmark samples
├── model/
│   ├── best_model.txt                 # Active classifier identifier (SVM)
│   ├── fake_news_model.pkl            # Active production pipeline
│   ├── model_logistic_regression.pkl  # Trained Logistic Regression pipeline
│   ├── model_svm.pkl                  # Trained Linear SVM pipeline
│   ├── model_random_forest.pkl        # Trained Random Forest ensemble pipeline
│   ├── tfidf_vectorizer.pkl           # Fitted 50,000 feature TF-IDF vectorizer
│   └── model_comparison.csv          # Held-out benchmark metrics
├── static/
│   ├── confusion_matrix.json          # Benchmark confusion matrix counts
│   ├── script.js                      # Reactive frontend, SVG dial, dynamic AJAX updater
│   └── style.css                      # Cyber-glassmorphic responsive dark theme
├── templates/
│   ├── index.html                     # AI Workspace Dashboard & News Analyzer
│   ├── comparison.html                # Live Dynamic Evaluation & Benchmark Comparison
│   ├── workflow.html                  # NLP Architecture Visualizer
│   ├── about.html                     # Architecture, Stack & Responsible AI
│   ├── account.html                   # User profile & personal analytics
│   ├── login.html                     # Glass card sign-in
│   └── register.html                  # Glass card account registration
├── app.py                             # Flask application & multi-model inference server
├── check_model.py                     # Held-out class balance and verification verification script
├── news_text.py                       # Preprocessing and text normalization helper
├── requirements.txt                   # Dependency manifest
└── train_model.py                     # Full training script for all 3 models
```
