# SentinelVision

SentinelVision is an AI-powered engine for behavior and fall detection using video streams. It consists of a FastAPI backend and a React (Vite) dashboard.

## Prerequisites

- **Python 3.8+**
- **Node.js 18+**

## Setup & Installation

### 1. Install Backend Dependencies
Ensure you have the required Python packages installed:
```bash
pip install fastapi uvicorn opencv-python ultralytics python-multipart
```
*(Note: `python-multipart` is required for file uploads in FastAPI).*

### 2. Install Frontend Dependencies
Navigate to the `SentinelVision` folder and install the required Node modules:
```bash
cd SentinelVision
npm install
```

## How to Run

### Windows Quick Start
You can easily start both the backend and frontend simultaneously by double-clicking the **`start.bat`** file in the root directory.

### Manual Start
**Backend (FastAPI):**
```bash
python api.py
```

**Frontend (React):**
```bash
cd SentinelVision
npm run dev
```

The React Dashboard will be available at: [http://localhost:5173/](http://localhost:5173/)

## Testing
A `test_videos/` folder has been provided in the repository. You can place your sample `.mp4` or `.avi` test files here, which can then be uploaded through the frontend dashboard for analysis.
