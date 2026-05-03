# Changelog

All notable changes to **cls-etsy-automation** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-05-03

### Added
- Initial project scaffold with full SOP pipeline suite
- `sop1_pipeline.py` — Listing creation & product sync (SOP-1)
- `sop2_pipeline.py` — Order intake & processing (SOP-2)
- `sop3_pipeline.py` — Fulfillment & shipping dispatch (SOP-3)
- `sop4_sentiment_parser.py` — Customer review sentiment analysis (SOP-4)
- `sop5_lifecycle.py` — Product lifecycle & inventory management (SOP-5)
- `cls_schema_validator.py` — CLS schema validation for all data files
- `scheduler.py` — Cron-style scheduler wiring all SOPs
- `run_qa.sh` — Shell script for running the full QA suite
- `requirements.txt` — Python dependency manifest
- `.env.example` — Environment variable template
- `data/` directory (gitignored) for runtime data files
- `docs/installation-guide.md` — Step-by-step installation guide
- `docs/command-line-basics.md` — CLI reference for all scripts
- `Master-Codebook-v1.0.pdf` — CLS field definitions and schema reference
