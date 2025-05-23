import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_logger() -> logging.Logger:
    return logging.getLogger()
