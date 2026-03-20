from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import re

# -------------------------
# setup driver
# -------------------------
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.fonts": 2
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)

    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd(
        "Network.setBlockedURLs",
        {
            "urls": [
                "*.jpg", "*.jpeg", "*.png", "*.gif", "*.webp",
                "*.woff", "*.woff2", "*.ttf",
                "*.mp4", "*.webm"
            ]
        }
    )

    return driver


# -------------------------
# accept cookies
# -------------------------
def accept_cookies(driver):
    try:
        wait = WebDriverWait(driver, 5)
        btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//button//span[contains(text(),"Accept")]')
        ))
        btn.click()
        print("Cookies accepted")
    except:
        pass


# -------------------------
# extract reviews (UPDATED)
# -------------------------
def get_reviews(driver, base_url, start):
    url = f"{base_url}?start={start}"   # ✅ NOW USES INPUT URL
    driver.get(url)

    wait = WebDriverWait(driver, 15)

    accept_cookies(driver)

    try:
        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//span[@lang]')
        ))
    except:
        print("No reviews found.")
        return []

    time.sleep(2)

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    text_elements = driver.find_elements(By.XPATH, '//span[@lang]')

    print(f"Found {len(text_elements)} text elements")

    reviews = []

    for text_el in text_elements:
        # text
        try:
            text = text_el.text
        except:
            text = None

        # rating
        try:
            parent = text_el.find_element(
                By.XPATH,
                './ancestor::div[.//*[@role="img" and contains(@aria-label, "ster")]][1]'
            )

            rating_el = parent.find_element(
                By.XPATH,
                './/*[@role="img" and contains(@aria-label, "ster")]'
            )

            rating = rating_el.get_attribute("aria-label")

            match = re.search(r'[\d.,]+', rating)
            rating_number = float(match.group().replace(',', '.')) if match else None

        except Exception as e:
            print("Rating error:", e)
            rating_number = None

        reviews.append({
            "text": text,
            "rating": rating_number
        })

    return reviews


# -------------------------
# MAIN FUNCTION (NEW)
# -------------------------
def scrape_yelp(base_url, max_pages=10):
    if not base_url.startswith("http"):
        base_url = "https://" + base_url
    driver = setup_driver()
    all_reviews = []

    try:
        for page in range(max_pages):
            start = page * 10
            print(f"\nScraping reviews starting at {start}...")

            reviews = get_reviews(driver, base_url, start)

            if not reviews:
                print("Stopping: no reviews found.")
                break

            all_reviews.extend(reviews)

            time.sleep(random.uniform(2, 4))

    finally:
        driver.quit()

    return all_reviews

import nltk
import spacy
from collections import Counter

nltk.download('punkt')
nlp = spacy.load("en_core_web_sm")

#aspect extraction
def extract_aspects(text):
    doc = nlp(text)
    aspects = []

    for chunk in doc.noun_chunks:
        #use root word
        aspect = chunk.root.text.lower()
        
        if len(aspect) > 2:
            aspects.append(aspect)
    
    return aspects

def remove_pronouns(text):
    doc = nlp(text)
    
    cleaned_tokens = []
    
    for token in doc:
        #remove pronouns so we do not get words like "they" in the output
        if token.pos_ != "PRON":
            cleaned_tokens.append(token.text)
    
    return " ".join(cleaned_tokens)

def analyze_reviews(reviews):
    positive_aspects = []
    negative_aspects = []

    for r in reviews:
        if not r["text"] or not r["rating"]:
            continue

        cleaned_text = remove_pronouns(r["text"])
        aspects = extract_aspects(cleaned_text)

        if r["rating"] > 3:
            positive_aspects.extend(aspects)
        else:
            negative_aspects.extend(aspects)

    pos_counter = Counter(positive_aspects)
    neg_counter = Counter(negative_aspects)

    avg_rating = round(sum(r["rating"] for r in reviews if r["rating"]) / len(reviews), 2)

    return {
        "avg_rating": avg_rating,
        "count": len(reviews),
        "positive": pos_counter.most_common(3),
        "negative": neg_counter.most_common(3)
    }

import streamlit as st

st.title("🍽️ Yelp Review Analyzer")

url = st.text_input("Paste Yelp restaurant URL")

if url:
    st.write("Analyzing:", url)

    with st.spinner("Scraping reviews..."):
        reviews = scrape_yelp(url)

    if not reviews:
        st.error("No reviews found. Check the URL.")
    else:
        with st.spinner("Analyzing reviews..."):
            results = analyze_reviews(reviews)

        st.subheader("Results")

        st.metric("⭐ Average Rating", results['avg_rating'])
        st.metric("📊 Reviews Analyzed", results['count'])

        st.write("👍 **Most praised:**")
        for aspect, count in results["positive"]:
            st.write(f"- {aspect} ({count})")

        st.write("👎 **Most complained about:**")
        for aspect, count in results["negative"]:
            st.write(f"- {aspect} ({count})")