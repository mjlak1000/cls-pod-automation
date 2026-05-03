"""
sop3_pipeline.py  —  SOP-3: Fulfillment & Shipping Dispatch
------------------------------------------------------------
Reads saved order files from the data directory, submits each unpacked
order to the shipping provider, records the tracking number back to Etsy,
and archives the order file.

Usage:
    python sop3_pipeline.py [--dry-run]

Environment variables (see .env.example):
    ETSY_API_KEY          Etsy API key
    ETSY_SHOP_ID          Etsy shop ID
    SHIPPING_PROVIDER     Carrier name passed to the shipping API (default: usps)
    SHIPPING_API_KEY      API key for the shipping provider
    DATA_DIR              Directory containing order JSON files (default: data)
    LOG_LEVEL             Logging level (default: INFO)
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("sop3_pipeline")

ETSY_API_BASE = "https://openapi.etsy.com/v3"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _etsy_headers() -> dict:
    api_key = os.getenv("ETSY_API_KEY", "")
    if not api_key:
        raise EnvironmentError("ETSY_API_KEY is not set")
    return {"x-api-key": api_key, "Content-Type": "application/json"}


def _load_pending_orders(data_dir: str) -> list[tuple[Path, dict]]:
    """Return (path, order_dict) tuples for every order_*.json in *data_dir*."""
    results = []
    if not os.path.isdir(data_dir):
        return results
    for entry in sorted(Path(data_dir).glob("order_*.json")):
        try:
            with entry.open(encoding="utf-8") as fh:
                results.append((entry, json.load(fh)))
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Could not read %s: %s", entry, exc)
    return results


def _create_shipment(order: dict, provider: str, shipping_api_key: str) -> str | None:
    """Submit a shipment request and return the tracking number, or None on failure."""
    ship_to = order.get("buyer_address", {})
    items = order.get("transactions", [])
    payload = {
        "carrier": provider,
        "to_address": ship_to,
        "items": items,
    }
    headers = {"Authorization": f"Bearer {shipping_api_key}", "Content-Type": "application/json"}
    try:
        response = requests.post(
            "https://api.example-shipping.com/v1/shipments",
            json=payload,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json().get("tracking_number")
    except requests.RequestException as exc:
        logger.error("Shipping API error for order %s: %s", order.get("receipt_id"), exc)
        return None


def _update_etsy_tracking(shop_id: str, receipt_id: str, tracking_number: str, carrier: str) -> bool:
    """Post the tracking number back to Etsy."""
    url = f"{ETSY_API_BASE}/application/shops/{shop_id}/receipts/{receipt_id}/tracking"
    payload = {"tracking_code": tracking_number, "carrier_name": carrier, "send_bcc": True}
    try:
        response = requests.post(url, json=payload, headers=_etsy_headers(), timeout=30)
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        logger.error("Failed to update tracking for receipt %s: %s", receipt_id, exc)
        return False


def _archive_order(filepath: Path) -> None:
    """Rename an order file to mark it as shipped (add .shipped suffix)."""
    archived = filepath.with_suffix(".shipped.json")
    filepath.rename(archived)
    logger.debug("Archived %s → %s", filepath.name, archived.name)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(dry_run: bool = False) -> int:
    """Run SOP-3. Returns the number of failed shipments."""
    shop_id = os.getenv("ETSY_SHOP_ID", "")
    data_dir = os.getenv("DATA_DIR", "data")
    provider = os.getenv("SHIPPING_PROVIDER", "usps")
    shipping_api_key = os.getenv("SHIPPING_API_KEY", "")

    if not dry_run:
        if not shop_id:
            raise EnvironmentError("ETSY_SHOP_ID is not set")
        if not shipping_api_key:
            raise EnvironmentError("SHIPPING_API_KEY is not set")

    pending = _load_pending_orders(data_dir)
    logger.info("SOP-3: %d pending order(s) to fulfil.", len(pending))

    if dry_run:
        for path, order in pending:
            logger.info("[dry-run] Would ship order %s via %s", order.get("receipt_id"), provider)
        return 0

    failures = 0
    for path, order in pending:
        receipt_id = str(order.get("receipt_id", ""))
        tracking = _create_shipment(order, provider, shipping_api_key)
        if not tracking:
            failures += 1
            continue
        logger.info("Shipment created for order %s — tracking: %s", receipt_id, tracking)
        if not _update_etsy_tracking(shop_id, receipt_id, tracking, provider):
            failures += 1
            continue
        _archive_order(path)

    logger.info("SOP-3 complete — %d failure(s).", failures)
    return failures


if __name__ == "__main__":
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )
    parser = argparse.ArgumentParser(description="SOP-3: Fulfillment & shipping dispatch")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without making API calls")
    args = parser.parse_args()
    sys.exit(run(dry_run=args.dry_run))
