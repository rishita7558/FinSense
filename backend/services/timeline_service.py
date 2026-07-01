from datetime import datetime


def generate_timeline(transcript, entities, emotion, risk):

    formatted_entities = []
    for e in entities:
        keyword = e.get("entity", "")
        amount = e.get("amount", "")
        if amount:
            formatted_entities.append(f"{keyword} ({amount})")
        else:
            formatted_entities.append(keyword)

    timeline_event = {
        "time": str(datetime.now()),
        "transcript": transcript,
        "entities": ", ".join(formatted_entities) if formatted_entities else "None",
        "emotion": emotion["label"],
        "risk_score": risk["score"],
        "risk_level": risk["risk_level"],
    }
    return timeline_event
