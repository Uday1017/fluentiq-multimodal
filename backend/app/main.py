# backend/app/main.py

import tempfile
import os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict

# --- Database initialization ---
from .db.database import init_db

# --- Services ---
from .services.audio_processor import analyze_audio_file
from .services.text_processor import analyze_text
from .services.video_processor import analyze_video_file
from .services.fusion import fuse_audio_text_video
from .services.history_service import save_session, get_all_sessions, get_summary

# --- Models ---
from .models.api_models import (
    AudioAnalysisResponse,
    TextAnalysisResponse,
    MultimodalAnalysisResponse,
    MultimodalStats,
)

# -------------------------------
# FastAPI App Setup
# -------------------------------

app = FastAPI(title="FluentIQ Multimodal Backend")

# Initialize database on startup
init_db()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/ping")
def ping():
    return {"message": "Backend is running!"}


# ------------------------------------------------------
#               MAIN MULTIMODAL PIPELINE
# ------------------------------------------------------
@app.post("/analyze/audio", response_model=MultimodalAnalysisResponse)
async def analyze_audio(file: UploadFile = File(...)):

    # Save uploaded file once to reuse for all processors
    suffix = Path(file.filename).suffix or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        # Wrapper so we can re-read file multiple times
        class _SimpleUpload:
            def __init__(self, path, filename):
                self.path = path
                self.filename = filename
                self.file = open(path, "rb")

            async def read(self):
                self.file.seek(0)
                return self.file.read()

            def close(self):
                try:
                    self.file.close()
                except:
                    pass

        ufile = _SimpleUpload(tmp_path, file.filename)

        # --- 1) AUDIO ANALYSIS ---
        audio_result = await analyze_audio_file(ufile)
        audio_dict = audio_result.dict()

        # --- 2) TEXT ANALYSIS ---
        transcript = audio_dict.get("transcript", "")
        text_result = analyze_text(transcript)
        text_dict = text_result if isinstance(text_result, dict) else text_result

        # --- 3) VIDEO ANALYSIS ---
        try:
            video_result = await analyze_video_file(ufile)
        except Exception:
            video_result = None
        finally:
            ufile.close()

        # --- 4) FUSION ---
        fused = fuse_audio_text_video(audio_dict, text_dict, video_result)

        # --- 5) STATISTICS MODEL ---
        stats = MultimodalStats(
            word_count=audio_dict["stats"]["word_count"],
            duration_seconds=audio_dict["stats"]["duration_seconds"],
            total_pause_seconds=audio_dict["stats"]["total_pause_seconds"],
            sentence_count=text_dict["stats"]["sentence_count"],
            avg_sentence_length=text_dict["stats"]["avg_sentence_length"],
            grammar_errors=text_dict["stats"]["grammar_errors"],
        )

        # --- 6) BUILD RESPONSE ---
        response = {
            "transcript": transcript,
            "audio": audio_dict,
            "text": text_dict,
            "video": video_result,
            "fused": fused,
            "stats": stats.dict(),
            "notes": {
                "pipeline": "audio -> text -> video fusion",
                "storage": "session saved to SQLite history",
            },
        }

        # --- 7) SAVE SESSION TO DB ---
        save_session(
            transcript=transcript,
            fused=fused,
            audio=audio_dict,
            text=text_dict,
            video=video_result
        )

        return response

    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


# ------------------------------------------------------
#                   HISTORY ENDPOINTS
# ------------------------------------------------------

@app.get("/history/all")
def history_all():
    """Return list of all past analysis sessions."""
    return get_all_sessions()


@app.get("/history/summary")
def history_summary():
    """Return aggregated improvement summary (averages)."""
    return get_summary()
