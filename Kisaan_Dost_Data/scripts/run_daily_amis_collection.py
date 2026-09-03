"""Automated Daily AMIS Punjab Market Price Collection Runner.

Can be scheduled via Windows Task Scheduler or cron (1-2 runs daily).
Executes a single collection pass across allowlisted commodities, validates output,
records manifest audit trail, and safely reports run health.
"""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    logger.info("=== Starting Scheduled Daily AMIS Punjab Collection ===")

    collector_path = SCRIPTS_DIR / "11_collect_amis_prices.py"
    if not collector_path.exists():
        logger.error(f"Collector script not found: {collector_path}")
        return 1

    spec = importlib.util.spec_from_file_location("collector_mod", collector_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    try:
        res = mod.run_collection()
        logger.info(f"Collection finished: {res['total_records']} records collected across {res['total_requests']} requests.")

        validator_path = SCRIPTS_DIR / "12_validate_amis_market_prices.py"
        v_spec = importlib.util.spec_from_file_location("validator_mod", validator_path)
        v_mod = importlib.util.module_from_spec(v_spec)
        v_spec.loader.exec_module(v_mod)

        valid = v_mod.run_full_validation()
        if not valid:
            logger.error("Dataset validation failed after collection run.")
            return 1

        logger.info("=== Daily AMIS Collection Run Completed Successfully ===")
        return 0

    except Exception as exc:
        logger.error(f"Fatal error during scheduled AMIS collection: {exc}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
