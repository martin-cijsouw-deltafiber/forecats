import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

LOG_FILE = Path("./logs/forecats_app.log")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def setup_logging() -> None:
    log_file = Path("./logs/forecats_app.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    handler = TimedRotatingFileHandler(
        LOG_FILE,
        when="midnight",  # Rotate at midnight
        interval=1,  # Every 1 day
        backupCount=7,  # Keep 7 days of logs
    )
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

    # Set up logging
    logging.basicConfig(level=logging.WARNING, handlers=[handler])
    logging.getLogger("forecats").setLevel(logging.DEBUG)
