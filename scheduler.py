"""
scheduler.py
------------
Cron-style scheduler that runs each SOP pipeline on a configurable interval.

Usage:
    python scheduler.py

Environment variables (see .env.example):
    SOP1_INTERVAL_MINUTES  (default: 60)
    SOP2_INTERVAL_MINUTES  (default: 30)
    SOP3_INTERVAL_MINUTES  (default: 15)
    SOP4_INTERVAL_MINUTES  (default: 120)
    SOP5_INTERVAL_MINUTES  (default: 1440)
"""

import logging
import os
import time

import schedule
from dotenv import load_dotenv

import sop1_pipeline
import sop2_pipeline
import sop3_pipeline
import sop4_sentiment_parser
import sop5_lifecycle

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("scheduler")


def _interval(env_var: str, default: int) -> int:
    """Read an integer interval from the environment, falling back to *default*."""
    try:
        return int(os.getenv(env_var, default))
    except ValueError:
        logger.warning("Invalid value for %s; using default %d", env_var, default)
        return default


def main() -> None:
    dry_run = os.getenv("DRY_RUN", "").lower() in ("1", "true")

    sop1_min = _interval("SOP1_INTERVAL_MINUTES", 60)
    sop2_min = _interval("SOP2_INTERVAL_MINUTES", 30)
    sop3_min = _interval("SOP3_INTERVAL_MINUTES", 15)
    sop4_min = _interval("SOP4_INTERVAL_MINUTES", 120)
    sop5_min = _interval("SOP5_INTERVAL_MINUTES", 1440)

    schedule.every(sop1_min).minutes.do(sop1_pipeline.run, dry_run=dry_run)
    schedule.every(sop2_min).minutes.do(sop2_pipeline.run, dry_run=dry_run)
    schedule.every(sop3_min).minutes.do(sop3_pipeline.run, dry_run=dry_run)
    schedule.every(sop4_min).minutes.do(sop4_sentiment_parser.run, dry_run=dry_run)
    schedule.every(sop5_min).minutes.do(sop5_lifecycle.run, dry_run=dry_run)

    logger.info(
        "Scheduler started — SOP1:%dm SOP2:%dm SOP3:%dm SOP4:%dm SOP5:%dm dry_run=%s",
        sop1_min,
        sop2_min,
        sop3_min,
        sop4_min,
        sop5_min,
        dry_run,
    )

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
