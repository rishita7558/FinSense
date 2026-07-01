import re


_POSITIVE = {
    "confident", "comfortable", "good", "great", "positive", "excited", "optimistic",
    "secure", "sure", "profit", "gain", "increase", "growth", "happy", "strong",
}
_NEGATIVE = {
    "worried", "concerned", "anxious", "fear", "risk", "loss", "debt", "stress",
    "hesitant", "uncertain", "bad", "decline", "drop", "negative", "pressure",
}


def detect_emotion(text):
    words = re.findall(r"[a-zA-Z']+", text.lower())
    positive_hits = sum(1 for word in words if word in _POSITIVE)
    negative_hits = sum(1 for word in words if word in _NEGATIVE)

    score = 50 + (positive_hits * 10) - (negative_hits * 12)
    score = max(0, min(100, score))

    if score >= 65:
        label = "POSITIVE"
    elif score <= 35:
        label = "NEGATIVE"
    else:
        label = "NEUTRAL"

    return {
        "label": label,
        "score": score,
        "positive_hits": positive_hits,
        "negative_hits": negative_hits,
    }