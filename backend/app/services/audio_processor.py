# backend/app/services/audio_processor.py
import os
import re
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

# Whisper is an optional heavy dependency; import lazily so the package
# can be imported by FastAPI/UVicorn even when Whisper isn't available
# (e.g., during static analysis or in lightweight environments).
_whisper_model: Optional[Any] = None

from ..models.api_models import AudioAnalysisResponse, AudioFluencyScores, AudioStats


def _get_whisper_model():
    """Lazily import and load the Whisper model, caching the instance.

    Raises RuntimeError with a helpful message if the `whisper` package
    is not installed.
    """
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model

    try:
        import whisper
    except ImportError as e:
        raise RuntimeError(
            "The 'whisper' package is required for audio transcription. "
            "Install it with 'pip install -U openai-whisper' or run the app in an "
            "environment that has Whisper available.") from e

    # Load model (this can be slow; done once per process)
    _whisper_model = whisper.load_model("base")
    return _whisper_model


def _compute_fluency_metrics(transcript: str, segments) -> Dict:
    """
    Compute words-per-minute, filler count, pause ratio, and fluency score
    from the transcript and Whisper segments.
    """
    words = re.findall(r"\w+", transcript)
    word_count = len(words)

    # Duration from first segment start to last segment end
    if segments:
        start_time = segments[0]["start"]
        end_time = segments[-1]["end"]
        total_duration = max(0.1, end_time - start_time)
    else:
        total_duration = 60.0  # fallback 1 min

    # Pause time = gaps between segments
    total_pause = 0.0
    for prev, curr in zip(segments, segments[1:]):
        gap = curr["start"] - prev["end"]
        if gap > 0:
            total_pause += gap

    # Simple metrics
    minutes = total_duration / 60.0
    wpm = word_count / minutes if minutes > 0 else 0.0
    pause_ratio = total_pause / total_duration if total_duration > 0 else 0.0

    # Filler words
    lower_words = [w.lower() for w in words]
    filler_count = sum(lower_words.count(f) for f in ["um", "uh", "like"])

    # Fluency score heuristic
    base_score = 90
    score = base_score
    score -= filler_count * 3
    score -= pause_ratio * 40  # more silence = lower fluency
    # penalise very low or very high speaking rate
    if wpm < 80:
        score -= 10
    elif wpm > 180:
        score -= 5

    score = int(max(0, min(100, score)))

    return {
        "word_count": word_count,
        "duration_seconds": total_duration,
        "total_pause_seconds": total_pause,
        "wpm": wpm,
        "filler_count": filler_count,
        "pause_ratio": pause_ratio,
        "fluency_score": score,
    }


async def analyze_audio_file(upload_file) -> AudioAnalysisResponse:
    """
    Save the uploaded file, run Whisper transcription,
    compute fluency metrics, and return a structured response.
    """
    suffix = Path(upload_file.filename).suffix or ".mp4"

    # Save to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        contents = await upload_file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        # Transcribe using Whisper (loaded lazily)
        model = _get_whisper_model()
        result = model.transcribe(tmp_path)
        transcript = result.get("text", "").strip()
        segments = result.get("segments", [])

        metrics = _compute_fluency_metrics(transcript, segments)

        scores = AudioFluencyScores(
            wpm=round(metrics["wpm"], 2),
            filler_count=metrics["filler_count"],
            pause_ratio=round(metrics["pause_ratio"], 3),
            fluency_score=metrics["fluency_score"],
        )

        stats = AudioStats(
            word_count=metrics["word_count"],
            duration_seconds=round(metrics["duration_seconds"], 2),
            total_pause_seconds=round(metrics["total_pause_seconds"], 2),
        )

        return AudioAnalysisResponse(
            transcript=transcript,
            scores=scores,
            stats=stats,
        )
    finally:
        # Clean up temp file
        try:
            os.remove(tmp_path)
        except OSError:
            pass
