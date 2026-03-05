'''
This file setups the basic configurations for logging in the application.'''
import logging
import os
from logging import Logger
def setup_logging()-> Logger:
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)