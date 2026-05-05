"""
sop2_pipeline.py  —  SOP-2: Order Intake & Processing
------------------------------------------------------
Polls Etsy for new orders, writes them to the data directory, and marks
each order as acknowledged in Etsy so that downstream SOPs can pick them up.

Usage:
    python sop2_pipeline.py [--dry-run]

Environment variables (see .env.example):
    ETSY_API_KEY    Etsy API key
    ETSY_SHOP_ID    Etsy shop ID
    DATA_DIR        Directory for order output files (default: data)
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
logger = logging.getLogger("sop2_pipeline")

ETSY_API_BASE = "https://openapi.etsy.com/v3"
_PAGE_SIZE = 100


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fetch_open_orders(shop_id: str) -> list[dict]:
    """Retrieve all open (unacknowledged) orders from Etsy, paginating as needed."""
    url = f"{ETSY_API_BASE}/application/shops/{shop_id}/receipts"
    all_orders: list[dict] = []
    offset = 0
    while True:
        params = {"was_paid": True, "was_shipped": False, "limit": _PAGE_SIZE, "offset": offset}
        try:
            response = requests.get(url, headers=etsy_headers(), params=params, timeout=30)
            response.raise_for_status()
            page = response.json().get("results", [])
        except requests.RequestException as exc:
            logger.error("Failed to fetch orders: %s", exc)
            break
        all_orders.extend(page)
        if len(page) < _PAGE_SIZE:
            break
        offset += _PAGE_SIZE
    return all_orders


def _acknowledge_order(shop_id: str, receipt_id: str) -> bool:
    """Mark an Etsy order receipt as acknowledged."""
    url = f"{ETSY_API_BASE}/application/shops/{shop_id}/receipts/{receipt_id}"
    try:
        response = requests.put(url, json={"was_paid": True}, headers=etsy_headers(), timeout=30)
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        logger.error("Failed to acknowledge order %s: %s", receipt_id, exc)
        return False


def _save_order(order: dict, data_dir: str) -> str:
    """Persist an order dict as a JSON file and return the filepath."""
    os.makedirs(data_dir, exist_ok=True)
    receipt_id = order.get("receipt_id", "unknown")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"order_{receipt_id}_{timestamp}.json"
    filepath = os.path.join(data_dir, filename)
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(order, fh, indent=2)
    return filepath


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(dry_run: bool = False) -> int:
    """Run SOP-2. Returns the number of processing failures."""
    shop_id = os.getenv("ETSY_SHOP_ID", "")
    data_dir = os.getenv("DATA_DIR", "data")

    if not shop_id and not dry_run:
        raise EnvironmentError("ETSY_SHOP_ID is not set")

    if dry_run:
        logger.info("[dry-run] SOP-2: Would fetch and persist open orders.")
        return 0

    orders = _fetch_open_orders(shop_id)
    logger.info("SOP-2: %d open order(s) retrieved.", len(orders))

    failures = 0
    for order in orders:
        receipt_id = str(order.get("receipt_id", ""))
        try:
            filepath = _save_order(order, data_dir)
            logger.info("Saved order %s → %s", receipt_id, filepath)
            if not _acknowledge_order(shop_id, receipt_id):
                failures += 1
        except OSError as exc:
            logger.error("Could not save order %s: %s", receipt_id, exc)
            failures += 1

    logger.info("SOP-2 complete — %d failure(s).", failures)
    return failures


if __name__ == "__main__":
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )
    parser = argparse.ArgumentParser(description="SOP-2: Order intake & processing")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without making API calls")
    args = parser.parse_args()
    sys.exit(run(dry_run=args.dry_run))
