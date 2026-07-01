def compute_risk_score(entities, sentiment):

    score = 0
    # Map the list of dictionaries back into a simple list of keywords
    entity_keywords = [e.get("entity", "") for e in entities]

    if "loan" in entity_keywords:
        score += 30

    if "emi" in entity_keywords:
        score += 20

    if "investment" in entity_keywords:
        score -= 10

    if sentiment["label"] == "NEGATIVE":
        score += 20

    if score < 20:
        risk = "Low Risk"

    elif score < 50:
        risk = "Moderate Risk"

    else:
        risk = "High Risk"

    return {"score": score, "risk_level": risk}
