from typing import Literal, Union
from pydantic import BaseModel
from .pub_base import BasePublisher
from .backends.pub_zmq import ZmqPublisher


class ZmqPubOptions(BaseModel):
    """
    Configuration options for ZeroMQ publisher.

    Attributes:
        backend_type: Fixed literal for ZMQ backend.
        endpoint: ZMQ connection string.
        is_connect: If True, uses 'connect'; if False, uses 'bind'.
    """

    backend_type: Literal["zmq"] = "zmq"
    endpoint: str = "tcp://localhost:5555"
    is_connect: bool = True


class MqttPubOptions(BaseModel):
    """
    Configuration options for MQTT publisher.

    Attributes:
        backend_type: Fixed literal for MQTT backend.
        broker_url: URL of the MQTT broker.
        port: Connection port.
    """

    backend_type: Literal["mqtt"] = "mqtt"
    broker_url: str
    port: int


PublisherOptions = Union[ZmqPubOptions, MqttPubOptions]


def get_publisher(options: PublisherOptions) -> BasePublisher:
    """
    Factory method to create a publisher instance.

    Args:
        options: Configuration object for the chosen backend.
    """
    if options.backend_type == "zmq":
        return ZmqPublisher(endpoint=options.endpoint, is_connect=options.is_connect)
    elif options.backend_type == "mqtt":
        raise NotImplementedError("MQTT backend is not implemented yet.")
    else:
        raise ValueError(f"Unknown backend type: {options.backend_type}")
