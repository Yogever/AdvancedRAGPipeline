import logging

_NOISY_LOGGERS = [
    "pymongo",
    "celery",
    "celery.app.trace",
    "celery.worker",
    "kombu",
    "qdrant_client",
    "httpx",
    "httpcore",
    "urllib3",
]

_FORMAT = "%(asctime)s %(levelname)-8s %(name)s — %(message)s"
_DATE_FORMAT = "%H:%M:%S"


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format=_FORMAT, datefmt=_DATE_FORMAT)
    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.ERROR)
