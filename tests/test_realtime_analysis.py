from backend.realtime.analysis import (
    build_summary,
    detect_intent,
    estimate_risk,
    estimate_sentiment,
    extract_entities,
)


def test_detect_intent_prefers_investment_discussion():
    text = "I want to invest in a mutual fund SIP for my long-term portfolio."
    assert detect_intent(text) == "Investment Discussion"


def test_extract_entities_detects_financial_terms_and_amounts():
    text = "I plan to invest 5000 rupees in a SIP and review my portfolio."
    entities = extract_entities(text)
    labels = {entity["entity"] for entity in entities}

    assert "sip" in labels
    assert any("5000" in label for label in labels)


def test_sentiment_and_risk_work_together():
    text = "I am worried about a loan and the interest rate, but I want to reduce the risk."
    sentiment = estimate_sentiment(text)
    entities = extract_entities(text)
    risk = estimate_risk(entities, sentiment)

    assert sentiment["label"] == "NEGATIVE"
    assert risk["risk_level"] in {"Moderate Risk", "High Risk"}


def test_build_summary_returns_topic_and_decisions():
    text = "We should start a SIP and invest monthly. The risk is manageable."
    summary = build_summary(text, "Investment Discussion")

    assert summary["topic"] == "Investments"
    assert summary["intent"] == "Investment Discussion"
    assert summary["decisions"]
