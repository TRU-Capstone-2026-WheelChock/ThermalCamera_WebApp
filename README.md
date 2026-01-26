# ThermalCamera_WebApp
thermal camera system with fast api &amp; mlx 90640

MLX90640 Thermal Data Collector
A FastAPI-based web application to stream real-time thermal images from an MLX90640 sensor and save raw temperature data to CSV files with a single click.

# What is this?
This project turns a Raspberry Pi (or similar I2C-capable device) into a Thermal Camera Web Server.

Real-time Streaming: View a colorized thermal heatmap in your browser.

Data Collection: Capture the raw 24x32 (768 pixels) temperature values and save them as labeled CSV files for datasets.

Hardware: Designed for the MLX90640 Far-Infrared thermal sensor array.

# How to use this
1. Prerequisites
    Ensure your hardware is connected via I2C and you have Python installed.

    Enable I2C on your device (e.g., sudo raspi-config on Raspberry Pi).

    Install the required system libraries for OpenCV (if necessary).

2. Installation
    Install the dependencies using the provided requirements.txt:

    ```Bash
    pip install -r requirements.txt
    ```

    if failed consider install following
    ```Bash
    sudo apt install liblgpio-dev
    sudo apt install swig
    ```

3. Running the Server
    Start the application by running main.py:

    ```Bash
    python main.py
    ```

    The server will start at http://0.0.0.0:8000.

4. Operations
Open the Web UI: Navigate to http://<your-ip>:8000 in your browser.

View Feed: You will see a live heatmap resized for better visibility.

## Save Data:

Enter a label (e.g., "person", "empty", "hot_cup") in the input field.

Click the Save button.

The raw temperature data will be saved in the /dataset folder as a .csv file named with the label and a timestamp.

# Project Structure
main.py: FastAPI web server and data saving logic.

camera.py: Hardware interface for the MLX90640 and image processing.

templates/index.html: The frontend user interface.

dataset/: (Auto-generated) Stores your captured thermal CSV files.\

# Hardware Connnection

Connect the MLX90640 sensor to the Raspberry Pi 4 or 5 using the following GPIO pins:
| MLX90640 Pin | Raspberry Pi Pin (GPIO) | Pin Number |
| :--- | :--- | :--- |
| **VCC** | 3.3V Power | Pin 1 |
| **GND** | Ground | Pin 6 (or 9, 14, 20, 25) |
| **SDA** | SDA (I2C Data) | Pin 3 (GPIO 2) |
| **SCL** | SCL (I2C Clock) | Pin 5 (GPIO 3) |

# Note
This is AI gen readme. there might be a wrong comments. if you encounter trouble, let me (Keishi) know.

# Troubleshooting
 - Raspberry 4 and 5 has different I2C capability. if it does not work as intended, consider changing following part in camera.py
    ```
    i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
    self.mlx = adafruit_mlx90640.MLX90640(i2c)
    self.mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_4_HZ
    ```