# cls-etsy-automation

**Print-on-demand Etsy automation suite** — a collection of SOP-driven pipelines, validators, and schedulers for managing listings, orders, fulfillment, and product lifecycle on Etsy.

---

## Project Structure

```
cls-etsy-automation/
├── README.md
├── CHANGELOG.md
├── Master-Codebook-v1.0.pdf
├── requirements.txt
├── .env.example
├── run_qa.sh
├── scheduler.py
├── cls_schema_validator.py
├── sop1_pipeline.py
├── sop2_pipeline.py
├── sop3_pipeline.py
├── sop4_sentiment_parser.py
├── sop5_lifecycle.py
├── data/                  ← (empty, gitignored)
├── docs/
│   ├── command-line-basics.md
│   └── installation-guide.md
└── .gitignore
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in your API keys and settings
```

### 3. Run the QA check

```bash
bash run_qa.sh
```

### 4. Run a pipeline manually

```bash
python sop1_pipeline.py
python sop2_pipeline.py
python sop3_pipeline.py
python sop4_sentiment_parser.py
python sop5_lifecycle.py
```

### 5. Start the scheduler

```bash
python scheduler.py
```

---

## SOPs Overview

| Script | SOP | Description |
|---|---|---|
| `sop1_pipeline.py` | SOP-1 | Listing creation & product sync |
| `sop2_pipeline.py` | SOP-2 | Order intake & processing |
| `sop3_pipeline.py` | SOP-3 | Fulfillment & shipping dispatch |
| `sop4_sentiment_parser.py` | SOP-4 | Customer review sentiment analysis |
| `sop5_lifecycle.py` | SOP-5 | Product lifecycle & inventory management |

---

## Validation

```bash
python cls_schema_validator.py
```

Validates all data files in `data/` against the CLS schema defined in `Master-Codebook-v1.0.pdf`.

---

## Documentation

- [Installation Guide](docs/installation-guide.md)
- [Command-Line Basics](docs/command-line-basics.md)

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.
