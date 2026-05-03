"""
sop1_pipeline.py  —  SOP-1: Listing Creation & Product Sync
------------------------------------------------------------
Fetches product data from the local data directory, validates each record
against the CLS schema, and creates or updates Etsy listings via the
Etsy Open API v3.

Usage:
    python sop1_pipeline.py [--dry-run]

Environment variables (see .env.example):
    ETSY_API_KEY    Etsy API key
    ETSY_SHOP_ID    Etsy shop ID
    DATA_DIR        Directory containing product JSON files (default: data)
    LOG_LEVEL       Logging level (default: INFO)
"""

import argparse
import json
import logging
import os
import sys

import requests
from dotenv import load_dotenv

import cls_schema_validator

load_dotenv()
logger = logging.getLogger("sop1_pipeline")

ETSY_API_BASE = "https://openapi.etsy.com/v3"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _headers() -> dict:
    api_key = os.getenv("ETSY_API_KEY", "")
    if not api_key:
        raise EnvironmentError("ETSY_API_KEY is not set")
    return {"x-api-key": api_key, "Content-Type": "application/json"}


def _load_products(data_dir: str) -> list[dict]:
    """Load all product JSON files from *data_dir*."""
    products: list[dict] = []
    if not os.path.isdir(data_dir):
        logger.warning("Data directory '%s' does not exist — no products loaded.", data_dir)
        return products

    for filename in sorted(os.listdir(data_dir)):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(data_dir, filename)
        try:
            with open(filepath, encoding="utf-8") as fh:
                data = json.load(fh)
            records = data if isinstance(data, list) else [data]
            products.extend(records)
            logger.debug("Loaded %d record(s) from %s", len(records), filename)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to load %s: %s", filepath, exc)

    return products


def _upsert_listing(product: dict, shop_id: str, dry_run: bool = False) -> bool:
    """Create or update a single Etsy listing. Returns True on success."""
    listing_id = product.get("listing_id")
    payload = {
        "title": product["title"],
        "description": product.get("description", ""),
        "price": {"amount": int(product["price"] * 100), "divisor": 100, "currency_code": "USD"},
        "quantity": product["quantity"],
        "state": product.get("status", "draft"),
        "taxonomy_id": product.get("taxonomy_id", 1),
        "tags": product.get("tags", []),
        "sku": product.get("sku", ""),
    }

    if dry_run:
        action = "UPDATE" if listing_id else "CREATE"
        logger.info("[dry-run] Would %s listing: %s", action, product.get("title"))
        return True

    try:
        if listing_id:
            url = f"{ETSY_API_BASE}/application/shops/{shop_id}/listings/{listing_id}"
            response = requests.patch(url, json=payload, headers=_headers(), timeout=30)
        else:
            url = f"{ETSY_API_BASE}/application/shops/{shop_id}/listings"
            response = requests.post(url, json=payload, headers=_headers(), timeout=30)

        response.raise_for_status()
        logger.info("Synced listing '%s' (id=%s)", product.get("title"), listing_id)
        return True
    except requests.RequestException as exc:
        logger.error("Failed to sync listing '%s': %s", product.get("title"), exc)
        return False


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(dry_run: bool = False) -> int:
    """Run SOP-1. Returns the number of failed upserts."""
    data_dir = os.getenv("DATA_DIR", "data")
    shop_id = os.getenv("ETSY_SHOP_ID", "")

    if not shop_id and not dry_run:
        raise EnvironmentError("ETSY_SHOP_ID is not set")

    products = _load_products(data_dir)
    if not products:
        logger.info("SOP-1: No products found — nothing to sync.")
        return 0

    # Validate before syncing
    failures = 0
    valid_products = []
    for product in products:
        errors = cls_schema_validator.validate_record(product, cls_schema_validator.CLS_SCHEMA)
        if errors:
            logger.warning("Skipping invalid product '%s': %s", product.get("title"), errors)
            failures += 1
        else:
            valid_products.append(product)

    logger.info("SOP-1: %d valid product(s) to sync.", len(valid_products))

    for product in valid_products:
        if not _upsert_listing(product, shop_id, dry_run=dry_run):
            failures += 1

    logger.info("SOP-1 complete — %d failure(s).", failures)
    return failures


if __name__ == "__main__":
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )
    parser = argparse.ArgumentParser(description="SOP-1: Listing creation & product sync")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without making API calls")
    args = parser.parse_args()
    sys.exit(run(dry_run=args.dry_run))
