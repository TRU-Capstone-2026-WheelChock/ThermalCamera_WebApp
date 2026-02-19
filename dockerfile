FROM python:3.11.2-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3-pip \
    i2c-tools \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    pkg-config \
    libzmq3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements2.txt .

RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir -r requirements2.txt

COPY . .

RUN mkdir -p /app/logs

ENV ZMQ_ZMQ_ENDPOINT="tcp://camera-server:5555" \
    THERMAL_DEVICE_ID="thermal_camera_001" \
    THERMAL_DEVICE_NAME="Thermal Imaging Camera" \
    PUBLISH_INTERVAL="1.0" \
    HEARTBEAT_INTERVAL="30" \
    MOCK_MODE="false" \
    LOG_LEVEL="INFO" \

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD python -c "import zmq; ctx=zmq.Context(); s=ctx.socket(zmq.REQ); s.setsockopt(zmq.LINGER,0); s.connect('$ZMQ_ENDPOINT'); s.send_string('PING'); s.close(); ctx.term()" || exit 1

CMD ["python3","main.py"]

