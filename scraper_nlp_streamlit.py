from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
from collections import Counter
import streamlit as st
import random
import time
import re

import nltk
import spacy

nltk.download('punkt')
nlp = spacy.load("en_core_web_sm")


# -------------------------
# DRIVER SETUP
# -------------------------

def setup_driver():
    """
    Initializes and returns a Chrome WebDriver with performance optimizations.
    Images, fonts, and media are blocked to speed up scraping.
    AutomationControlled flag is disabled to reduce bot detection.
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Disable images and fonts via Chrome preferences to speed up page loads
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.fonts": 2
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)

    # Also block media/image URLs at the network level for extra speed
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
# COOKIE HANDLING
# -------------------------

def decline_cookies(driver):
    """
    Clicks the 'reject non-essential cookies' button on the OneTrust banner.
    Uses the stable button ID which is consistent across all Yelp language versions,
    so no language-specific text matching is needed.
    Silently passes if no banner appears.
    """
    try:
        wait = WebDriverWait(driver, 5)
        btn = wait.until(EC.element_to_be_clickable(
            (By.ID, "onetrust-reject-all-handler")
        ))
        btn.click()
        print("Cookies declined.")
    except:
        pass  # No cookie banner appeared, continue normally


# -------------------------
# NORMALIZING URL
# -------------------------

def normalize_url(url):
    """
    Strips the 'start' parameter from a Yelp URL so scraping always
    begins from page 1, even if the user pastes a mid-pagination link.

    e.g. https://yelp.nl/biz/place?osq=fastfood&start=70
      -> https://yelp.nl/biz/place?osq=fastfood
    """
    parsed = urlparse(url)
    # Parse query params and remove 'start' if present
    params = parse_qs(parsed.query, keep_blank_values=True)
    params.pop("start", None)
    # Flatten lists back (parse_qs returns {'key': ['val']})
    flat_params = {k: v[0] for k, v in params.items()}
    clean_query = urlencode(flat_params)
    return urlunparse(parsed._replace(query=clean_query))


# -------------------------
# PAGINATION
# -------------------------

def get_next_page_url(driver):
    """
    Checks whether a 'next page' link exists on the current page.

    On Yelp, the next-page button is an <a> tag with an href when there are
    more pages, but becomes a plain <div> (no href) on the last page.

    Returns the href URL string if a next page exists, otherwise None.
    """
    try:
        next_link = driver.find_element(
            By.XPATH,
            '//a[contains(@class, "next-link") and contains(@class, "navigation-button")]'
        )
        href = next_link.get_attribute("href")
        # Return the URL only if it's a real link (not None or empty)
        return href if href else None
    except:
        # Element not found or is a <div> instead of <a> — we're on the last page
        return None


# -------------------------
# REVIEW EXTRACTION
# -------------------------

def extract_reviews_from_page(driver):
    """
    Extracts all reviews from the currently loaded page.

    Note: this function assumes the page is already loaded and cookies have
    been handled by the caller (scrape_yelp). It only handles waiting for
    review elements, scrolling, and extracting data.

    Each review is a dict with:
      - 'text':   the review body (str or None)
      - 'rating': the star rating as a float (e.g. 4.0), or None if not found

    Returns a list of review dicts.
    """
    wait = WebDriverWait(driver, 15)

    # Wait until at least one review text element is present
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, '//span[@lang]')))
    except:
        print("No review text elements found on this page.")
        return []

    # Allow dynamic content to settle before extracting
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    # All review text elements are <span> tags with a 'lang' attribute
    text_elements = driver.find_elements(By.XPATH, '//span[@lang]')
    print(f"Found {len(text_elements)} review text elements on this page.")

    reviews = []

    for text_el in text_elements:
        # --- Extract review text ---
        try:
            text = text_el.text
        except:
            text = None

        # --- Extract star rating ---
        # Navigate up the DOM to find the ancestor that contains the rating image,
        # then read its aria-label (e.g. "4 sterren" on Dutch Yelp)
        try:
            parent = text_el.find_element(
                By.XPATH,
                './ancestor::div[.//*[@role="img" and (contains(@aria-label, "star") or contains(@aria-label, "ster") or contains(@aria-label, "étoile") or contains(@aria-label, "Stern"))]][1]'
            )
            rating_el = parent.find_element(
                By.XPATH,
                './/*[@role="img" and (contains(@aria-label, "star") or contains(@aria-label, "ster") or contains(@aria-label, "étoile") or contains(@aria-label, "Stern"))]'
            )
            rating_label = rating_el.get_attribute("aria-label")

            # Parse the numeric rating from the aria-label string
            match = re.search(r'[\d.,]+', rating_label)
            rating_number = float(match.group().replace(',', '.')) if match else None

        except Exception as e:
            print(f"Could not extract rating: {e}")
            rating_number = None

        reviews.append({"text": text, "rating": rating_number})

    return reviews


# -------------------------
# MAIN SCRAPER
# -------------------------

def scrape_yelp(base_url, max_pages=15):
    """
    Scrapes reviews from a Yelp restaurant page by following 'next page' links.

    Instead of constructing URLs with ?start=N (which caused repeated scraping
    of the same page), we now detect the actual 'next' button href and follow it.
    Scraping stops when no next-page link is found (i.e. we're on the last page).

    The URL is normalized before scraping to strip any 'start' parameter, so
    pasting a mid-pagination link still starts from page 1.

    Args:
        base_url  (str): The Yelp restaurant URL to start scraping from.
        max_pages (int): Safety cap on the number of pages to scrape (default 15,
                         covering up to ~150 reviews). Increase if needed.

    Returns:
        list of dicts: All reviews collected across all pages.
    """
    if not base_url.startswith("http"):
        base_url = "https://" + base_url

    # Strip any 'start' param so we always begin from page 1
    base_url = normalize_url(base_url)

    driver = setup_driver()
    all_reviews = []
    current_url = base_url

    try:
        # Use 1-based page numbering for readable debug output
        for page in range(1, max_pages + 1):
            print(f"\n--- Scraping page {page} ---")
            print(f"URL: {current_url}")

            # Navigate to the current page
            driver.get(current_url)

            # Handle cookie consent on first load
            decline_cookies(driver)

            # Extract reviews from the already-loaded page
            reviews = extract_reviews_from_page(driver)

            # DEBUG: print first review of each page to verify pages are actually different
            #if reviews:
            #    first_text = reviews[0]["text"] or ""
            #    first_rating = reviews[0]["rating"]
            #    preview = first_text.replace("\n", " ").strip()[:60]
            #    print(f"[DEBUG] Page {page} | First review preview: '{preview}' | Rating: {first_rating}")

            if not reviews:
                print("No reviews found on this page. Stopping.")
                break

            all_reviews.extend(reviews)
            print(f"Total reviews collected so far: {len(all_reviews)}")

            # Check if there is a next page to navigate to
            next_url = get_next_page_url(driver)
            if not next_url:
                print("No next page link found — reached the last page.")
                break

            # Move to the next page and add a polite delay to avoid rate limiting
            current_url = next_url
            time.sleep(random.uniform(2, 4))

    finally:
        # Always close the browser, even if an error occurred
        driver.quit()

    return all_reviews


# -------------------------
# NLP: TEXT CLEANING
# -------------------------

def remove_pronouns(text):
    """
    Removes pronouns from text using spaCy POS tagging.
    This prevents generic words like 'they', 'it', 'we' from appearing
    in the aspect frequency results.
    """
    doc = nlp(text)
    cleaned_tokens = [token.text for token in doc if token.pos_ != "PRON"]
    return " ".join(cleaned_tokens)


# -------------------------
# NLP: ASPECT EXTRACTION
# -------------------------

def extract_aspects(text):
    """
    Extracts meaningful noun aspects from text using spaCy noun chunks.
    Uses the root word of each chunk (e.g. 'the great food' → 'food').
    Filters out very short words (≤ 2 chars) to remove noise.
    """
    doc = nlp(text)
    aspects = []

    for chunk in doc.noun_chunks:
        aspect = chunk.root.text.lower()
        if len(aspect) > 2:
            aspects.append(aspect)

    return aspects


# -------------------------
# REVIEW ANALYSIS
# -------------------------

def analyze_reviews(reviews):
    """
    Analyzes scraped reviews to extract:
      - Average star rating
      - Total review count
      - Top 3 most praised aspects (from reviews rated > 3 stars)
      - Top 3 most complained-about aspects (from reviews rated ≤ 3 stars)

    Reviews with missing text or rating are skipped.

    Returns a dict with keys: avg_rating, count, positive, negative.
    """
    positive_aspects = []
    negative_aspects = []

    for r in reviews:
        # Skip reviews with missing data
        if not r["text"] or not r["rating"]:
            continue

        # Clean text and extract noun aspects
        cleaned_text = remove_pronouns(r["text"])
        aspects = extract_aspects(cleaned_text)

        # Separate aspects by sentiment based on star rating threshold
        if r["rating"] > 3:
            positive_aspects.extend(aspects)
        else:
            negative_aspects.extend(aspects)

    pos_counter = Counter(positive_aspects)
    neg_counter = Counter(negative_aspects)

    # Only count reviews that have a valid rating for the average
    rated_reviews = [r for r in reviews if r["rating"]]
    avg_rating = round(sum(r["rating"] for r in rated_reviews) / len(rated_reviews), 2) if rated_reviews else 0

    return {
        "avg_rating": avg_rating,
        "count": len(reviews),
        "positive": pos_counter.most_common(3),
        "negative": neg_counter.most_common(3)
    }


# -------------------------
# STREAMLIT UI
# -------------------------

st.title("🍽️ Yelp Review Analyzer")

url = st.text_input("Paste Yelp restaurant URL")

if url:
    st.write("Analyzing:", url)

    # Step 1: Scrape reviews by following next-page links
    with st.spinner("Scraping reviews..."):
        reviews = scrape_yelp(url)

    if not reviews:
        st.error("No reviews found. Please check the URL and try again.")
    else:
        # Step 2: Run NLP analysis on collected reviews
        with st.spinner("Analyzing reviews..."):
            results = analyze_reviews(reviews)

        st.subheader("Results")

        st.metric("⭐ Average Rating", results["avg_rating"])
        st.metric("📊 Reviews Analyzed", results["count"])

        st.write("👍 **Most praised:**")
        for aspect, count in results["positive"]:
            st.write(f"- {aspect} ({count}x mentioned)")

        st.write("👎 **Most complained about:**")
        for aspect, count in results["negative"]:
            st.write(f"- {aspect} ({count}x mentioned)")