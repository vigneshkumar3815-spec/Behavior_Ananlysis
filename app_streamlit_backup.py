import streamlit as st
import cv2
import tempfile
import time
import pandas as pd
from fall_detection import FallDetector

# Must be the very first Streamlit command
st.set_page_config(page_title="Vision Intelligence Dashboard", page_icon="👁️", layout="wide", initial_sidebar_state="expanded")

# --- Session State for Login & Logging ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = True
    st.session_state.user_contact = "admin@hacknex.com"
if 'event_logs' not in st.session_state:
    st.session_state.event_logs = []

# --- Custom CSS for Sleek & Accessible Design ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    :root {
        --bg: #07111f;
        --bg-elev: #0d1b2a;
        --panel: rgba(15, 23, 42, 0.88);
        --panel-strong: rgba(12, 18, 30, 0.96);
        --border: rgba(148, 163, 184, 0.18);
        --muted: #a5b4cf;
        --text: #edf3ff;
        --accent: #67e8f9;
        --accent-2: #22c55e;
        --warning: #fbbf24;
        --danger: #ff5a5f;
        --shadow: 0 18px 40px rgba(2, 6, 23, 0.45);
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background: radial-gradient(circle at top, rgba(34, 211, 238, 0.16), transparent 30%),
                    linear-gradient(135deg, #020817 0%, #0a1426 30%, #040d1a 100%);
        color: var(--text);
    }

    .stApp {
        background: transparent;
    }

    div[data-testid="stAppViewContainer"] > .main {
        background: transparent;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1500px;
    }

    h1, h2, h3 {
        color: var(--text) !important;
        font-weight: 800 !important;
        letter-spacing: -0.04em !important;
    }

    .stTabs [role="tablist"] {
        gap: 0.5rem;
    }

    .stButton > button,
    .stDownloadButton > button {
        background: linear-gradient(135deg, #10253c, #1d3557);
        color: white;
        border: 1px solid rgba(103, 232, 249, 0.35);
        border-radius: 12px;
        padding: 0.75rem 1rem;
        font-weight: 700;
        box-shadow: var(--shadow);
        transition: all 0.2s ease;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        border-color: rgba(103, 232, 249, 0.9);
        transform: translateY(-1px);
    }

    .stButton > button:focus,
    .stDownloadButton > button:focus {
        box-shadow: 0 0 0 0.2rem rgba(103, 232, 249, 0.25);
    }

    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div,
    .stCheckbox > div {
        background: rgba(15, 23, 42, 0.7);
        color: var(--text);
        border: 1px solid var(--border);
        border-radius: 12px;
    }

    .stFileUploader > div > div {
        background: rgba(15, 23, 42, 0.7);
        border: 2px dashed rgba(103, 232, 249, 0.35);
        border-radius: 14px;
        color: var(--text);
    }

    .sidebar .block-container {
        background: rgba(6, 12, 20, 0.75);
        border-right: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 0;
    }

    [data-testid="stSidebar"] {
        background: rgba(7, 17, 31, 0.96);
        border-right: 1px solid rgba(148, 163, 184, 0.16);
    }

    [data-testid="stSidebarNav"] {
        background: transparent;
    }

    .log-console {
        background: linear-gradient(180deg, rgba(15, 23, 42, 0.95), rgba(10, 15, 27, 0.98));
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 16px;
        padding: 20px;
        height: 500px;
        overflow-y: auto;
        font-family: 'Courier New', Courier, monospace;
        font-size: 14px;
        line-height: 1.6;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), var(--shadow);
    }

    .log-alert { color: #ff8a8a; font-weight: 600; background-color: rgba(255, 90, 95, 0.12); padding: 6px 10px; border-radius: 8px; margin-bottom: 6px; border: 1px solid rgba(255, 90, 95, 0.18); }
    .log-dispatch { color: #ffffff; font-weight: 700; background: linear-gradient(135deg, rgba(255, 90, 95, 0.95), rgba(185, 28, 28, 0.95)); padding: 8px 10px; border-radius: 8px; margin-bottom: 6px; border: 1px solid rgba(255, 255, 255, 0.12); }
    .log-panic { color: #ffd166; font-weight: 700; background-color: rgba(251, 191, 36, 0.10); padding: 6px 10px; border-radius: 8px; margin-bottom: 6px; border: 1px solid rgba(251, 191, 36, 0.2); }
    .log-event { color: #ffe38c; font-weight: 600; padding: 6px 10px; margin-bottom: 6px; border-radius: 8px; background-color: rgba(250, 202, 21, 0.08); }
    .log-success { color: #7ef7bd; font-weight: 600; padding: 6px 10px; margin-bottom: 6px; border-radius: 8px; background-color: rgba(34, 197, 94, 0.08); }
    .log-normal { color: #c0d1ef; padding: 6px 10px; margin-bottom: 6px; border-radius: 8px; }

    [data-testid="stMetricValue"] {
        font-size: 1.9rem !important;
        font-weight: 800 !important;
        color: var(--text) !important;
    }

    [data-testid="stMetricLabel"] {
        color: var(--muted) !important;
        font-size: 0.78rem !important;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    .metric-card {
        border: 1px solid rgba(148, 163, 184, 0.18);
        background: linear-gradient(180deg, rgba(15, 23, 42, 0.85), rgba(11, 17, 28, 0.9));
        border-radius: 16px;
        padding: 1rem 1.1rem;
        box-shadow: var(--shadow);
    }

    .glass-panel {
        background: rgba(15, 23, 42, 0.7);
        border-radius: 18px;
        border: 1px solid rgba(148, 163, 184, 0.18);
        box-shadow: var(--shadow);
        padding: 1.25rem;
    }

    .source-card {
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.96), rgba(12, 18, 30, 0.9));
        border: 1px solid rgba(103, 232, 249, 0.32);
        border-radius: 20px;
        padding: 1.2rem 1.3rem;
        box-shadow: var(--shadow);
        margin-bottom: 1rem;
    }

    .source-card h4 {
        margin: 0 0 0.3rem 0;
        color: var(--text);
        font-weight: 700;
    }

    .upload-banner {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(34, 211, 238, 0.1));
        border: 1px solid rgba(34, 211, 238, 0.24);
        border-radius: 16px;
        padding: 0.9rem 1rem;
        color: var(--text);
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

if not st.session_state.logged_in:
    # --- Authentication Page ---
    st.markdown("<div style='padding: 2rem 0 0.5rem 0;'><h1 style='font-size: 2.6rem; margin-bottom: 0.2rem;'>🔒 Security Operations Center</h1></div>", unsafe_allow_html=True)
    st.markdown("<p style='color: #b8c7df; font-size: 1.08rem; margin-top: 0.2rem; margin-bottom: 1.8rem;'>Please log in with your <strong>Gmail</strong> or <strong>Phone Number</strong> to access the dashboard.</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class='glass-panel' style='padding: 1.5rem; border-radius: 20px; margin-bottom: 1rem;'>
            <div style='display: flex; align-items: center; gap: 0.7rem; margin-bottom: 0.75rem;'>
                <div style='width: 12px; height: 12px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 18px rgba(34, 197, 94, 0.8);'></div>
                <span style='color: #dfe9ff; font-weight: 700;'>Secure Access</span>
            </div>
        """, unsafe_allow_html=True)
        with st.form("login_form"):
            contact = st.text_input("Gmail or Phone Number", value="admin@hacknex.com", placeholder="e.g., admin@gmail.com or +1234567890")
            password = st.text_input("Password (Optional for Demo)", type="password", value="demo123")
            submit = st.form_submit_button("Secure Login", use_container_width=True)

            if submit:
                if contact:
                    st.session_state.user_contact = contact
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("⚠️ Please enter a valid email or phone number to continue.")
        st.markdown("</div>", unsafe_allow_html=True)
else:
    # --- Main Dashboard ---
    st.markdown("<div style='display: flex; justify-content: space-between; align-items: end; gap: 1rem; flex-wrap: wrap; margin-bottom: 0.5rem;'><div><h1 style='margin: 0; font-size: 2.4rem;'>👁️ Autonomous Vision Intelligence</h1></div></div>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #7ef7bd; font-size: 1rem; margin-top: -6px; margin-bottom: 0.5rem;'>👤 Logged in as: <b>{st.session_state.user_contact}</b></p>", unsafe_allow_html=True)
    st.markdown("---")

    # --- Sidebar Configuration ---
    with st.sidebar:
        st.header("⚙️ System Settings")
        
        st.markdown("### 🔔 Emergency Notifications")
        send_alerts = st.checkbox("Enable SMS/Email Dispatch", value=True, help="Sends an emergency alert to your login contact if someone is unresponsive for > 15 seconds.")
        
        st.markdown("---")
        st.markdown("### 🎛️ AI Parameters")
        unresponsive_thresh = st.slider("Initial Alert Threshold (sec)", min_value=1.0, max_value=10.0, value=3.0, step=0.5)
        panic_speed_thresh = st.slider("Panic Speed Threshold (px/s)", min_value=100, max_value=800, value=300, step=50, help="Lower values make the AI more sensitive to running speeds.")
        movement_thresh = st.slider("Movement Tolerance (px)", min_value=10, max_value=100, value=30, step=5)
                                    
        st.markdown("---")
        st.header("🎥 Data Source")
        use_webcam = st.checkbox("Use Live Webcam Feed", value=False)
        st.caption("Upload a video file to analyze recorded footage for falls and emergencies.")
        uploaded_file = st.file_uploader(
            "📂 Upload Surveillance Footage",
            type=['mp4', 'avi', 'mov'],
            help="Supported formats: MP4, AVI, MOV. The model will detect falls from the uploaded footage.",
            use_container_width=True
        )

        if uploaded_file is not None:
            st.success(f"Loaded: {uploaded_file.name}")

        st.markdown("---")
        st.header("📥 Reporting")
        
        # CSV Export Logic
        if st.session_state.event_logs:
            df = pd.DataFrame(st.session_state.event_logs)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Incident Log (CSV)",
                data=csv,
                file_name=f"soc_incident_report_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv',
                use_container_width=True
            )
        else:
            st.button("📥 Export Incident Log (CSV)", disabled=True, use_container_width=True, help="No incidents to export yet.")
            
        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_contact = ""
            st.session_state.event_logs = []
            st.rerun()

    video_source = None

    if use_webcam:
        video_source = 0  # 0 targets the default local webcam
    else:
        if uploaded_file is not None:
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            tfile.write(uploaded_file.read())
            video_source = tfile.name

    if not use_webcam and uploaded_file is None:
        st.markdown("""
        <div class='source-card'>
            <h4>📁 Upload a video file to detect falls</h4>
            <div class='upload-banner'>Select a recorded MP4, AVI, or MOV file from the sidebar to start fall monitoring.</div>
        </div>
        """, unsafe_allow_html=True)

    if video_source is not None:
        # Dashboard layout
        col_video, col_panel = st.columns([2.6, 1.4], gap="large")

        with col_video:
            st.markdown("<div class='glass-panel' style='padding: 0.9rem 1rem 0.7rem 1rem; margin-bottom: 0.9rem;'><h3 style='margin: 0;'>📷 Live Camera Feed</h3></div>", unsafe_allow_html=True)
            stframe = st.empty()

        with col_panel:
            st.markdown("<div class='glass-panel' style='padding: 0.9rem 1rem 0.7rem 1rem; margin-bottom: 0.9rem;'><h3 style='margin: 0;'>📊 Live Analytics</h3></div>", unsafe_allow_html=True)
            metric_col1, metric_col2 = st.columns(2)
            metric_alerts = metric_col1.empty()
            metric_status = metric_col2.empty()

            metric_alerts.markdown("""
            <div class='metric-card'>
                <div style='color: #a5b4cf; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.08em;'>Active Critical Alerts</div>
                <div style='font-size: 2.1rem; font-weight: 800; margin-top: 0.35rem;'>0</div>
            </div>
            """, unsafe_allow_html=True)
            metric_status.markdown("""
            <div class='metric-card'>
                <div style='color: #a5b4cf; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.08em;'>System Status</div>
                <div style='font-size: 1.2rem; font-weight: 700; margin-top: 0.35rem; color: #7ef7bd;'>Initializing...</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div class='glass-panel' style='padding: 0.9rem 1rem 0.7rem 1rem; margin-top: 1rem; margin-bottom: 0.9rem;'><h3 style='margin: 0;'>📋 Security Event Log</h3></div>", unsafe_allow_html=True)
            log_container = st.empty()
            log_container.markdown('<div class="log-console"><span class="log-normal">System initialized. Awaiting events...</span></div>', unsafe_allow_html=True)

        # Initialize AI
        detector = FallDetector(unresponsive_thresh=unresponsive_thresh, movement_thresh=movement_thresh, panic_speed_thresh=panic_speed_thresh)
        all_logs_html = []
        active_alert_count = 0
        
        metric_status.metric(label="System Status", value="Monitoring Live")
        
        # Process video stream
        for frame, logs in detector.process_video_stream(video_source):
            if frame is None:
                st.error("Lost connection to video source.")
                break
                
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            stframe.image(frame_rgb, channels="RGB", use_container_width=True)
            
            if logs:
                for log_event in logs:
                    t_stamp = time.strftime('%H:%M:%S') # Simulated real-world time for logs
                    msg = log_event['message']
                    l_type = log_event['type']
                    
                    # 1. Save to Database / Session State for Exporting later
                    st.session_state.event_logs.append({
                        'Time': t_stamp,
                        'Event Type': l_type,
                        'Details': msg
                    })
                    
                    # 2. Format HTML output for the live UI log console
                    if l_type == 'DISPATCH_ALERT':
                        formatted_log = f"<div class='log-dispatch'>[{t_stamp}] ☎️ {msg}</div>"
                        if send_alerts:
                            st.toast(f"📧 ALERT SENT TO: {st.session_state.user_contact}", icon="🚨")
                    elif l_type == 'UNRESPONSIVE_ALERT':
                        formatted_log = f"<div class='log-alert'>[{t_stamp}] 🚨 {msg}</div>"
                        active_alert_count += 1
                    elif l_type == 'PANIC_ALERT':
                        formatted_log = f"<div class='log-panic'>[{t_stamp}] 🏃 {msg}</div>"
                    elif l_type == 'FALL_EVENT':
                        formatted_log = f"<div class='log-event'>[{t_stamp}] ⚠️ {msg}</div>"
                    elif l_type == 'RECOVER_EVENT':
                        formatted_log = f"<div class='log-success'>[{t_stamp}] ✅ {msg}</div>"
                        active_alert_count = max(0, active_alert_count - 1)
                    else:
                        formatted_log = f"<div class='log-normal'>[{t_stamp}] {msg}</div>"
                        
                    all_logs_html.append(formatted_log)
                
                # Keep last 25 logs rendered to prevent lag
                display_html = "".join(all_logs_html[-25:])
                log_container.markdown(f'<div class="log-console">{display_html}</div>', unsafe_allow_html=True)
                
                # Update metrics
                if active_alert_count > 0:
                    metric_alerts.metric(label="Active Critical Alerts", value=active_alert_count, delta="URGENT", delta_color="inverse")
                else:
                    metric_alerts.metric(label="Active Critical Alerts", value="0")
                    
            # Check for changes in the sidebar dynamically
            st.session_state.current_frame = frame

        if not use_webcam:
            metric_status.metric(label="System Status", value="Complete", delta="100%")
            st.success("✅ Analysis Complete. System returning to standby.")
