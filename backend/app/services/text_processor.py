# backend/app/services/text_processor.py
import re
from typing import Dict
import language_tool_python
import spacy
import nltk
from nltk.corpus import stopwords
from . import __name__  # silence unused import in some editors

# Load spaCy model once
nlp = spacy.load("en_core_web_sm")
lt_tool = language_tool_python.LanguageTool("en-US")
_stopwords = set(stopwords.words("english"))

# Simple list of discourse/signpost markers used to estimate structure/coherence
_SIGNPOSTS = [
    "first", "second", "third", "finally", "in conclusion", "to conclude",
    "to summarise", "to summarize", "firstly", "secondly", "next", "then",
    "in summary", "lastly", "to begin"
]


def _tokenize_sentences(text: str):
    return nltk.tokenize.sent_tokenize(text)


def analyze_text(transcript: str) -> Dict:
    """
    Analyze transcript with spaCy + LanguageTool and return:
    - grammar errors count
    - lexical richness (unique / total)
    - coherence estimate based on presence of signposts
    - readability proxy (short heuristic)
    - highlights: small suggestions and examples
    """
    text = transcript.strip()
    if not text:
        # empty response
        return {
            "transcript": "",
            "scores": {
                "grammar_score": 0,
                "lexical_richness": 0.0,
                "coherence_score": 0,
                "readability_score": 0.0,
            },
            "stats": {
                "word_count": 0,
                "sentence_count": 0,
                "avg_sentence_length": 0.0,
                "grammar_errors": 0,
            },
            "highlights": {},
        }

    # Basic tokenization & counts
    sentences = _tokenize_sentences(text)
    sentence_count = len(sentences) or 1

    words = re.findall(r"\w+", text)
    word_count = len(words) or 0
    unique_words = len(set(w.lower() for w in words))
    lexical_richness = (unique_words / word_count) if word_count else 0.0
    avg_sentence_len = word_count / sentence_count if sentence_count else 0.0

    # LanguageTool grammar checks
    matches = lt_tool.check(text)
    grammar_errors = len(matches)

    # Map grammar errors to score (simple heuristic)
    # fewer errors => higher score. We scale to 0-100.
    base_grammar = 95
    grammar_score = base_grammar - grammar_errors * 3
    if grammar_errors == 0:
        grammar_score = 98
    grammar_score = max(0, min(100, int(grammar_score)))

    # Coherence/structure heuristic: count signposts present / sentence_count
    lower = text.lower()
    signpost_hits = sum(1 for s in _SIGNPOSTS if s in lower)
    # coherence score: prefer at least 2 signposts in a longer talk; scale 0-100
    coherence_score = min(100, int((signpost_hits / max(1, sentence_count)) * 200))
    # small adjustment so short talks don't get penalized too hard
    if sentence_count < 3:
        coherence_score = max(coherence_score, 50)

    # Readability proxy: prefer avg sentence length ~12-20 words -> higher score
    if 10 <= avg_sentence_len <= 20:
        readability_score = 85.0
    elif avg_sentence_len < 10:
        readability_score = 70.0
    else:
        readability_score = 70.0
    # small penalty for many grammar errors
    readability_score = max(0.0, readability_score - min(20, grammar_errors * 0.5))

    # Highlights: show up to 3 notable suggestions (construct from LanguageTool matches)
    highlights = {}
    if matches:
        # pick top 3 matches
        for i, m in enumerate(matches[:3], start=1):
            message = m.message
            context = text[m.offset : m.offset + m.errorLength] if hasattr(m, "errorLength") else ""
            highlights[f"issue_{i}"] = f"{message} — Example: '{context}'"
    else:
        highlights["positive"] = "No obvious grammar/style issues detected."

    # Also compute POS distribution (optional small example highlight)
    doc = nlp(text)
    pos_counts = {}
    for token in doc:
        pos_counts[token.pos_] = pos_counts.get(token.pos_, 0) + 1
    # find if there's heavy noun/adj usage
    pos_suggestion = ""
    nouns = pos_counts.get("NOUN", 0)
    verbs = pos_counts.get("VERB", 0)
    if nouns > verbs * 2:
        pos_suggestion = "Try adding more verbs / action words to make sentences more dynamic."

    if pos_suggestion:
        highlights["style"] = pos_suggestion

    return {
        "transcript": text,
        "scores": {
            "grammar_score": grammar_score,
            "lexical_richness": round(lexical_richness, 3),
            "coherence_score": coherence_score,
            "readability_score": round(readability_score, 1),
        },
        "stats": {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_sentence_length": round(avg_sentence_len, 2),
            "grammar_errors": grammar_errors,
        },
        "highlights": highlights,
    }
