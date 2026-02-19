# src/msg_handler/schemas.py
from pydantic import BaseModel, Field, field_serializer
from typing import Any, Generic, TypeVar, Optional
from datetime import datetime, timedelta

"""
Payload definitions.
Note: Pydantic parses Union types by field matching (first match wins). 
BE CAREFUL WITH FIELD OVERLAPS! Consider using 'Discriminator' if payload types increase.
"""


class SensorPayload(BaseModel):
    """
    Payload for human detection sensor data.

    Attributes:
        isThereHuman: True if a human is detected.
        sensor_status: Operational status string.
        sensor_status_code: Numeric status code.
    """

    isThereHuman: bool
    sensor_status: str
    sensor_status_code: int
    # uptime : timedelta


class HeartBeatPayload(BaseModel):
    """
    Payload for device health status (heartbeat).

    Attributes:
        status: Device health status (e.g., 'Active').
        status_code: Numeric health code.
    """

    status: str
    status_code: int
    # uptime : timedelta


class SensorMessage(BaseModel):
    """
    Generic envelope for sensor telemetry.

    Attributes:
        sender_id: Unique device identifier.
        sender_name: Optional human-readable device name.
        timestamp: Event creation time.
        data_type: Discriminator for the payload type.
        payload: The actual data content (SensorPayload or HeartBeatPayload).

    Note:
        - When serialized to JSON, `timestamp` is formatted as 'YYYY-MM-DD HH:MM'.
        - [Important] The `payload` is validated against classes in T (first match wins).
          Ensure that the dictionary keys do not overlap significantly
          between these types to avoid incorrect type inference.
    """

    sender_id: str
    sender_name: str | None
    timestamp: datetime = Field(default_factory=datetime.now)
    data_type: str
    payload: SensorPayload | HeartBeatPayload
    sequence_no: int = 0

    @field_serializer("timestamp")
    def serialize_timestamp(self, dt: datetime, _info):
        return dt.strftime("%Y-%m-%d %H:%M")
