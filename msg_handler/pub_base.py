# src/msg_handler/base.py
import logging
from abc import ABC, abstractmethod
from .schemas import SensorMessage

logger = logging.getLogger(__name__)


class BasePublisher(ABC):
    """Interface for sending data"""

    def __init__(self):
        self._seq_no = 0

    def __enter__(self):
        self._connect_impl()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def connect(self):
        """
        [Deprecated] This is for Manual connection.
        Please use 'with' statement for automatic resource management.
        """
        logger.warning(
            "⚠️ Direct call to connect() is deprecated. "
            "Use 'with Publisher(...) as pub:' context manager."
        )
        self._connect_impl()

    @abstractmethod
    def _connect_impl(self):
        """Actual connection logic to be implemented by subclasses."""
        pass

    def send(self, msg: SensorMessage):
        """Send a validated SensorMessage. Recommended for most use cases.

        Args:
            msg (SensorMessage): The validated message object to be sent.
        """
        try:
            msg.sequence_no = self._seq_no
            self._seq_no += 1
            logger.debug(f"Publishing msg {msg.sequence_no} (type: {msg.data_type})")
            logger.debug(f"content is {msg.model_dump_json()}")

            self.send_raw(msg.model_dump_json())
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise

    @abstractmethod
    def send_raw(self, data: str):
        """Send a raw string directly. Useful for testing, debugging, or
            sending custom payloads that don't follow the standard schema.

        Args:
            data (str): The raw string to be transmitted.

        Note:
            This is for testing purpose. Notify to team member if you use this for actual code.
        """
        pass

    @abstractmethod
    def close(self):
        """Closing connection completely."""
        pass
