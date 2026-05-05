"""
sop5_lifecycle.py  —  SOP-5: Product Lifecycle & Inventory Management
----------------------------------------------------------------------
Reviews all active listings, flags slow-moving or out-of-stock items,
updates quantities where needed, and deactivates listings that have
exhausted their inventory.

Lifecycle rules:
    quantity == 0       → deactivate listing (status = inactive)
    quantity <= LOW_STOCK_THRESHOLD → emit a low-stock warning
    listing age > MAX_LISTING_DAYS  → flag for renewal

Usage:
    python sop5_lifecycle.py [--dry-run]

Environment variables (see .env.example):
    ETSY_API_KEY    Etsy API key
    ETSY_SHOP_ID    Etsy shop ID
    DATA_DIR        Directory for lifecycle report output (default: data)
    LOG_LEVEL       Logging level (default: INFO)
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

from etsy_client import etsy_headers

load_dotenv()
logger = logging.getLogger("sop5_lifecycle")

ETSY_API_BASE = "https://openapi.etsy.com/v3"
LOW_STOCK_THRESHOLD = 3
MAX_LISTING_DAYS = 120
_PAGE_SIZE = 100


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fetch_active_listings(shop_id: str) -> list[dict]:
    """Retrieve all active listings for the shop, paginating as needed."""
    url = f"{ETSY_API_BASE}/application/shops/{shop_id}/listings/active"
    all_listings: list[dict] = []
    offset = 0
    while True:
        try:
            response = requests.get(
                url, headers=etsy_headers(), params={"limit": _PAGE_SIZE, "offset": offset}, timeout=30
            )
            response.raise_for_status()
            page = response.json().get("results", [])
        except requests.RequestException as exc:
            logger.error("Failed to fetch active listings: %s", exc)
            break
        all_listings.extend(page)
        if len(page) < _PAGE_SIZE:
            break
        offset += _PAGE_SIZE
    return all_listings


def _deactivate_listing(shop_id: str, listing_id: str) -> bool:
    """Set a listing to inactive."""
    url = f"{ETSY_API_BASE}/application/shops/{shop_id}/listings/{listing_id}"
    try:
        response = requests.patch(url, json={"state": "inactive"}, headers=etsy_headers(), timeout=30)
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        logger.error("Failed to deactivate listing %s: %s", listing_id, exc)
        return False


def _renew_listing(shop_id: str, listing_id: str) -> bool:
    """Renew an ageing listing to reset its expiry clock."""
    url = f"{ETSY_API_BASE}/application/shops/{shop_id}/listings/{listing_id}/renew"
    try:
        response = requests.put(url, headers=etsy_headers(), timeout=30)
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        logger.error("Failed to renew listing %s: %s", listing_id, exc)
        return False


def _listing_age_days(listing: dict) -> float:
    """Return the age of a listing in days (using creation_tsz epoch field)."""
    creation_ts = listing.get("creation_tsz") or listing.get("creation_timestamp", 0)
    if not creation_ts:
        return 0.0
    created = datetime.fromtimestamp(int(creation_ts), tz=timezone.utc)
    return (datetime.now(tz=timezone.utc) - created).days


def _save_report(report: dict, data_dir: str) -> str:
    os.makedirs(data_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filepath = os.path.join(data_dir, f"lifecycle_report_{timestamp}.json")
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    return filepath


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(dry_run: bool = False) -> int:
    """Run SOP-5. Returns the number of action failures."""
    shop_id = os.getenv("ETSY_SHOP_ID", "")
    data_dir = os.getenv("DATA_DIR", "data")

    if not shop_id and not dry_run:
        raise EnvironmentError("ETSY_SHOP_ID is not set")

    if dry_run:
        logger.info("[dry-run] SOP-5: Would audit listing lifecycle and inventory.")
        return 0

    listings = _fetch_active_listings(shop_id)
    logger.info("SOP-5: Auditing %d active listing(s).", len(listings))

    deactivated, renewed, low_stock_warnings, failures = [], [], [], 0

    for listing in listings:
        listing_id = str(listing.get("listing_id", ""))
        title = listing.get("title", listing_id)
        quantity = listing.get("quantity", 0)
        age_days = _listing_age_days(listing)

        if quantity == 0:
            logger.info("Deactivating out-of-stock listing: %s", title)
            if _deactivate_listing(shop_id, listing_id):
                deactivated.append(listing_id)
            else:
                failures += 1
        elif quantity <= LOW_STOCK_THRESHOLD:
            logger.warning("Low stock (%d remaining): %s", quantity, title)
            low_stock_warnings.append({"listing_id": listing_id, "title": title, "quantity": quantity})

        if age_days >= MAX_LISTING_DAYS:
            logger.info("Renewing ageing listing (%d days old): %s", int(age_days), title)
            if _renew_listing(shop_id, listing_id):
                renewed.append(listing_id)
            else:
                failures += 1

    report = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "deactivated": deactivated,
        "renewed": renewed,
        "low_stock_warnings": low_stock_warnings,
        "failures": failures,
    }
    filepath = _save_report(report, data_dir)
    logger.info("SOP-5: Lifecycle report written to %s", filepath)
    logger.info(
        "SOP-5 complete — deactivated: %d, renewed: %d, low-stock warnings: %d, failures: %d",
        len(deactivated),
        len(renewed),
        len(low_stock_warnings),
        failures,
    )
    return failures


if __name__ == "__main__":
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )
    parser = argparse.ArgumentParser(description="SOP-5: Product lifecycle & inventory management")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without making API calls")
    args = parser.parse_args()
    sys.exit(run(dry_run=args.dry_run))
