# CLS — Closed Loop System

**v1.0 &nbsp;•&nbsp; Etsy Print-on-Demand Automation**

> A professional automation framework that runs your Etsy POD shop end-to-end — from niche research to order fulfillment — so you spend less time on repetitive tasks and more time on what matters.

---

## What Is the Closed Loop?

Most POD sellers work in disconnected pieces: list a product, wait for sales, react to problems. CLS closes that loop — every stage feeds data into the next, so the system continuously improves itself.

```
  Trends & Listings  ──▶  Orders  ──▶  Fulfillment
         ▲                                    │
         └────  Lifecycle Decisions  ◀──  Reviews
```

Five automated pipelines handle the full cycle. You set the rules; CLS executes them.

---

## Core Pipelines

| Script | SOP | What It Does |
|---|---|---|
| `sop1_pipeline.py` | SOP-1 | Creates and syncs Etsy listings from your product data |
| `sop2_pipeline.py` | SOP-2 | Polls Etsy for new orders and saves them locally |
| `sop3_pipeline.py` | SOP-3 | Submits orders to your shipping provider and posts tracking back to Etsy |
| `sop4_sentiment_parser.py` | SOP-4 | Scores customer reviews with sentiment analysis |
| `sop5_lifecycle.py` | SOP-5 | Audits listings — renews aging products, flags low stock, deactivates dead listings |

Run them individually on demand, or let `scheduler.py` fire them automatically on the intervals you configure.

---

## Design Principles

| Principle | What It Means in Practice |
|---|---|
| **Safety First** | Schema validation and `--dry-run` mode on every pipeline mean nothing goes live until it passes the gate. |
| **Truth Over Hope** | Every decision is backed by real data — sentiment scores, lifecycle metrics, inventory counts. |
| **Discipline Enables Scale** | Consistent SOPs and strict field definitions keep the system predictable as your catalogue grows. |
| **You Stay in Control** | No black boxes. Every pipeline is a readable Python script you can inspect, fork, and extend. |

---

## Quick Start

New to the command line? Start with [docs/installation-guide.md](docs/installation-guide.md) for a step-by-step walkthrough.

### 1. Clone & enter the repo

```bash
git clone https://github.com/mjlak1000/cls-pod-automation.git
cd cls-pod-automation
```

### 2. Create a virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure your environment

```bash
cp .env.example .env
# Open .env and fill in your Etsy API key, shop ID, and shipping credentials
```

Key variables:

| Variable | Description |
|---|---|
| `ETSY_API_KEY` | Your Etsy Open API v3 key |
| `ETSY_SHOP_ID` | Your Etsy shop ID |
| `SHIPPING_PROVIDER` | Carrier name (e.g. `usps`, `fedex`) |
| `SHIPPING_API_KEY` | Shipping provider API key |

### 4. Verify your setup

```bash
bash run_qa.sh
```

This runs schema validation, a dry-run of every pipeline, and a syntax check across all scripts. All checks should pass before you go live.

### 5. Run a pipeline

```bash
python sop1_pipeline.py --dry-run   # Preview what would be synced
python sop1_pipeline.py             # Run for real
```

Every script accepts `--dry-run` so you can always preview before committing.

### 6. Start the scheduler (optional)

```bash
python scheduler.py
```

The scheduler runs each SOP at the intervals defined in your `.env` (defaults: SOP-1 every 60 min, SOP-2 every 30 min, SOP-3 every 15 min, SOP-4 every 2 h, SOP-5 once daily). Press `Ctrl+C` to stop.

---

## Documentation

| Resource | Description |
|---|---|
| 📘 **[Master-Codebook-v1.0.pdf](Master-Codebook-v1.0.pdf)** | **Start here.** Full CLS field definitions, schema reference, and system architecture. |
| [Installation Guide](docs/installation-guide.md) | Detailed setup for macOS, Linux, and Windows (WSL) |
| [Command-Line Basics](docs/command-line-basics.md) | Flags, examples, and environment variable reference for every script |
| [Changelog](CHANGELOG.md) | Version history |

---

## Requirements

- Python **3.11+**
- pip 23+
- Git 2+
- Etsy Open API v3 credentials
- A shipping provider API key (for SOP-3)

---

## Project Structure

```
cls-pod-automation/
├── README.md
├── CHANGELOG.md
├── Master-Codebook-v1.0.pdf      ← main reference document
├── requirements.txt
├── .env.example                  ← copy to .env and fill in your keys
├── run_qa.sh                     ← run this first to verify your setup
├── scheduler.py                  ← runs all SOPs on a timer
├── cls_schema_validator.py       ← validates data files against CLS schema
├── sop1_pipeline.py
├── sop2_pipeline.py
├── sop3_pipeline.py
├── sop4_sentiment_parser.py
├── sop5_lifecycle.py
├── data/                         ← runtime data (gitignored)
└── docs/
    ├── installation-guide.md
    └── command-line-basics.md
```
