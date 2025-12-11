# backend/app/models/api_models.py
from pydantic import BaseModel
from typing import Dict
from pydantic import BaseModel
from typing import Dict, Optional


# --- existing audio models (keep these if already present) ---
class AudioFluencyScores(BaseModel):
    wpm: float
    filler_count: int
    pause_ratio: float
    fluency_score: int

class AudioStats(BaseModel):
    word_count: int
    duration_seconds: float
    total_pause_seconds: float

class AudioAnalysisResponse(BaseModel):
    transcript: str
    scores: AudioFluencyScores
    stats: AudioStats

# --- new text models ---
class TextScores(BaseModel):
    grammar_score: int        # 0-100 derived from grammar errors
    lexical_richness: float   # unique_words / total_words
    coherence_score: int      # 0-100 heuristic for signposts/structure
    readability_score: float  # basic readability proxy (0-100)

class TextStats(BaseModel):
    word_count: int
    sentence_count: int
    avg_sentence_length: float
    grammar_errors: int

class TextAnalysisResponse(BaseModel):
    transcript: str
    scores: TextScores
    stats: TextStats
    highlights: Dict[str, str]  # e.g., {"suggestion1": "...", "example": "..."}

class FusionScores(BaseModel):
    fluency: int
    grammar: int
    coherence: int
    readability: float
    overall: int

class MultimodalStats(BaseModel):
    word_count: int
    duration_seconds: float
    total_pause_seconds: float
    sentence_count: int
    avg_sentence_length: float
    grammar_errors: int

class MultimodalAnalysisResponse(BaseModel):
    transcript: str
    audio: AudioAnalysisResponse
    text: TextAnalysisResponse
    fused: FusionScores
    stats: MultimodalStats
    notes: Optional[Dict[str, str]] = None

class VideoScores(BaseModel):
    posture_score: int      # 0-100
    gaze_score: int         # 0-100 (eye-contact quality)
    movement_score: int     # 0-100 (excessive movement/fidgeting)

class VideoStats(BaseModel):
    duration_seconds: float
    frames_analyzed: int
    avg_shoulder_tilt_deg: float
    percent_eye_contact: float

class MultimodalAnalysisResponse(BaseModel):
    transcript: str
    audio: AudioAnalysisResponse
    text: TextAnalysisResponse
    video: Optional[Dict] = None   # video dict if present; else None
    fused: FusionScores
    stats: MultimodalStats
    notes: Optional[Dict[str, str]] = None