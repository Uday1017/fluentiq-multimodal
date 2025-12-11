<div align="center">📣 FluentIQ</div>
<div align="center">AI-Powered Multimodal Public Speaking & Communication Feedback System</div>
<div align="center"> A research-driven project analyzing **speech**, **language**, and **non-verbal communication** using multimodal machine learning. <br><br> <img src="https://img.shields.io/badge/Framework-FastAPI-009688?style=flat-square"/> <img src="https://img.shields.io/badge/Frontend-HTML%2FCSS%2FJS-blue?style=flat-square"/> <img src="https://img.shields.io/badge/Models-ML%2FRL%2BRule--Based-orange?style=flat-square"/> </div>
📍 Overview

FluentIQ is an AI-powered multimodal analysis system designed to evaluate key aspects of public speaking performance using:

🔹 Audio cues (fluency, pauses, rate of speech)
🔹 Textual language quality (grammar, coherence, readability)
🔹 Visual cues (posture, gaze, movement)
🔹 Fused multimodal scoring (overall performance score)

It provides:

Detailed feedback

Skill improvement plans

Analytics dashboard

Session-wise history

Radar & line charts

Export options (CSV, PNG, JSON)

This project supports research titled:
“AI-Powered Multimodal Framework for Enhancing Public Speaking and Communication Skills.”

🧠 System Architecture
               ┌──────────────┐
               │   Frontend    │
               │ HTML/CSS/JS   │
               └──────┬───────┘
                      │ Upload video/audio
                      ▼
              ┌─────────────────────┐
              │     FastAPI API     │
              └─────────────────────┘
       ┌─────────────┬──────────────┬──────────────┐
       ▼             ▼              ▼              ▼
┌──────────┐   ┌──────────┐  ┌────────────┐  ┌──────────────┐
│ Audio     │→ │ Text      │→│ Video       │→│ Fusion Model  │
│ Analysis  │  │ Analysis  │ │ Analysis    │ │ (Rule-based)  │
└──────────┘   └──────────┘  └────────────┘  └──────────────┘
                     │
                     ▼
          ┌───────────────────────┐
          │ SQLite Session Storage │
          └─────────┬─────────────┘
                    │
                    ▼
       ┌────────────────────────────┐
       │ History Dashboard (Charts) │
       └────────────────────────────┘

✨ Features
🎤 Audio Analysis

Filler-word detection

Pause duration

Speech rate

Word count

Whisper-based transcript extraction (optional: API-based)

📝 Text Analysis

Grammar scoring (LanguageTool)

Coherence & readability scoring (Flesch-Kincaid, rule-based)

Highlighted feedback with real suggestions

🎥 Video Analysis

Face detection

Gaze stability

Posture alignment

Movement intensity

(Lightweight rule-based version implemented — replaceable with ML models later.)

🧩 Multimodal Fusion

Scores combined using weighted fusion:

40% language

40% audio

20% video

📊 Analytics Dashboard

Line chart (performance over time)

Radar chart (session comparison)

Session history table

Transcript viewer

CSV / PNG / JSON exports

🌐 Modern Frontend

Upload UI

Progress indicator

Result view with charts

Clean dashboard design

⚙️ Tech Stack
Layer	Technology
Backend	FastAPI, Python 3.12
Audio	Librosa, rule-based metrics
Text	LanguageTool, readability index
Video	OpenCV
Storage	SQLite
Frontend	HTML, CSS, Vanilla JS
Charts	Chart.js
Export	CSV, PNG, JSON
🚀 Setup Instructions
1. Clone the repository
git clone https://github.com/YOUR_USERNAME/fluentiq-multimodal.git
cd fluentiq-multimodal/backend

2. Setup Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

3. Install dependencies
pip install -r requirements.txt


If you don’t have the file yet, create one:

fastapi
uvicorn[standard]
python-multipart
language_tool_python
opencv-python
numpy
librosa

4. Run the backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000


Test:
🔗 http://127.0.0.1:8000/ping

🔗 http://127.0.0.1:8000/docs

5. Run the frontend

From the frontend/ folder:

Option A — VS Code Live Server

Right-click → Open with Live Server

Option B — Python static server
python3 -m http.server 5500


Then open:
🔗 http://127.0.0.1:5500/pages/index.html

🧪 API Endpoints
Health Check
GET /ping

Multimodal Analysis
POST /analyze/audio
file: UploadFile


Returns:

{
  "transcript": "...",
  "audio": {...},
  "text": {...},
  "video": {...},
  "fused": {...},
  "stats": {...}
}

History
GET /history/all
GET /history/summary

📈 Dashboard Features

Compare two sessions (radar)

View overall trajectory (line chart)

Inspect transcripts

Export JSON of any session

Export all sessions as CSV

📄 Citation (research paper)

If you use this system in academic work:

Gundu, Uday. *AI-Powered Multimodal Framework for Enhancing Public Speaking and Communication Skills*. 2025.

🤝 Contributing

Pull requests are welcome!
Suggestions for improving models (especially video posture or multimodal fusion) are encouraged.

⭐ Show your support

If this project helps your work or research, star the repository!