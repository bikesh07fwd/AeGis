import sys
import logging
import google.cloud.logging
from config.settings import settings

def setup_logging():
    # Setup standard python logging outputting to stdout for Cloud Run / local
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    
    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

setup_logging()
logger = logging.getLogger("AegisAI")