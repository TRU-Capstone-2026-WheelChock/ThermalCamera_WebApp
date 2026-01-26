from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import csv
import os
import time
import datetime
import logging
from camera import ThermalCamera
from contextlib import asynccontextmanager

# --- Logging Setup / ロガー設定 / 日志设置 ---
logger = logging.getLogger("FastAPI_Server")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # EN: Shutdown process / JA: サーバー停止時に実行される処理 / ZH: 服务器关闭时的处理
    print("Shutting down camera...")
    # EN: Force terminate process / JA: 強制的にプロセスを終了 / ZH: 强制终止进程
    os._exit(0)

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

# --- Camera Initialization / カメラ初期化 / 摄像头初始化 ---
try:
    camera = ThermalCamera()
except Exception as e:
    logger.critical("Failed to start camera. Exiting.")
    exit(1)

latest_raw_data = None

# --- Directory setup / 保存先フォルダ設定 / 设置保存目录 ---
DATA_DIR = 'dataset'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    logger.info(f"Created data directory: {DATA_DIR}")

# --- CSV Header / CSVヘッダー / CSV表头 ---
HEADER = ['timestamp', 'label'] + [f'pix_{i}' for i in range(768)]

def gen_frames():
    global latest_raw_data
    while True:
        frame_bytes, raw_data = camera.get_frame()
        if frame_bytes:
            latest_raw_data = raw_data
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            time.sleep(0.1)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(gen_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

# --- Save individual file / 個別ファイル保存 / 保存独立文件 ---
@app.post("/save")
async def save_data(request: Request, background_tasks: BackgroundTasks):
    global latest_raw_data
    
    body = await request.json()
    label = body.get("label", "unknown")
    
    if latest_raw_data is None:
        return JSONResponse(status_code=500, content={"message": "No data available"})
    
    try:
        data_to_save = list(latest_raw_data)
        
        # EN: Get current time / JA: 現在時刻を取得 / ZH: 获取当前时间
        now = datetime.datetime.now()
        # EN: Unix timestamp for CSV / JA: CSV内部用タイムスタンプ / ZH: 用于CSV内部的时间戳
        timestamp_val = now.timestamp()
        
        # EN: Create filename string (YYYYMMDD_HHMMSS_f) 
        # JA: ファイル名用の時刻文字列を作成
        # ZH: 创建文件名用的时间字符串
        time_str = now.strftime('%Y%m%d_%H%M%S_%f')[:-5]
        
        # EN: Generate path: dataset/label_datetime.csv
        # JA: ファイル名を生成
        # ZH: 生成文件名
        filename = f"{label}_{time_str}.csv"
        filepath = os.path.join(DATA_DIR, filename)

        # EN: Save as individual CSV / JA: 個別CSVとして保存 / ZH: 保存为独立CSV文件
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            # EN: Write header / JA: ヘッダーも毎回書き込む / ZH: 每次都写入表头
            writer.writerow(HEADER)
            writer.writerow([timestamp_val, label] + data_to_save)
            
        logger.info(f"SAVED: {filename}")
        
        return {"status": "saved", "filename": filename}
        
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        return JSONResponse(status_code=500, content={"message": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)