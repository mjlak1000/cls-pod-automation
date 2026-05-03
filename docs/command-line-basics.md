# Command-Line Basics

This document is a quick reference for running every script in **cls-etsy-automation** from the terminal.

---

## General conventions

- All scripts accept a `--dry-run` flag that simulates the operation without making live API calls.
- All scripts read configuration from the `.env` file (or environment variables).
- Exit code `0` means success; any non-zero code indicates failures.

---

## Schema Validator

```
python cls_schema_validator.py [--data-dir PATH]
```

| Flag | Default | Description |
|---|---|---|
| `--data-dir` | `data` | Directory containing JSON files to validate |

**Examples:**
```bash
# Validate the default data/ directory
python cls_schema_validator.py

# Validate a custom directory
python cls_schema_validator.py --data-dir /tmp/my-data
```

---

## SOP-1 — Listing Creation & Product Sync

```
python sop1_pipeline.py [--dry-run]
```

Loads product JSON files from `DATA_DIR`, validates them against the CLS schema, then creates or updates the corresponding Etsy listings.

```bash
python sop1_pipeline.py
python sop1_pipeline.py --dry-run
```

---

## SOP-2 — Order Intake & Processing

```
python sop2_pipeline.py [--dry-run]
```

Polls Etsy for new paid orders, saves each one as a JSON file in `DATA_DIR`, and acknowledges receipt.

```bash
python sop2_pipeline.py
python sop2_pipeline.py --dry-run
```

---

## SOP-3 — Fulfillment & Shipping Dispatch

```
python sop3_pipeline.py [--dry-run]
```

Reads `order_*.json` files from `DATA_DIR`, submits each to the configured shipping provider, and posts tracking numbers back to Etsy.

```bash
python sop3_pipeline.py
python sop3_pipeline.py --dry-run
```

---

## SOP-4 — Customer Review Sentiment Analysis

```
python sop4_sentiment_parser.py [--dry-run]
```

Fetches recent Etsy reviews, scores their sentiment with TextBlob, and writes a JSON report to `DATA_DIR`.

```bash
python sop4_sentiment_parser.py
python sop4_sentiment_parser.py --dry-run
```

---

## SOP-5 — Product Lifecycle & Inventory Management

```
python sop5_lifecycle.py [--dry-run]
```

Audits all active listings: deactivates out-of-stock items, renews ageing listings, and emits low-stock warnings. Writes a lifecycle report to `DATA_DIR`.

```bash
python sop5_lifecycle.py
python sop5_lifecycle.py --dry-run
```

---

## Scheduler

```
python scheduler.py
```

Runs all five SOPs on the intervals configured in `.env`. There are no additional flags; edit `.env` to change intervals.

```bash
python scheduler.py        # start
# Ctrl+C to stop
```

---

## QA Runner

```
bash run_qa.sh
```

Runs schema validation, dry-run validation of every SOP pipeline, and a Python syntax check across all scripts.

```bash
bash run_qa.sh
```

---

## Environment variables quick reference

| Variable | Used by | Description |
|---|---|---|
| `ETSY_API_KEY` | all SOPs | Etsy Open API v3 key |
| `ETSY_SHOP_ID` | all SOPs | Your Etsy shop ID |
| `SHIPPING_PROVIDER` | SOP-3 | Carrier name (e.g. `usps`) |
| `SHIPPING_API_KEY` | SOP-3 | Shipping provider API key |
| `DATA_DIR` | all SOPs | Data directory (default: `data`) |
| `LOG_LEVEL` | all scripts | Python log level (default: `INFO`) |
| `SOP1_INTERVAL_MINUTES` | scheduler | Run interval for SOP-1 |
| `SOP2_INTERVAL_MINUTES` | scheduler | Run interval for SOP-2 |
| `SOP3_INTERVAL_MINUTES` | scheduler | Run interval for SOP-3 |
| `SOP4_INTERVAL_MINUTES` | scheduler | Run interval for SOP-4 |
| `SOP5_INTERVAL_MINUTES` | scheduler | Run interval for SOP-5 |
