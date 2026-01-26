import time
import board
import busio
import numpy as np
import cv2
import adafruit_mlx90640
import logging

# --- Logging Setup / ロガー設定 / 日志设置 ---
logger = logging.getLogger("ThermalCamera")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class ThermalCamera:
    def __init__(self):
        logger.info("Initializing MLX90640 Camera...")
        try:
            # EN: I2C Setup (800kHz for high speed)
            # JA: I2Cのセットアップ（高速化のため800kHzに設定）
            # ZH: I2C设置（设为800kHz以实现高速传输）
            i2c = busio.I2C(board.SCL, board.SDA, frequency=800000)
            self.mlx = adafruit_mlx90640.MLX90640(i2c)
            self.mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_8_HZ
            
            # EN: Data storage / JA: データ格納用 / ZH: 数据存储用
            self.frame = [0] * 768
            self.raw_data = None
            logger.info("Camera initialized successfully.")
            
        except Exception as e:
            logger.critical(f"Camera initialization FAILED: {e}")
            # EN: Re-raise exception as init failure is critical
            # JA: 初期化失敗は致命的なので例外を再送出
            # ZH: 初始化失败是致命的，重新抛出异常
            raise e 

    def get_frame(self):
        """
        EN: Data acquisition and image conversion
        JA: データ取得と画像変換を行う
        ZH: 数据获取与图像转换
        """
        try:
            # EN: Get frame data / JA: データを取得 / ZH: 获取帧数据
            self.mlx.getFrame(self.frame)
            
            # EN: Convert raw data to Numpy array
            # JA: 生データをNumpy配列化して保持
            # ZH: 将原始数据转换为Numpy数组并保存
            self.raw_data = np.array(self.frame)
            
            # --- Image Processing / 画像処理 / 图像处理 ---
            # EN: Reshape to 24x32 grid / JA: 24x32にリシェイプ / ZH: 重塑为24x32网格
            data_array = self.raw_data.reshape((24, 32))
            
            # EN: Normalize for visualization
            # JA: 可視化用に正規化
            # ZH: 归一化以用于可视化
            min_val, max_val = np.min(data_array), np.max(data_array)
            norm_data = (data_array - min_val) / (max_val - min_val)
            norm_data = (norm_data * 255).astype(np.uint8)
            
            # EN: Apply colormap (JET) / JA: カラーマップ（JET）を適用 / ZH: 应用伪彩色（JET）
            heatmap = cv2.applyColorMap(norm_data, cv2.COLORMAP_JET)
            
            # --- Resize for display / 表示用にリサイズ / 调整大小以便显示 ---
            # EN: Choose interpolation: INTER_NEAREST (pixelated) or INTER_CUBIC (smooth)
            # JA: 補完方法の選択: INTER_NEAREST（ピクセル感を残す）または INTER_CUBIC（滑らか）
            # ZH: 插值方式选择：INTER_NEAREST（保持像素感）或 INTER_CUBIC（平滑）
            
            # heatmap = cv2.resize(heatmap, (640, 480), interpolation=cv2.INTER_CUBIC)
            heatmap = cv2.resize(heatmap, (640, 480), interpolation=cv2.INTER_NEAREST)
            
            # EN: Encode to JPEG / JA: JPEGにエンコード / ZH: 编码为JPEG
            ret, jpeg = cv2.imencode('.jpg', heatmap)
            
            return jpeg.tobytes(), list(self.frame)
            
        except RuntimeError as e:
            # EN: Log as warning as I2C errors can occur frequently
            # JA: I2Cのエラーは頻発しうるため、Warningレベルで記録
            # ZH: I2C错误可能频繁发生，记为警告级别
            logger.warning(f"Sensor read error (RuntimeError): {e}")
            return None, None
        except Exception as e:
            logger.error(f"Unexpected error in get_frame: {e}")
            return None, None