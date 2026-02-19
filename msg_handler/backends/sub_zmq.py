import zmq
import zmq.asyncio
from ..sub_base import BaseSubscriber, AsyncBaseSubscriber
from ..schemas import SensorMessage


class ZmqSubscriber(BaseSubscriber):
    """
    Synchronous ZeroMQ implementation of a subscriber.

    Attributes:
        endpoint: ZMQ endpoint string.
        is_bind: Whether to bind (True) or connect (False).
        topics: List of topic strings to filter.
    """

    def __init__(self, endpoint: str, is_bind=True, topics: list[str] | None = None):
        self.endpoint = endpoint
        self.topics = topics or [""]
        self.is_bind = is_bind
        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.SUB)
        self._running = True

    def connect(self):
        """Set up ZMQ socket and subscribe to topics."""
        if self.is_bind:
            self.socket.bind(self.endpoint)
        else:
            self.socket.connect(self.endpoint)

        for t in self.topics:
            self.socket.subscribe(t)

    def __iter__(self):
        """Blocking generator that yields parsed SensorMessages."""
        if self.socket.closed:
            self.connect()

        while self._running:
            try:
                json_str = self.socket.recv_string()
                yield SensorMessage.model_validate_json(json_str)
            except zmq.ZMQError:
                break
            except Exception as e:
                print(f"Error receiving message: {e}")
                continue

    def close(self):
        """Stop processing and terminate ZMQ context."""
        self._running = False
        self.socket.close()
        self.ctx.term()


class AsyncZmqSubscriber(AsyncBaseSubscriber):
    """
    Asynchronous ZeroMQ implementation of a subscriber.

    Attributes:
        endpoint: ZMQ endpoint string.
        is_bind: Whether to bind (True) or connect (False).
        topics: List of topic strings to filter.
    """

    def __init__(self, endpoint: str, is_bind=True, topics: list[str] | None = None):
        self.endpoint = endpoint
        self.is_bind = is_bind
        self.topics = topics or [""]
        self.ctx = zmq.asyncio.Context()
        self.socket = self.ctx.socket(zmq.SUB)
        self._running = True

    async def connect(self):
        """Set up async ZMQ socket and subscribe to topics."""
        if self.is_bind:
            self.socket.bind(self.endpoint)
        else:
            self.socket.connect(self.endpoint)
        for t in self.topics:
            self.socket.subscribe(t)

    async def __aiter__(self):
        """Async generator that yields parsed SensorMessages."""
        if self.socket.closed:
            await self.connect()

        while self._running:
            try:
                json_str = await self.socket.recv_string()
                yield SensorMessage.model_validate_json(json_str)
            except zmq.ZMQError:
                break
            except Exception as e:
                print(f"Async receive error: {e}")
                continue

    async def close(self):
        """Stop processing and terminate ZMQ context asynchronously."""
        self._running = False
        self.socket.close()
        self.ctx.term()
