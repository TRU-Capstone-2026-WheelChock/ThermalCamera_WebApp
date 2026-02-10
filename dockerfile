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
    && rm -rf /var/lib/apt/lists/*

COPY requirements2.txt .

RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir -r requirements2.txt

COPY . .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYECODE=1

EXPOSE 8000

CMD ["python3","main.py"]

