from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from Img_predictor import Img_predictor
import csv
import os
import time
import datetime
import threading
import logging

IN_DOCKER = os.path.exists('/dockerenv')
if IN_DOCKER:
    print("Runing in Docker container")
    os.environ['BLIKNA_FORCEBOARD'] = 'RASPBERRY_PI_4B'
    os.environ['BLINKA_FORCECHIP'] = 'BCM2XXX'
    
logger = logging.getLogger("FastAPI_Server")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    print("shutting down camera...")
    os.exit(0)

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

try:
    camera = Img_predictor()
except Exception as e:
    logger.critical(f"Failed to start camera. Exiting.{e}")
    exit(1)

latest_raw_data = None

DATA_DIR = 'dataset'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    logger.info(f"Created data directory: {DATA_DIR}")

HEADER = ['timestamp', 'label'] + [f'pix_{i}' for i in range(768)]

def gen_frames():
    global latest_raw_data
    while True:
        frame_bytes, raw_data = camera.camera()
        if frame_bytes:
            latest_raw_data = raw_data
            yield(
                b'--frame\r\n'
                b'Content-Type: image/jpg\r\n\r\n' + frame_bytes + b'\r\n'
            )
        else:
            time.sleep(0.1)
    
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(gen_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.post("/save")
async def seve_data(request: Request, backgorund_tasks: BackgroundTasks):
    global latest_raw_data
    
    body = await request.json()

    label = body.get("label", "unknown")

    if latest_raw_data is None:
        return JSONResponse({"error": "No data available"})
    
    try:
        data_to_save = list(latest_raw_data)
        now = datetime.datetime.now()
        timestamp_val = now.timestamp()
        time_str = now.strftime("%Y%m%d_%H%M%S_%f")[:-5]
        filename = f"{label}_{time_str}.csv"
        filepath = os.path.join(DATA_DIR, filename)

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(HEADER)
            writer.writerow([timestamp_val, label] + data_to_save)
        
        y_pred = camera.predict_from_camera()
        
        logger.info(f"Saved: {filename}")
        
        return {"Status": "saved", "filename": filename}

    except Exception as e:

        logger.error(f"Error saving data: {e}")

        return JSONResponse(status_code=500, content={"message": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=1)