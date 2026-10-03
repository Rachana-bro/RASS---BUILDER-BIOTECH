"""
RASS-BUILDER: Standalone Background Worker Process
Can be run as an independent background daemon or container in decoupled deployments.

Usage:
    python backend/scripts/run_worker.py
"""

import sys
import time
import signal
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from database.schema import init_db
from database.repository import SqliteJobRepository
from jobs.worker import BackgroundJobWorker
from core.logger import logger


_running = True


def handle_shutdown(signum, frame):
    global _running
    logger.info("Received termination signal. Draining worker tasks...")
    _running = False


def main():
    global _running
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    init_db()
    repo = SqliteJobRepository()
    worker = BackgroundJobWorker(repo)

    # Recover any stale interrupted jobs from previous unclean shutdowns
    recovered = repo.recover_stale_running_jobs()
    if recovered:
        logger.warning(f"Standalone worker recovered {len(recovered)} interrupted jobs.")

    logger.info("[*] RASS-BUILDER standalone background worker started. Polling for queued analysis jobs...")

    while _running:
        try:
            queued_jobs = repo.get_queued_jobs(limit=5)
            if not queued_jobs:
                time.sleep(1.0)
                continue

            for job in queued_jobs:
                if not _running:
                    break
                logger.info(f"Processing queued analysis job: {job.job_id}")
                worker.process_job(job.job_id)

        except Exception as exc:
            logger.error(f"Error in standalone worker execution loop: {str(exc)}")
            time.sleep(2.0)

    logger.info("[+] RASS-BUILDER standalone worker stopped gracefully.")


if __name__ == "__main__":
    main()
