import cv2
import numpy as np
import time
from collections import defaultdict
from ultralytics import YOLO
import os
import threading
import base64
from io import BytesIO
from PIL import Image
try:
    from google import genai
except ImportError:
    genai = None

class FallDetector:
    def __init__(self, model_path='yolov8s-pose.pt', unresponsive_thresh=3.0, movement_thresh=30, panic_speed_thresh=300):
        self.model = YOLO(model_path)
        self.unresponsive_thresh = unresponsive_thresh 
        self.movement_thresh = movement_thresh 
        self.panic_speed_thresh = panic_speed_thresh
        
        self.custom_rule = None
        self.gemini_client = None
        self.gemini_alerts = [] # Thread-safe appending
        
        self.person_states = defaultdict(lambda: {
            'state': 'normal', 
            'fall_start_time': None, 
            'last_center': None,
            'alert_triggered': False,
            'long_alert_triggered': False,
            'running_alert': False,
            'history': [] # list of tuples: (timestamp, cx, cy)
        })
        
    def _is_fallen(self, keypoints, box, state_info):
        x, y, w, h = box
        aspect_ratio = w / h
        
        # Hysteresis: if already fallen, require a much stricter threshold to "recover" (stand back up)
        # This prevents flickering recovery events while the person is crumpled on the floor.
        if state_info['state'] == 'fallen':
            if aspect_ratio < 0.8: 
                return False # Clearly standing up
            return True # Still on the ground
            
        # If normal, require strict threshold to fall
        if aspect_ratio > 1.2:
            return True
            
        if len(keypoints) >= 17:
            head_y = keypoints[0][1] 
            hip_y = (keypoints[11][1] + keypoints[12][1]) / 2
            ankle_y = (keypoints[15][1] + keypoints[16][1]) / 2
            if ankle_y > 0 and head_y > 0: # Valid keypoints
                height_estimate = abs(ankle_y - head_y)
                if height_estimate < w * 0.8 and head_y > hip_y:
                    return True
        return False


    def set_custom_rule(self, rule, api_key=None):
        self.custom_rule = rule if rule and rule.strip() != "" else None
        if api_key and genai:
            self.gemini_client = genai.Client(api_key=api_key)
        elif not self.gemini_client and genai and os.environ.get("GEMINI_API_KEY"):
            self.gemini_client = genai.Client()

    def _evaluate_gemini(self, crop, track_id, rule, current_time, vid_time_str):
        if not self.gemini_client: return
        try:
            pil_img = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
            prompt = f"Does this image show the anomaly: '{rule}'? Reply only TRUE or FALSE. Look closely at the person in the image."
            interaction = self.gemini_client.interactions.create(
                model='gemini-3.8-flash',
                input=[prompt, pil_img]
            )
            if interaction.output_text and "TRUE" in interaction.output_text.upper():
                self.gemini_alerts.append({'type': 'CUSTOM_ALERT', 'message': f"{vid_time_str} AI VISION FLAG [{rule}] on Person {track_id}", 'time': current_time, 'track_id': track_id})
        except Exception as e:
            print("Gemini eval error:", e)

    def process_video_stream(self, video_path, frame_skip=2):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            yield None, [{'type': 'ERROR', 'message': "Error opening video", 'time': 0}]
            return
            
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
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
                # conf=0.3 allows Nano model to see people without filtering them out before tracking
                results = self.model.track(small_frame, persist=True, tracker="bytetrack.yaml", conf=0.3, classes=[0], verbose=False)
                last_results = results
                
            results = last_results
            logs = []
            annotated_frame = frame.copy()
            
            # Format video timestamp
            vid_mins = int(current_time // 60)
            vid_secs = int(current_time % 60)
            vid_time_str = f"[{vid_mins:02d}:{vid_secs:02d}]"
            
            # Drain Gemini alerts
            while len(self.gemini_alerts) > 0:
                alert = self.gemini_alerts.pop(0)
                t_id = alert.get('track_id')
                if t_id is not None:
                    s_info = self.person_states[t_id]
                    s_info['last_gemini_flag_time'] = current_time
                    if current_time - s_info.get('last_gemini_alert_time', -100.0) > 15.0:
                        logs.append(alert)
                        s_info['last_gemini_alert_time'] = current_time
                else:
                    logs.append(alert)
                
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
                    
                    is_fallen = self._is_fallen(kpts, box, state_info)
                    
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
                    # is_fallen is already evaluated above
                    # --- Determine Visual State Color ---
                    box_color = (0, 255, 0) # Green = Normal/Walking
                    if is_fallen or state_info.get('long_alert_triggered'):
                        box_color = (0, 0, 255) # Red = Critical
                    elif state_info.get('loitering_alert') or state_info.get('alert_triggered'):
                        box_color = (0, 0, 255) # Red = Anomaly
                    elif state_info.get('idle_start_time') is not None:
                        box_color = (0, 255, 255) # Yellow = Warning/Idle
                        
                    # --- Complex Behavior: Hands Up ---
                    if not is_fallen and len(kpts) >= 17:
                        nose_y = kpts[0][1]
                        l_wrist_y = kpts[9][1]
                        r_wrist_y = kpts[10][1]
                        # Check if both wrists are detected and above the nose (lower y value)
                        if nose_y > 0 and l_wrist_y > 0 and r_wrist_y > 0:
                            if l_wrist_y < nose_y and r_wrist_y < nose_y:
                                state_info['state'] = 'hands_up'
                                box_color = (255, 0, 255) # Purple for Hands Up
                                cv2.putText(annotated_frame, "DISTRESS / HANDS UP!", (int(box_xyxy[0]), int(box_xyxy[1])-45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)
                            elif state_info['state'] == 'hands_up':
                                state_info['state'] = 'normal'
                                
                    # Check if recently flagged by Gemini
                    recently_flagged = (current_time - state_info.get('last_gemini_flag_time', -100.0)) < 5.0
                    if recently_flagged:
                        box_color = (0, 0, 255) # Red for Custom Alert
                        cv2.putText(annotated_frame, f"FLAG: {self.custom_rule[:15] if self.custom_rule else ''}", (int(box_xyxy[0]), int(box_xyxy[1])-70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)
                        
                    # --- Draw Bounding Box & Label ---
                    # --- Advanced HUD Rendering (Wow Factor) ---
                    # Draw Skeleton Keypoints
                    
                    if self.custom_rule and frame_count % 30 == 0:
                        crop = frame[max(0, int(box_xyxy[1])):int(box_xyxy[3]), max(0, int(box_xyxy[0])):int(box_xyxy[2])].copy()
                        if crop.size > 0:
                            threading.Thread(target=self._evaluate_gemini, args=(crop, track_id, self.custom_rule, current_time, vid_time_str), daemon=True).start()
                            
                    # Draw Skeleton Keypoints
                    if kpts is not None and len(kpts) >= 17:
                        for kp in kpts:
                            kx, ky = int(kp[0]), int(kp[1])
                            if kx > 0 and ky > 0:
                                cv2.circle(annotated_frame, (kx, ky), 4, (0, 255, 255), -1)
                        
                        # Draw Skeleton Connections
                        connections = [(5,7), (7,9), (6,8), (8,10), (5,6), (5,11), (6,12), (11,12), (11,13), (13,15), (12,14), (14,16)]
                        for (p1, p2) in connections:
                            x1, y1 = int(kpts[p1][0]), int(kpts[p1][1])
                            x2, y2 = int(kpts[p2][0]), int(kpts[p2][1])
                            if x1 > 0 and y1 > 0 and x2 > 0 and y2 > 0:
                                cv2.line(annotated_frame, (x1, y1), (x2, y2), box_color, 2)

                    # Draw Corner Brackets
                    x1, y1, x2, y2 = int(box_xyxy[0]), int(box_xyxy[1]), int(box_xyxy[2]), int(box_xyxy[3])
                    ll = max(15, int((x2-x1)*0.2))
                    for pt, dx, dy in [((x1,y1), ll, ll), ((x2,y1), -ll, ll), ((x1,y2), ll, -ll), ((x2,y2), -ll, -ll)]:
                        cv2.line(annotated_frame, pt, (pt[0]+dx, pt[1]), box_color, 3)
                        cv2.line(annotated_frame, pt, (pt[0], pt[1]+dy), box_color, 3)
                        
                    label = f"TGT-{track_id:03d} [{state_info['state'].upper()}]"
                    cv2.putText(annotated_frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
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
                
            # Draw Progress Bar at the bottom
            if total_frames > 0:
                progress = min(1.0, frame_count / total_frames)
                h, w = annotated_frame.shape[:2]
                bar_h = 10
                # Dark background track
                cv2.rectangle(annotated_frame, (0, h - bar_h), (w, h), (30, 30, 30), -1)
                # Cyan progress fill
                cv2.rectangle(annotated_frame, (0, h - bar_h), (int(w * progress), h), (255, 255, 0), -1)
                
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
