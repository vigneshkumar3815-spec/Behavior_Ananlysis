import cv2
import numpy as np
import time
from collections import defaultdict
from ultralytics import YOLO

class FallDetector:
    def __init__(self, model_path='yolov8n-pose.pt', unresponsive_thresh=3.0, movement_thresh=30, panic_speed_thresh=300):
        self.model = YOLO(model_path)
        self.unresponsive_thresh = unresponsive_thresh 
        self.movement_thresh = movement_thresh 
        self.panic_speed_thresh = panic_speed_thresh
        
        self.person_states = defaultdict(lambda: {
            'state': 'normal', 
            'fall_start_time': None, 
            'last_center': None,
            'alert_triggered': False,
            'long_alert_triggered': False,
            'running_alert': False,
            'history': [] # list of tuples: (timestamp, cx, cy)
        })
        
    def _is_fallen(self, keypoints, box):
        if len(keypoints) < 17: return False
        x, y, w, h = box
        aspect_ratio = w / h
        head_y = keypoints[0][1] 
        hip_y = (keypoints[11][1] + keypoints[12][1]) / 2
        ankle_y = (keypoints[15][1] + keypoints[16][1]) / 2
        height_estimate = abs(ankle_y - head_y)
        if aspect_ratio > 1.2 or (height_estimate < w * 0.8 and head_y > hip_y):
            return True
        return False

    def process_video_stream(self, video_path, frame_skip=5):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            yield None, [{'type': 'ERROR', 'message': "Error opening video", 'time': 0}]
            return
            
        frame_count = 0
        last_results = None
        last_logs = []
        
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break
                
            frame_count += 1
            current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            
            # Only run heavy YOLO inference every N frames
            if frame_count % frame_skip == 0:
                small_frame = cv2.resize(frame, (640, 360))
                # Use bytetrack for much better ID persistence during occlusions/falls
                results = self.model.track(small_frame, persist=True, tracker="bytetrack.yaml", classes=[0], verbose=False)
                last_results = results
                
            results = last_results
            logs = []
            annotated_frame = frame.copy()
            
            # Format video timestamp
            vid_mins = int(current_time // 60)
            vid_secs = int(current_time % 60)
            vid_time_str = f"[{vid_mins:02d}:{vid_secs:02d}]"
            
            if results and results[0].boxes and results[0].boxes.id is not None:
                # Scale boxes back to original frame size
                orig_h, orig_w = frame.shape[:2]
                scale_x = orig_w / 640.0
                scale_y = orig_h / 360.0
                
                boxes = results[0].boxes.xywh.cpu().numpy()
                boxes[:, [0, 2]] *= scale_x
                boxes[:, [1, 3]] *= scale_y
                
                boxes_xyxy = results[0].boxes.xyxy.cpu().numpy()
                boxes_xyxy[:, [0, 2]] *= scale_x
                boxes_xyxy[:, [1, 3]] *= scale_y
                
                track_ids = results[0].boxes.id.int().cpu().tolist()
                
                if hasattr(results[0], 'keypoints') and results[0].keypoints is not None:
                    keypoints = results[0].keypoints.data.cpu().numpy()
                    # Scale keypoints
                    for i in range(len(keypoints)):
                        if len(keypoints[i]) > 0:
                            keypoints[i][:, 0] *= scale_x
                            keypoints[i][:, 1] *= scale_y
                else:
                    keypoints = [[] for _ in range(len(boxes))]
                
                for box, box_xyxy, track_id, kpts in zip(boxes, boxes_xyxy, track_ids, keypoints):
                    cx, cy, w, h = box
                    state_info = self.person_states[track_id]
                    
                    # --- Behavior Understanding (Walking vs Idle vs Loitering) ---
                    history = state_info.setdefault('history', [])
                    history.append((current_time, cx, cy))
                    # Keep 5 seconds of history for behavior tracking
                    history = [h for h in history if current_time - h[0] <= 5.0]
                    state_info['history'] = history
                    
                    is_fallen = self._is_fallen(kpts, box)
                    
                    if not is_fallen:
                        if len(history) >= 5:
                            dt = history[-1][0] - history[0][0]
                            if dt > 1.0: # Evaluate behavior over at least 1 second
                                xs = [h[1] for h in history]
                                ys = [h[2] for h in history]
                                max_dist = np.sqrt((max(xs) - min(xs))**2 + (max(ys) - min(ys))**2)
                                
                                # If they haven't moved more than half their width over the timeframe
                                if max_dist < w * 0.5:
                                    if state_info.get('idle_start_time') is None:
                                        state_info['idle_start_time'] = current_time
                                    
                                    idle_time = current_time - state_info['idle_start_time']
                                    if idle_time > 10.0 and not state_info.get('loitering_alert'):
                                        logs.append({'type': 'ANOMALY', 'message': f"{vid_time_str} Person {track_id} is loitering (standing still >10s).", 'time': current_time})
                                        state_info['loitering_alert'] = True
                                        
                                    if idle_time > 2.0:
                                        cv2.putText(annotated_frame, f"STANDING IDLE ({int(idle_time)}s)", (int(box_xyxy[0]), int(box_xyxy[1])-25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                                else:
                                    # They are moving
                                    state_info['idle_start_time'] = None
                                    if state_info.get('loitering_alert'):
                                        logs.append({'type': 'NORMAL', 'message': f"{vid_time_str} Person {track_id} resumed moving.", 'time': current_time})
                                    state_info['loitering_alert'] = False
                                    
                                    speed = max_dist / dt
                                    relative_speed = speed / max(h, 1)
                                    if relative_speed > 0.3:
                                        cv2.putText(annotated_frame, "WALKING", (int(box_xyxy[0]), int(box_xyxy[1])-25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                    # --- Fall Detection ---
                    is_fallen = self._is_fallen(kpts, box)
                    
                    # --- Determine Visual State Color ---
                    box_color = (0, 255, 0) # Green = Normal/Walking
                    if is_fallen or state_info.get('long_alert_triggered'):
                        box_color = (0, 0, 255) # Red = Critical
                    elif state_info.get('loitering_alert') or state_info.get('alert_triggered'):
                        box_color = (0, 0, 255) # Red = Anomaly
                    elif state_info.get('idle_start_time') is not None:
                        box_color = (0, 255, 255) # Yellow = Warning/Idle
                        
                    # --- Draw Bounding Box & Label ---
                    cv2.rectangle(annotated_frame, (int(box_xyxy[0]), int(box_xyxy[1])), (int(box_xyxy[2]), int(box_xyxy[3])), box_color, 2)
                    label = f"ID: {track_id}"
                    cv2.putText(annotated_frame, label, (int(box_xyxy[0]), int(box_xyxy[1])-8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
                    
                    # --- Draw Motion Trail ---
                    if len(history) > 1:
                        for i in range(1, len(history)):
                            # Fade color based on age (older = thinner/darker)
                            pt1 = (int(history[i-1][1]), int(history[i-1][2] + h/2)) # Bottom center of person
                            pt2 = (int(history[i][1]), int(history[i][2] + h/2))
                            thickness = max(1, int(3 * (i / len(history))))
                            cv2.line(annotated_frame, pt1, pt2, box_color, thickness)
                    
                    if is_fallen:
                        if state_info['state'] == 'normal':
                            state_info['state'] = 'fallen'
                            state_info['fall_start_time'] = current_time
                            state_info['last_center'] = (cx, cy)
                            state_info['running_alert'] = False
                            logs.append({'type': 'FALL_EVENT', 'message': f"{vid_time_str} Person {track_id} fell.", 'time': current_time})
                        
                        elif state_info['state'] == 'fallen':
                            time_fallen = current_time - state_info['fall_start_time']
                            prev_cx, prev_cy = state_info['last_center']
                            movement = np.sqrt((cx - prev_cx)**2 + (cy - prev_cy)**2)
                            
                            if time_fallen > self.unresponsive_thresh:
                                if movement < self.movement_thresh:
                                    if not state_info['alert_triggered']:
                                        logs.append({'type': 'UNRESPONSIVE_ALERT', 'message': f"{vid_time_str} Person {track_id} unresponsive for {int(time_fallen)}s.", 'time': current_time})
                                        state_info['alert_triggered'] = True
                                        
                                    # 15 Second Critical Alert Dispatch
                                    if time_fallen > 15.0 and not state_info['long_alert_triggered']:
                                        logs.append({'type': 'DISPATCH_ALERT', 'message': f"{vid_time_str} Person {track_id} unresponsive for >15s! Dispatching help.", 'time': current_time})
                                        state_info['long_alert_triggered'] = True
                                        
                                    cv2.rectangle(annotated_frame, (int(box_xyxy[0]), int(box_xyxy[1])), 
                                                  (int(box_xyxy[2]), int(box_xyxy[3])), (0, 0, 255), 4)
                                    cv2.putText(annotated_frame, f"UNRESPONSIVE!", 
                                                (int(box_xyxy[0]), int(box_xyxy[1])-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)
                                else:
                                    # Reset if they move
                                    state_info['fall_start_time'] = current_time
                                    state_info['alert_triggered'] = False
                                    state_info['long_alert_triggered'] = False
                                    
                            state_info['last_center'] = (cx, cy)
                    else:
                        if state_info['state'] == 'fallen':
                            logs.append({'type': 'RECOVER_EVENT', 'message': f"{vid_time_str} Person {track_id} got back up.", 'time': current_time})
                        state_info['state'] = 'normal'
                        state_info['fall_start_time'] = None
                        state_info['alert_triggered'] = False
                        state_info['long_alert_triggered'] = False
            else:
                annotated_frame = frame
                
            # Only yield frame to UI if there are logs (to show alerts immediately) or every 3rd frame to save massive UI overhead
            if len(logs) > 0 or frame_count % 3 == 0:
                # Resize the output frame to 720p maximum to drastically reduce Streamlit websocket lag
                out_h, out_w = annotated_frame.shape[:2]
                if out_w > 1280:
                    scale = 1280 / out_w
                    annotated_frame = cv2.resize(annotated_frame, (1280, int(out_h * scale)))
                    
                yield annotated_frame, logs
            
        cap.release()

    def process_video(self, video_path, output_path=None):
        for frame, logs in self.process_video_stream(video_path):
            if frame is None: break
            cv2.imshow("Fall & Unresponsive Detection", frame)
            for log in logs: print(log['message'])
            if cv2.waitKey(1) & 0xFF == ord("q"): break
        cv2.destroyAllWindows()
