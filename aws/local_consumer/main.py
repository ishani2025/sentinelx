"""Run the local Security Hub SQS consumer and dispatcher."""

from __future__ import annotations

import logging
import signal
import sys
import threading

from config import AppConfig, ConfigError
from consumer import SQSConsumer
from dispatcher import Dispatcher
from logger import configure_logging
from priority_queue_manager import PriorityQueueManager

logger = logging.getLogger(__name__)


def main() -> int:
    """Start the local consumer and dispatcher processes."""
    configure_logging()

    try:
        config = AppConfig.from_env()
    except ConfigError as exc:
        logger.error("%s", exc)
        return 2

    queue_manager = PriorityQueueManager()
    dispatcher = Dispatcher(queue_manager)
    consumer = SQSConsumer(config, queue_manager)

    dispatcher_thread = threading.Thread(
        target=dispatcher.run_forever,
        name="dispatcher",
        daemon=True,
    )
    dispatcher_thread.start()

    def handle_shutdown(_signum: int, _frame: object) -> None:
        logger.info("Shutdown requested")
        dispatcher.stop()
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    try:
        consumer.run_forever()
    except KeyboardInterrupt:
        logger.info("Local consumer stopped")
        dispatcher.stop()
        dispatcher_thread.join(timeout=5)
        return 0


if __name__ == "__main__":
    sys.exit(main())

