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

logger = logging.getLogger("cls_schema_validator")

# ---------------------------------------------------------------------------
# CLS schema definition
# (fields are derived from Master-Codebook-v1.0 — update here when the PDF
#  is revised)
# ---------------------------------------------------------------------------
CLS_SCHEMA = {
    "type": "object",
    "required": ["listing_id", "title", "price", "quantity", "status"],
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
    """Return a list of validation error messages for *record*."""
    errors: list[str] = []

    required = schema.get("required", [])
    for field in required:
        if field not in record:
            errors.append(f"Missing required field: '{field}'")

    props = schema.get("properties", {})
    for field, rules in props.items():
        if field not in record:
            continue
        value = record[field]
        expected_type = rules.get("type")
        if expected_type == "string" and not isinstance(value, str):
            errors.append(f"Field '{field}' must be a string, got {type(value).__name__}")
        elif expected_type == "number" and not isinstance(value, (int, float)):
            errors.append(f"Field '{field}' must be a number, got {type(value).__name__}")
        elif expected_type == "integer" and not isinstance(value, int):
            errors.append(f"Field '{field}' must be an integer, got {type(value).__name__}")
        elif expected_type == "array" and not isinstance(value, list):
            errors.append(f"Field '{field}' must be a list, got {type(value).__name__}")

        if isinstance(value, str):
            if "minLength" in rules and len(value) < rules["minLength"]:
                errors.append(
                    f"Field '{field}' is too short (min {rules['minLength']} chars)"
                )
            if "maxLength" in rules and len(value) > rules["maxLength"]:
                errors.append(
                    f"Field '{field}' is too long (max {rules['maxLength']} chars)"
                )
        if isinstance(value, (int, float)) and "minimum" in rules:
            if value < rules["minimum"]:
                errors.append(
                    f"Field '{field}' must be >= {rules['minimum']}, got {value}"
                )
        if isinstance(value, list) and "maxItems" in rules:
            if len(value) > rules["maxItems"]:
                errors.append(
                    f"Field '{field}' has too many items (max {rules['maxItems']})"
                )
        if "enum" in rules and value not in rules["enum"]:
            errors.append(
                f"Field '{field}' must be one of {rules['enum']}, got '{value}'"
            )

    return errors


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
