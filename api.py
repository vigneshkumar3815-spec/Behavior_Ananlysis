import cv2
import threading
import time
import os
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from fall_detection import FallDetector

app = FastAPI(title="SentinelVision API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoStreamer:
    def __init__(self):
        self.detector = FallDetector()
        self.current_frame = None
        self.events = []
        self.source = None # Default to no video source
        self.lock = threading.Lock()
        self.running_source = self.source
        self.source_changed = False
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()
        
    def change_source(self, new_source):
        self.source = new_source
        self.source_changed = True
        
    def _update(self):
        while True:
            self.running_source = self.source
            self.source_changed = False
            
            if self.running_source is None:
                time.sleep(0.5)
                continue
                
            # Try local webcam first if source is 0
            cap = cv2.VideoCapture(self.running_source)
            if not cap.isOpened():
                print(f"Failed to open source: {self.running_source}")
                self.source = None
                continue
            else:
                cap.release()

            for frame, logs in self.detector.process_video_stream(self.running_source):
                if self.source_changed:
                    break # Break out of the generator to restart with new source
                if frame is None:
                    break
                ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                if ret:
                    with self.lock:
                        self.current_frame = buffer.tobytes()
                        if logs:
                            # We attach a unique ID to each log for the frontend
                            for log in logs:
                                log['id'] = str(time.time()) + "-" + str(log['time'])
                            self.events.extend(logs)
                time.sleep(0.01)
            time.sleep(1)

streamer = VideoStreamer()

def generate():
    while True:
        with streamer.lock:
            frame = streamer.current_frame
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.033)

@app.get("/api/video_feed")
def video_feed():
    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/api/events")
def get_events():
    with streamer.lock:
        logs = streamer.events.copy()
        streamer.events.clear()
    return {"events": logs}

@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    # Save uploaded file to disk
    os.makedirs("uploads", exist_ok=True)
    file_path = os.path.join("uploads", file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
        
    # Tell the streamer to switch to the new video
    streamer.change_source(file_path)
    return {"status": "success", "filename": file.filename, "message": "Video uploaded and stream switched!"}

from pydantic import BaseModel
class SourceRequest(BaseModel):
    source: int

@app.post("/api/set_source")
def set_source(req: SourceRequest):
    streamer.change_source(req.source)
    return {"status": "success", "message": f"Switched to source {req.source}"}

class CustomRuleRequest(BaseModel):
    rule: str
    api_key: str = None

@app.post("/api/custom_rule")
def set_custom_rule(req: CustomRuleRequest):
    streamer.detector.set_custom_rule(req.rule, req.api_key)
    return {"status": "success", "message": f"Custom rule updated to: {req.rule}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
