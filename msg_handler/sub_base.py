from abc import ABC, abstractmethod
from typing import Iterator, AsyncIterator
from .schemas import SensorMessage


class BaseSubscriber(ABC):
    """
    Abstract base class for synchronous subscribers.

    Note:
        Implements the context manager protocol to ensure connection cleanup.
    """

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @abstractmethod
    def connect(self):
        """Initialize the connection."""
        pass

    @abstractmethod
    def __iter__(self) -> Iterator[SensorMessage]:
        """Iterate over received messages."""
        pass

    @abstractmethod
    def close(self):
        """Close the connection and release resources."""
        pass


class AsyncBaseSubscriber(ABC):
    """
    Abstract base class for asynchronous subscribers.
    """

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    @abstractmethod
    async def connect(self):
        """Initialize the connection asynchronously."""
        pass

    @abstractmethod
    def __aiter__(self) -> AsyncIterator[SensorMessage]:
        """Iterate over received messages using async for."""
        pass

    @abstractmethod
    async def close(self):
        """Close the connection asynchronously."""
        pass
