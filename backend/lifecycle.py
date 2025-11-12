"""
Background job for request lifecycle management.

Design Decision:
- Runs periodically to check for timed out requests
- Can be triggered manually or run as cron job
- Logs all timeout events
"""

import asyncio
import logging
from datetime import datetime

from database import get_db
from services import HelpRequestService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_timeouts_job():
    """
    Background job to check and mark timed out requests.

    Design Decision:
    - Run every 5 minutes
    - Mark requests past timeout_at as TIMEOUT
    - Can be run manually or as scheduled task
    """
    logger.info("Starting timeout check job...")

    db = get_db()
    service = HelpRequestService(db)

    try:
        timed_out_ids = await service.check_timeouts()

        if timed_out_ids:
            logger.info(
                f"Marked {len(timed_out_ids)} requests as timed out: {timed_out_ids}"
            )
        else:
            logger.info("No timed out requests found")

        return timed_out_ids

    except Exception as e:
        logger.error(f"Error in timeout check job: {e}")
        raise


async def run_periodic_timeout_check(interval_minutes: int = 5):
    """
    Run timeout check periodically.

    Args:
        interval_minutes: How often to run the check
    """
    logger.info(f"Starting periodic timeout checker (interval: {interval_minutes} min)")

    while True:
        try:
            await check_timeouts_job()
        except Exception as e:
            logger.error(f"Error in periodic timeout check: {e}")

        # Wait for next interval
        await asyncio.sleep(interval_minutes * 60)


if __name__ == "__main__":
    # Run the periodic checker
    asyncio.run(run_periodic_timeout_check())
