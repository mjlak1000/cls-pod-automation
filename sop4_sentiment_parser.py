"""
sop4_sentiment_parser.py  —  SOP-4: Customer Review Sentiment Analysis
-----------------------------------------------------------------------
Fetches recent Etsy reviews for the shop, scores each review's text with
TextBlob, and writes a sentiment report to the data directory.

Sentiment buckets:
    positive  polarity >  0.1
    neutral   polarity in [-0.1, 0.1]
    negative  polarity < -0.1

Usage:
    python sop4_sentiment_parser.py [--dry-run]

Environment variables (see .env.example):
    ETSY_API_KEY        Etsy API key
    ETSY_SHOP_ID        Etsy shop ID
    SENTIMENT_ENGINE    Engine to use — only "textblob" is supported (default)
    DATA_DIR            Output directory for the sentiment report (default: data)
    LOG_LEVEL           Logging level (default: INFO)
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from textblob import TextBlob

from etsy_client import etsy_headers

load_dotenv()
logger = logging.getLogger("sop4_sentiment_parser")

ETSY_API_BASE = "https://openapi.etsy.com/v3"
_PAGE_SIZE = 100


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fetch_reviews(shop_id: str) -> list[dict]:
    """Retrieve all recent shop reviews from Etsy, paginating as needed."""
    url = f"{ETSY_API_BASE}/application/shops/{shop_id}/reviews"
    all_reviews: list[dict] = []
    offset = 0
    while True:
        try:
            response = requests.get(
                url, headers=etsy_headers(), params={"limit": _PAGE_SIZE, "offset": offset}, timeout=30
            )
            response.raise_for_status()
            page = response.json().get("results", [])
        except requests.RequestException as exc:
            logger.error("Failed to fetch reviews: %s", exc)
            break
        all_reviews.extend(page)
        if len(page) < _PAGE_SIZE:
            break
        offset += _PAGE_SIZE
    return all_reviews


def _score_review(review: dict) -> dict:
    """Analyse the sentiment of a single review dict and return an enriched dict."""
    text = review.get("review", "") or ""
    blob = TextBlob(text)
    polarity: float = blob.sentiment.polarity
    subjectivity: float = blob.sentiment.subjectivity

    if polarity > 0.1:
        bucket = "positive"
    elif polarity < -0.1:
        bucket = "negative"
    else:
        bucket = "neutral"

    return {
        "review_id": review.get("review_id"),
        "rating": review.get("rating"),
        "text": text,
        "polarity": round(polarity, 4),
        "subjectivity": round(subjectivity, 4),
        "sentiment": bucket,
    }


def _save_report(scored: list[dict], data_dir: str) -> str:
    """Write the scored reviews to a timestamped JSON report file."""
    os.makedirs(data_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filepath = os.path.join(data_dir, f"sentiment_report_{timestamp}.json")

    counts = {"positive": 0, "neutral": 0, "negative": 0}
    for item in scored:
        counts[item["sentiment"]] += 1

    report = {
        "generated_at": timestamp,
        "total_reviews": len(scored),
        "summary": counts,
        "reviews": scored,
    }
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    return filepath


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(dry_run: bool = False) -> int:
    """Run SOP-4. Returns 0 on success, 1 on failure."""
    shop_id = os.getenv("ETSY_SHOP_ID", "")
    data_dir = os.getenv("DATA_DIR", "data")

    if not shop_id and not dry_run:
        raise EnvironmentError("ETSY_SHOP_ID is not set")

    if dry_run:
        logger.info("[dry-run] SOP-4: Would fetch reviews and produce sentiment report.")
        return 0

    reviews = _fetch_reviews(shop_id)
    if not reviews:
        logger.info("SOP-4: No reviews found.")
        return 0

    logger.info("SOP-4: Scoring %d review(s)...", len(reviews))
    scored = [_score_review(r) for r in reviews]

    filepath = _save_report(scored, data_dir)
    logger.info("SOP-4: Sentiment report written to %s", filepath)

    positives = sum(1 for r in scored if r["sentiment"] == "positive")
    negatives = sum(1 for r in scored if r["sentiment"] == "negative")
    logger.info(
        "SOP-4 complete — %d positive, %d neutral, %d negative.",
        positives,
        len(scored) - positives - negatives,
        negatives,
    )
    return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )
    parser = argparse.ArgumentParser(description="SOP-4: Customer review sentiment analysis")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without making API calls")
    args = parser.parse_args()
    sys.exit(run(dry_run=args.dry_run))
