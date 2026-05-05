"""
cls_schema_validator.py
-----------------------
Validates CSV/JSON data files in the data/ directory against the CLS schema
defined in Master-Codebook-v1.0.pdf.

Usage:
    python cls_schema_validator.py [--data-dir data]

Exit codes:
    0 — all files valid (or no files found)
    1 — one or more validation errors detected
"""

import argparse
import json
import logging
import os
import sys

import jsonschema

logger = logging.getLogger("cls_schema_validator")

# ---------------------------------------------------------------------------
# CLS schema definition
# (fields are derived from Master-Codebook-v1.0 — update here when the PDF
#  is revised)
# NOTE: listing_id is intentionally NOT required; its absence signals a new
#       listing to be created (present = UPDATE, absent = CREATE).
# ---------------------------------------------------------------------------
CLS_SCHEMA = {
    "type": "object",
    "required": ["title", "price", "quantity", "status"],
    "properties": {
        "listing_id": {"type": "string"},
        "title": {"type": "string", "minLength": 1, "maxLength": 140},
        "description": {"type": "string"},
        "price": {"type": "number", "minimum": 0.01},
        "quantity": {"type": "integer", "minimum": 0},
        "status": {"type": "string", "enum": ["active", "inactive", "draft", "sold_out"]},
        "tags": {"type": "array", "items": {"type": "string"}, "maxItems": 13},
        "sku": {"type": "string"},
    },
    "additionalProperties": True,
}


def validate_record(record: dict, schema: dict) -> list[str]:
    """Return a list of validation error messages for *record* using jsonschema."""
    validator = jsonschema.Draft7Validator(schema)
    return [error.message for error in sorted(validator.iter_errors(record), key=str)]


def validate_file(filepath: str) -> list[str]:
    """Validate a JSON file and return a list of error strings."""
    all_errors: list[str] = []
    try:
        with open(filepath, encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        return [f"JSON parse error: {exc}"]

    records = data if isinstance(data, list) else [data]
    for idx, record in enumerate(records):
        errors = validate_record(record, CLS_SCHEMA)
        for err in errors:
            all_errors.append(f"Record {idx}: {err}")

    return all_errors


def main(data_dir: str = "data") -> int:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )

    json_files = [
        os.path.join(data_dir, f)
        for f in os.listdir(data_dir)
        if f.endswith(".json")
    ] if os.path.isdir(data_dir) else []

    if not json_files:
        logger.info("No JSON files found in '%s' — nothing to validate.", data_dir)
        return 0

    total_errors = 0
    for filepath in json_files:
        errors = validate_file(filepath)
        if errors:
            logger.error("Validation FAILED for %s:", filepath)
            for err in errors:
                logger.error("  %s", err)
            total_errors += len(errors)
        else:
            logger.info("Validation passed: %s", filepath)

    if total_errors:
        logger.error("%d validation error(s) found.", total_errors)
        return 1

    logger.info("All files validated successfully.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate CLS data files")
    parser.add_argument(
        "--data-dir",
        default=os.getenv("DATA_DIR", "data"),
        help="Directory containing data files (default: data)",
    )
    args = parser.parse_args()
    sys.exit(main(args.data_dir))
