"""
Dedicated entry point for running the background Cron worker in production.
Ensures only one instance of the Cron service is running across the system.
"""
import time
import logging
from app import create_app

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("cron-worker")

def run_cron():
    logger.info("Starting dedicated EnpiAI Cron Worker...")
    # create_app with start_services=True will start the background thread
    app = create_app(start_services=True)
    
    # Keep the main process alive while the background thread works
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Cron Worker stopping...")

if __name__ == "__main__":
    run_cron()
