import os
import json
import logging
import zmq
from datetime import datetime
from msg_handler import get_publisher,ZmqPubOptions,SensorMessage,SensorPayload,HeartBeatPayload

logger = logging.getLogger(__name__)

class ThermalPublisher:
    def __init__(self, config: dict = None):
        self.control_endpoint = config.get('control_endpoint') if config else \
            os.getenv("ZMQ_CONTROL_ENDPOINT", "tcp://camera-server:5555")
        self.image_endpoint = config.get('image_endpoint') if config else \
            os.getenv("ZMQ_IMAGE_ENDPOINT", "tcp://camera-server:5556")
        self.device_id = config.get('device_id') if config else \
            os.getenv("THERMAL_DEVICE_ID", "thermal_camera_001")
        self.device_name = config.get('device_name') if config else \
            os.getenv("THERMAL_DEVICE_NAME", "Thermal Camera")

        self.control_pub = None
        self.image_context = None
        self.image_pub = None
        self.sequence_no = 0

        logger.info(f"ThermalPublisher initialized: control={self.control_endpoint}, "
                    f"image={self.image_endpoint}")

    def connect(self):
        try:
            options = ZmqPubOptions(
                endpoint=self.control_endpoint,
                is_connect=True
            )
            self.control_pub = get_publisher(options)
            if hasattr(self.control_pub, '_connect_impl'):
                self.control_pub._connect_impl()
            elif hasattr(self.control_pub, 'connect'):
                self.control_pub.connect()
            logger.info(f"Control publisher connected to {self.control_endpoint}")
        except Exception as e:
            logger.error(f"Failed to connect control publisher: {e}")
            raise

        try:
            self.image_context = zmq.Context()
            self.image_pub = self.image_context.socket(zmq.PUB)
            self.image_pub.connect(self.image_endpoint)
            logger.info(f"Image publisher connected to {self.image_endpoint}")
        except Exception as e:
            logger.error(f"Failed to connect image publisher: {e}")
            if self.control_pub:
                self.control_pub.close()
            raise

    def close(self):
        logger.info("Closing publishers...")
        if self.control_pub:
            try:
                self.control_pub.close()
            except Exception as e:
                logger.error(f"Error closing control publisher: {e}")
        if self.image_pub:
            try:
                self.image_pub.close()
            except Exception as e:
                logger.error(f"Error closing image publisher: {e}")
        if self.image_context:
            self.image_context.term()
        logger.info("Publishers closed")

    def send_heartbeat(self):
        try:
            payload = HeartBeatPayload(
                status="active",
                status_code=200
            )
            msg = SensorMessage(
                sender_id=self.device_id,
                sender_name=self.device_name,
                timestamp=datetime.now(),
                data_type="heartbeat",
                payload=payload,
                sequence_no=self.sequence_no
            )
            self.sequence_no += 1
            self.control_pub.send(msg)
            logger.debug("Heartbeat sent")
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")

    def send_prediction(self, prediction, metadata: dict = None):
        try:
            has_human = bool(prediction) if prediction is not None else False
            payload = SensorPayload(
                isThereHuman=has_human,
                sensor_status="OK",
                sensor_status_code=200
            )
            msg = SensorMessage(
                sender_id=self.device_id,
                sender_name=self.device_name,
                timestamp=datetime.now(),
                data_type="thermal_prediction",
                payload=payload,
                sequence_no=self.sequence_no
            )
            self.sequence_no += 1
            self.control_pub.send(msg)
            logger.info(f"Prediction sent: human={has_human}")
        except Exception as e:
            logger.error(f"Failed to send prediction: {e}")

    def send_image_frame(self, frame_bytes: bytes, metadata: dict):
        try:
            self.image_pub.send_multipart([
                b"image_frame",
                json.dumps(metadata).encode('utf-8'),
                frame_bytes
            ])
        except Exception as e:
            logger.error(f"Failed to send image frame: {e}")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()