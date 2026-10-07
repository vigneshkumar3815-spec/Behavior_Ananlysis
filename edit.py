import re

with open("d:/HackNex/fall_detection.py", "r") as f:
    code = f.read()

# Imports
code = code.replace("from ultralytics import YOLO", "from ultralytics import YOLO\nimport os\nimport threading\nimport base64\nfrom io import BytesIO\nfrom PIL import Image\ntry:\n    from google import genai\nexcept ImportError:\n    genai = None")

# Init
init_block = """        self.panic_speed_thresh = panic_speed_thresh
        
        self.custom_rule = None
        self.gemini_client = None
        self.gemini_alerts = [] # Thread-safe appending
"""
code = code.replace("        self.panic_speed_thresh = panic_speed_thresh\n", init_block)

# set_custom_rule
set_rule_code = """
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
            response = self.gemini_client.models.generate_content(
                model='gemini-1.5-flash',
                contents=[prompt, pil_img]
            )
            if "TRUE" in response.text.upper():
                self.gemini_alerts.append({'type': 'CUSTOM_ALERT', 'message': f"{vid_time_str} AI VISION FLAG [{rule}] on Person {track_id}", 'time': current_time, 'track_id': track_id})
        except Exception as e:
            print("Gemini eval error:", e)

    def process_video_stream(self, video_path, frame_skip=2):"""
code = code.replace("    def process_video_stream(self, video_path, frame_skip=2):", set_rule_code)

# Add alert draining and evaluation spawning
loop_inject = """            
            # Drain Gemini alerts
            while len(self.gemini_alerts) > 0:
                logs.append(self.gemini_alerts.pop(0))

            if results is not None and len(results) > 0 and results[0].boxes is not None and results[0].boxes.id is not None:"""
code = code.replace("            if results is not None and len(results) > 0 and results[0].boxes is not None and results[0].boxes.id is not None:", loop_inject)

# Spawn thread on tracking logic
spawn_logic = """                    # --- Draw Bounding Box & Label ---
                    # --- Advanced HUD Rendering (Wow Factor) ---
                    # Draw Skeleton Keypoints
                    
                    if self.custom_rule and frame_count % 30 == 0:
                        crop = frame[max(0, int(box_xyxy[1])):int(box_xyxy[3]), max(0, int(box_xyxy[0])):int(box_xyxy[2])].copy()
                        if crop.size > 0:
                            threading.Thread(target=self._evaluate_gemini, args=(crop, track_id, self.custom_rule, current_time, vid_time_str), daemon=True).start()
                            
                    # Draw Skeleton Keypoints"""
code = code.replace("                    # --- Draw Bounding Box & Label ---\n                    # --- Advanced HUD Rendering (Wow Factor) ---\n                    # Draw Skeleton Keypoints", spawn_logic)


# Alert red box logic for custom alerts
red_box = """                        if state_info['state'] == 'hands_up':
                                state_info['state'] = 'normal'
                        
                    # Check if recently flagged by Gemini
                    recently_flagged = any(log['type'] == 'CUSTOM_ALERT' and log.get('track_id') == track_id and (current_time - log['time']) < 5.0 for log in self.gemini_alerts + logs)
                    if recently_flagged:
                        box_color = (0, 0, 255) # Red for Custom Alert
                        cv2.putText(annotated_frame, f"FLAG: {self.custom_rule[:15]}", (int(box_xyxy[0]), int(box_xyxy[1])-70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)
"""
code = code.replace("                        if state_info['state'] == 'hands_up':\n                                state_info['state'] = 'normal'", red_box)

with open("d:/HackNex/fall_detection.py", "w") as f:
    f.write(code)
print("Done editing fall_detection.py")
