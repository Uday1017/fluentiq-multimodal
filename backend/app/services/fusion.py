# backend/app/services/fusion.py
from typing import Dict, Optional


def fuse_audio_text(audio: Dict, text: Dict) -> Dict:
    """
    Simple weighted fusion between audio fluency and text grammar/coherence.
    Returns a dict with component scores and an overall 0-100 score.

    audio: dict returned by AudioAnalysisResponse (scores + stats)
    text: dict returned by analyze_text(...) (scores + stats)
    """

    # Extract numeric parts
    fluency_score = audio["scores"].get("fluency_score", audio["scores"].get("fluency", 0))
    grammar_score = text["scores"].get("grammar_score", 0)
    coherence = text["scores"].get("coherence_score", 0)
    readability = text["scores"].get("readability_score", 0.0)

    # Weights (tunable). Since we don't have video yet, allocate to audio/text:
    w_fluency = 0.40
    w_grammar = 0.40
    w_coherence = 0.10
    w_readability = 0.10

    fused_fluency = int(round(float(fluency_score) if fluency_score is not None else 0))
    fused_grammar = int(round(float(grammar_score) if grammar_score is not None else 0))
    fused_coherence = int(round(float(coherence) if coherence is not None else 0))
    fused_readability = float(round(float(readability) if readability is not None else 0.0, 1))

    overall = int(round(
        fused_fluency * w_fluency +
        fused_grammar * w_grammar +
        fused_coherence * w_coherence +
        fused_readability * w_readability
    ))

    overall = max(0, min(100, overall))

    return {
        "fluency": fused_fluency,
        "grammar": fused_grammar,
        "coherence": fused_coherence,
        "readability": fused_readability,
        "overall": overall,
    }


def fuse_audio_text_video(audio: Dict, text: Dict, video: Optional[Dict] = None) -> Dict:
    """
    Fuse audio + text + optional video into final scores.
    If video is present, it gets a weight; otherwise fusion uses only audio+text.
    Returns a dict with component scores and an overall 0-100 score.
    """

    # --- extract audio fluency score robustly ---
    fluency_score = 0
    if isinstance(audio, dict) and "scores" in audio:
        s = audio["scores"]
        fluency_score = s.get("fluency_score") or s.get("fluency") or s.get("wpm") or 0

    # --- extract text scores ---
    grammar_score = 0
    coherence = 0
    readability = 0.0
    if isinstance(text, dict) and "scores" in text:
        grammar_score = text["scores"].get("grammar_score", 0)
        coherence = text["scores"].get("coherence_score", 0)
        readability = text["scores"].get("readability_score", 0.0)

    # --- extract video scores if present ---
    posture = 0
    gaze = 0
    movement = 0
    if video and isinstance(video, dict) and "scores" in video:
        v_scores = video["scores"]
        posture = v_scores.get("posture_score", v_scores.get("posture", 0))
        gaze = v_scores.get("gaze_score", v_scores.get("gaze", 0))
        movement = v_scores.get("movement_score", v_scores.get("movement", 0))

    # --- decide weights ---
    if video:
        # Use audio 30%, text 40%, video 30% (split)
        w_audio = 0.30
        w_text = 0.40
        # video split
        w_posture = 0.14
        w_gaze = 0.10
        w_movement = 0.06
    else:
        # No video: audio 40%, text 60%
        w_audio = 0.40
        w_text = 0.60
        w_posture = w_gaze = w_movement = 0.0

    fused_fluency = int(round(float(fluency_score))) if fluency_score is not None else 0
    fused_grammar = int(round(float(grammar_score))) if grammar_score is not None else 0
    fused_coherence = int(round(float(coherence))) if coherence is not None else 0
    fused_readability = float(round(float(readability), 1)) if readability is not None else 0.0

    overall = int(round(
        fused_fluency * w_audio +
        fused_grammar * w_text +
        posture * w_posture +
        gaze * w_gaze +
        movement * w_movement
    ))

    overall = max(0, min(100, overall))

    return {
        "fluency": fused_fluency,
        "grammar": fused_grammar,
        "coherence": fused_coherence,
        "readability": fused_readability,
        "video": {"posture": int(posture), "gaze": int(gaze), "movement": int(movement)} if video else None,
        "overall": overall,
    }
