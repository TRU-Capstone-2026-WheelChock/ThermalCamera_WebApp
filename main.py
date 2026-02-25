import os
import time
import signal
import logging
from datetime import datetime

from Img_predictor import Img_predictor
from thermal_publisher import ThermalPublisher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('thermal_service.log')
    ]
)
logger = logging.getLogger("ThermalMain")

should_exit = False

def signal_handler(signum, frame):
    global should_exit
    logger.info(f"Received signal {signum}, shutting down...")
    should_exit = True

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


class ThermalService:
    def __init__(self):
        self.publish_interval = float(os.getenv("PUBLISH_INTERVAL", "2.0"))
        # self.heartbeat_interval = int(os.getenv("HEARTBEAT_INTERVAL", "30"))
        self.mock_mode = os.getenv("MOCK_MODE", "false").lower() == "true"

        self.camera = None
        self.publisher = None

        self.frame_count = 0
        self.start_time = None

        logger.info("=" * 50)
        logger.info("Thermal Service Started")
        logger.info(f"Publish Interval: {self.publish_interval}s")
        # logger.info(f"Heartbeat Interval: {self.heartbeat_interval}s")
        logger.info(f"Mock Mode: {self.mock_mode}")
        logger.info("=" * 50)

    def init_camera(self):
        try:
            if self.mock_mode:
                logger.info("Running in mock mode")
                self.camera = Img_predictor()
            else:
                self.camera = Img_predictor()
            logger.info("Camera initialized")
            return True
        except Exception as e:
            logger.error(f"Camera init failed: {e}")
            if not self.mock_mode:
                logger.warning("Falling back to mock mode")
                self.mock_mode = True
                return self.init_camera()
            return False

    def init_publisher(self):
        self.publisher = ThermalPublisher()
        try:
            self.publisher.connect()
            return True
        except Exception as e:
            logger.error(f"Publisher connect failed: {e}")
            return False

    def capture_and_send(self):
        try:
            frame_bytes, raw_data = self.camera.camera()
            if frame_bytes is None:
                logger.warning("Capture failed")
                return False

            prediction = None
            try:
                if hasattr(self.camera, 'predict_from_camera'):
                    prediction = self.camera.predict_from_camera()
                    if hasattr(prediction, 'item'):
                        prediction = prediction.item()
            except Exception as e:
                logger.error(f"Prediction error: {e}")

            metadata = {
                "device_id": self.publisher.device_id,
                "device_name": self.publisher.device_name,
                "timestamp": datetime.now().isoformat(),
                "frame_number": self.frame_count,
                "prediction": prediction,
                "has_human": bool(prediction) if prediction is not None else False
            }

            self.publisher.send_image_frame(frame_bytes, metadata)

            self.publisher.send_prediction(prediction, metadata)

            self.frame_count += 1
            if self.frame_count % 10 == 0:
                logger.info(f"Sent {self.frame_count} frames")
            return True

        except Exception as e:
            logger.error(f"Error in capture_and_send: {e}")
            return False

    def run(self):
        if not self.init_camera():
            logger.critical("Camera init failed, exiting")
            return

        if not self.init_publisher():
            logger.critical("Publisher init failed, exiting")
            return

        self.start_time = time.time()
        # last_heartbeat = time.time()

        try:
            while not should_exit:
                loop_start = time.time()

                self.capture_and_send()

                now = time.time()
                if now - last_heartbeat >= self.heartbeat_interval:
                    self.publisher.send_heartbeat()
                    last_heartbeat = now

                elapsed = time.time() - loop_start
                sleep_time = max(0, self.publish_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    logger.warning(f"Processing took {elapsed:.3f}s > interval {self.publish_interval}s")

        except KeyboardInterrupt:
            logger.info("Interrupted")
        finally:
            self.cleanup()

    def cleanup(self):
        logger.info("Cleaning up...")
        if self.publisher:
            self.publisher.close()
        if hasattr(self.camera, 'close'):
            self.camera.close()
        elif hasattr(self.camera, 'release'):
            self.camera.release()
        elapsed = time.time() - self.start_time if self.start_time else 0
        logger.info(f"Stopped. Frames sent: {self.frame_count}, uptime: {elapsed:.1f}s")

if __name__ == "__main__":
    service = ThermalService()
    service.run()