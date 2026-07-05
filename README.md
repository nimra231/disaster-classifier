# 🛰️ SENTINEL — AI-Powered Disaster Tweet Classifier

**Live Demo:** [disaster-classifier-slbdmkjrcmynqvfhhkpdn8.streamlit.app](https://disaster-classifier-slbdmkjrcmynqvfhhkpdn8.streamlit.app/)

SENTINEL is a real-time classification engine that scans tweets (or any short text), separates genuine disaster reports from noise, and scores severity in seconds — combining a fully explainable keyword engine with an independent Machine Learning cross-check.

During real disasters, thousands of social media posts are published every minute — far more than any emergency response team can read manually. SENTINEL explores how AI can help surface what actually matters, fast, while staying transparent about *why* it made a decision.

---

## ✨ Features

- 🔍 **106+ term keyword classification engine** — spans natural disasters, fire & explosion, structural accidents, violence & security, and health emergencies. Uses word-boundary regex matching so short words like "fire" don't false-positive on "fireplace," and multi-word phrases like "gas leak" are matched as whole phrases.
- 🧾 **"Why Flagged" breakdown** — every classification traces back to the exact keyword(s) that triggered it. No black-box guessing.
- 🤖 **ML Verification Layer** — a TF-IDF + Logistic Regression model, trained on a hand-labeled dataset (including paraphrased disaster reports with no exact keyword match), independently scores every tweet and cross-checks the keyword engine's verdict.
- ⚖️ **Verdict resolution logic** — combines both layers into a single final verdict:
  - Keyword + ML agree → verdict stands
  - Keyword flags it, ML strongly disagrees → downgraded & flagged for human review (catches false positives like *"my exam was a disaster"*)
  - No keyword match, but ML flags it → upgraded for review (catches paraphrased reports keywords alone would miss)
- 🌡️ **Live threat-level gauge** based on recent scan history
- 📍 **Automatic location detection** with map visualization (city/country gazetteer)
- 📊 **Analytics dashboard** — severity distribution, top keywords, top locations, top categories, and real model evaluation metrics (accuracy, precision, recall, F1)
- 📦 **Batch analysis mode** — classify up to 30 tweets at once with exportable CSV reports
- 📜 **Session history** with severity filtering and CSV export
- ⏱️ **Real measured scan latency** per classification
- 🎨 **Custom "Disaster Command Center" UI** — built end-to-end in Streamlit with a cinematic dark theme, animated embers, radar sweep, and responsive layout

---

## 🧠 How it works

1. **Ingest** — raw text comes in via the input box or batch paste.
2. **Keyword Match** — text is scanned against the 106+ term dictionary using word-boundary regex.
3. **Severity Scoring** — each matched term carries a severity weight (Critical / High / Medium); the tweet inherits its highest-weight match, and a weighted sum drives the confidence score.
4. **Location Extraction** — a city/country gazetteer is checked against the text and plotted on a map if matched.
5. **Action Recommendation** — severity maps to a suggested response tier (decision-support signal, not automated dispatch).
6. **ML Cross-Check** — an independently trained TF-IDF + Logistic Regression model scores the same text and either confirms, downgrades, or upgrades the keyword verdict.

---

## 🛠️ Tech Stack

- **Frontend/App:** Streamlit
- **ML:** scikit-learn (TF-IDF Vectorizer + Logistic Regression)
- **Data handling:** pandas, NumPy
- **Visualization:** Matplotlib, Streamlit native charts/maps
- **Language:** Python

---

## 🚀 Running Locally

```bash
# Clone the repo
git clone https://github.com/nimra231/disaster-classifier.git
cd disaster-classifier

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## ⚠️ Known Limitations

This is a **portfolio-scale project**, and I want to be upfront about that:

- It does **not** yet pull from a live social media feed — input is manual (single tweet or batch paste).
- The ML layer is trained on a small, hand-labeled dataset (~150 examples), not a large public benchmark. Reported accuracy/precision/recall/F1 metrics should be treated as an internal sanity check, not a rigorous evaluation.
- Location detection relies on a fixed gazetteer of cities/countries, not full NLP-based geoparsing.

### Roadmap ideas
- Swap in a larger labeled dataset (e.g., the public *"Real or Not? NLP with Disaster Tweets"* dataset) for a stronger, more generalizable ML layer
- Connect to a live streaming API (e.g., Twitter/X API) for real-time ingestion
- Upgrade location extraction to a proper NLP-based geoparser
- Add multi-language keyword support

---

## 🙋 Feedback

Try it on the [live demo](https://disaster-classifier-slbdmkjrcmynqvfhhkpdn8.streamlit.app/) with disaster-related keywords or paraphrased reports, and let me know what works, what doesn't, and what you'd improve.

---

**Built by Nimra Iftikhar**  · Real-Time Disaster Detection
