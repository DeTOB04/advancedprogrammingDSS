# 🍽️ Yelp Review Analyzer

A local tool that scrapes reviews from any Yelp restaurant page and uses NLP to surface what customers love and complain about most.

---

## What it does:
- **Scrapes reviews:** navigates through all pages of a Yelp restaurant listing using Selenium and Chrome
- **Analyzes sentiment:** splits reviews into positive (> 3 stars) and negative (≤ 3 stars)
- **Extracts key aspects:** uses spaCy NLP to identify the most frequently mentioned topics in each group
- **Shows results:** displays average rating, total review count, top 3 praised aspects, and top 3 complained-about aspects in a Streamlit web UI

---

## Requirements
- **Anaconda** or **Miniconda**
- **Google Chrome** (used by Selenium for scraping)

> ⚠️ Make sure all files are in the same folder before running.

---

## How to run

**Windows:**
```
.\run.bat
```

**macOS / Linux:**
```bash
bash run.sh
```

The script will:
1. Detect your conda installation automatically
2. Create a `yelp_scraper` conda environment (Python 3.11) if it doesn't exist yet
3. Install all required packages (`selenium`, `streamlit`, `nltk`, `spacy`)
4. Download the spaCy English model (`en_core_web_sm`) and NLTK data
5. Launch the Streamlit app in your browser

---

## Usage
1. Open the Streamlit page that appears in your browser
2. Paste a Yelp restaurant URL (e.g. `https://www.yelp.com/biz/some-restaurant`)
3. Press Enter and wait

---

## Output

| Field | Description |
|---|---|
| ⭐ Average Rating | Mean star rating across all scraped reviews |
| 📊 Reviews Analyzed | Total number of reviews collected |
| 👍 Most praised | Top 3 aspects mentioned in positive reviews (> 3 stars) |
| 👎 Most complained about | Top 3 aspects mentioned in negative reviews (≤ 3 stars) |
