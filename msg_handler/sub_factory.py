import os
from typing import Literal, Union, List
from pydantic import BaseModel, Field
from .sub_base import BaseSubscriber, AsyncBaseSubscriber
from .backends.sub_zmq import ZmqSubscriber, AsyncZmqSubscriber

BACKEND_TYPE = os.getenv("MSG_BACKEND", "zmq")


class ZmqSubOptions(BaseModel):
    """
    Configuration options for ZeroMQ subscriber.

    Attributes:
        backend_type: Fixed literal for ZMQ backend.
        endpoint: ZMQ connection string (e.g., tcp://localhost:5555).
        topics: List of topics to subscribe to.
        is_bind: Whether to bind or connect to the endpoint.
    """

    backend_type: Literal["zmq"] = "zmq"
    endpoint: str = "tcp://localhost:5555"
    topics: List[str] = Field(default_factory=lambda: [""])
    is_bind: bool = True


class MqttSubOptions(BaseModel):
    """
    Configuration options for MQTT subscriber.

    Attributes:
        backend_type: Fixed literal for MQTT backend.
        broker_url: URL of the MQTT broker.
        port: Connection port.
        topics: List of MQTT topics to subscribe to.
    """

    backend_type: Literal["mqtt"] = "mqtt"
    broker_url: str
    port: int = 1883
    topics: List[str] = Field(default_factory=list)


SubscriberOptions = Union[ZmqSubOptions, MqttSubOptions]


def get_subscriber(options: SubscriberOptions) -> BaseSubscriber:
    """
    Factory method to create a synchronous subscriber.

    Args:
        options: Configuration object for the chosen backend.
    """
    if options.backend_type == "zmq":
        return ZmqSubscriber(
            endpoint=options.endpoint, topics=options.topics, is_bind=options.is_bind
        )
    elif options.backend_type == "mqtt":
        raise NotImplementedError("MQTT backend is not implemented yet.")
    else:
        raise ValueError(f"Unknown backend type: {options.backend_type}")


def get_async_subscriber(options: SubscriberOptions) -> AsyncBaseSubscriber:
    """
    Factory method to create an asynchronous subscriber.

    Args:
        options: Configuration object for the chosen backend.
    """
    if options.backend_type == "zmq":
        return AsyncZmqSubscriber(
            endpoint=options.endpoint, topics=options.topics, is_bind=options.is_bind
        )
    elif options.backend_type == "mqtt":
        raise NotImplementedError("MQTT backend is not implemented yet.")
    else:
        raise ValueError(f"Unknown backend type: {options.backend_type}")
