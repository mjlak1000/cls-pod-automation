# Installation Guide

This guide walks you through setting up **cls-etsy-automation** from scratch on macOS, Linux, or Windows (WSL).

---

## Prerequisites

| Requirement | Minimum version |
|---|---|
| Python | 3.11 |
| pip | 23.x |
| Git | 2.x |
| bash / WSL | any recent version |

---

## 1. Clone the repository

```bash
git clone https://github.com/mjlak1000/Cls_sauce.git cls-etsy-automation
cd cls-etsy-automation
```

---

## 2. Create and activate a virtual environment

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (WSL or PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

---

## 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` in your editor and fill in the required values:

| Variable | Description |
|---|---|
| `ETSY_API_KEY` | Your Etsy Open API v3 key |
| `ETSY_SHOP_ID` | Your Etsy shop ID |
| `SHIPPING_PROVIDER` | Carrier name (e.g. `usps`, `fedex`) |
| `SHIPPING_API_KEY` | Shipping provider API key |

All other variables have sensible defaults; see `.env.example` for details.

---

## 5. Verify the installation

Run the QA script to confirm every component is working:

```bash
bash run_qa.sh
```

Expected output:
```
============================================
 cls-etsy-automation — QA Runner
============================================

[1/3] Running schema validation...
      Schema validation passed.
[2/3] Validating SOP pipelines (dry-run)...
      → sop1_pipeline.py
      → sop2_pipeline.py
      → sop3_pipeline.py
      → sop4_sentiment_parser.py
      → sop5_lifecycle.py
      All pipelines validated.
[3/3] Syntax-checking all Python scripts...
      Syntax check passed.

============================================
 All QA checks passed. ✓
============================================
```

---

## 6. Start the scheduler (optional)

```bash
python scheduler.py
```

The scheduler will run each SOP pipeline at the intervals defined in your `.env` file.
Press `Ctrl+C` to stop.

---

## Troubleshooting

### `ModuleNotFoundError`
Make sure your virtual environment is activated and that you ran `pip install -r requirements.txt`.

### `EnvironmentError: ETSY_API_KEY is not set`
Copy `.env.example` to `.env` and fill in your Etsy API key.

### Python version error
Ensure you are running Python 3.11 or later:
```bash
python --version
```
