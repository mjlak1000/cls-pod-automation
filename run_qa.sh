#!/usr/bin/env bash
# run_qa.sh — Run the full QA suite for cls-etsy-automation
set -euo pipefail

echo "============================================"
echo " cls-etsy-automation — QA Runner"
echo "============================================"

# 1. Schema validation
echo ""
echo "[1/3] Running schema validation..."
python cls_schema_validator.py
echo "      Schema validation passed."

# 2. Run each SOP pipeline in dry-run / validate mode
echo ""
echo "[2/3] Validating SOP pipelines (dry-run)..."
for sop in sop1_pipeline.py sop2_pipeline.py sop3_pipeline.py sop4_sentiment_parser.py sop5_lifecycle.py; do
    echo "      → $sop"
    python "$sop" --dry-run
done
echo "      All pipelines validated."

# 3. Python syntax check on all scripts
echo ""
echo "[3/3] Syntax-checking all Python scripts..."
python -m py_compile cls_schema_validator.py \
    etsy_client.py \
    scheduler.py \
    sop1_pipeline.py \
    sop2_pipeline.py \
    sop3_pipeline.py \
    sop4_sentiment_parser.py \
    sop5_lifecycle.py \
    trend_harvester.py
echo "      Syntax check passed."

echo ""
echo "============================================"
echo " All QA checks passed. ✓"
echo "============================================"
