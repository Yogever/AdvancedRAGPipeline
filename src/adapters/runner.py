import logging
import signal
import time

from adapters.base import BaseAdapter

logger = logging.getLogger(__name__)


class AdapterRunner:
    """
    Owns the lifecycle of any BaseAdapter: start, block the main thread,
    and stop cleanly on SIGTERM or SIGINT.
    """

    def __init__(self, adapter: BaseAdapter):
        self._adapter = adapter
        self._running = False

    def run(self) -> None:
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        logger.info("Starting adapter: %s", type(self._adapter).__name__)
        self._adapter.start()
        self._running = True

        try:
            while self._running:
                time.sleep(1)
        finally:
            logger.info("Stopping adapter: %s", type(self._adapter).__name__)
            self._adapter.stop()
            logger.info("Adapter stopped.")

    def _handle_signal(self, signum: int, frame) -> None:
        logger.info("Received signal %d — shutting down.", signum)
        self._running = False
