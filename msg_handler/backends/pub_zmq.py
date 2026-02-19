import zmq
import logging
from ..pub_base import BasePublisher
from ..schemas import SensorMessage

logger = logging.getLogger(__name__)


class ZmqPublisher(BasePublisher):
    """
    ZeroMQ implementation of a publisher.

    Attributes:
        endpoint: ZMQ connection string.
        is_connect: If True, performs 'connect'. If False, performs 'bind'.
    """

    def __init__(self, endpoint: str = "tcp://localhost:5555", is_connect: bool = True):
        super().__init__()
        self.endpoint = endpoint
        self.is_connect = is_connect
        self.ctx = None
        self.socket = None

    def _connect_impl(self):
        """Internal logic to establish the ZMQ PUB socket connection."""
        if self.socket:
            logger.warning(f"Already connected to {self.endpoint}")
            return

        logger.info(f"Connecting to ZMQ endpoint: {self.endpoint}")
        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.PUB)

        try:
            if self.is_connect:
                self.socket.connect(self.endpoint)
                logger.info(f"ZMQ Socket connected successfully to {self.endpoint}")
            else:
                self.socket.bind(self.endpoint)
                logger.info(f"ZMQ Socket bound successfully to {self.endpoint}")
        except zmq.ZMQError as e:
            self.socket.close()
            raise ConnectionError(f"Failed to setup ZMQ on {self.endpoint}: {e}")

    def send_raw(self, data: str):
        """
        Sends a raw string message via ZMQ.

        Note:
            Requires the socket to be connected via connect() first.
        """
        if not isinstance(data, str):
            raise TypeError(f"Payload must be str! Received: {type(data)}")

        if not self.socket:
            logger.error("Attempted to send data but socket is not connected.")
            raise ConnectionError("Not connected. Call connect() first.")
        self.socket.send_string(data)

    def close(self):
        """Close the ZMQ socket and terminate the context."""
        if self.socket:
            self.socket.close()
            self.socket = None
        if self.ctx:
            self.ctx.term()
            self.ctx = None
