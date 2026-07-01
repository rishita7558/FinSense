from __future__ import annotations

import re

ENTITY_KEYWORDS = [
    "stock",
    "stocks",
    "mutual fund",
    "mutual funds",
    "etf",
    "gold",
    "real estate",
    "sip",
    "emi",
    "loan",
    "insurance",
    "tax",
    "budget",
    "expense",
    "income",
    "salary",
    "dividend",
    "cryptocurrency",
    "interest rate",
    "inflation",
    "portfolio",
    "asset allocation",
    "risk",
    "return",
    "investment",
    "invest",
]

INTENT_RULES = {
    "Investment Discussion": [
        "invest",
        "investment",
        "sip",
        "mutual fund",
        "stock",
        "portfolio",
        "etf",
    ],
    "Savings Goal": ["save", "savings", "emergency fund", "deposit"],
    "Budget Planning": ["budget", "expense", "income", "salary", "spend"],
    "Loan Discussion": ["loan", "emi", "interest rate", "refinance"],
    "Insurance Planning": ["insurance", "premium", "policy"],
    "Tax Planning": ["tax", "tds", "80c", "80d"],
    "Retirement Planning": ["retirement", "pension", "nps", "pf"],
    "Stock Market Discussion": ["stock", "nifty", "sensex", "bse", "nse"],
    "Mutual Fund Discussion": ["mutual fund", "sip", "nav"],
    "Portfolio Review": ["portfolio", "asset allocation", "diversification"],
    "Risk Assessment": ["risk", "loss", "volatility", "uncertain"],
}


def extract_entities(text: str):
    lowered = text.lower()
    seen = set()
    detected = []

    for keyword in ENTITY_KEYWORDS:
        if keyword in lowered and keyword not in seen:
            seen.add(keyword)
            detected.append({"entity": keyword})

    amount_matches = re.findall(
        r"(?:₹|rs\.?|inr)?\s?\d+(?:\.\d+)?\s?(?:lakh|lakhs|crore|crores|k|m|thousand|hundred|%)?",
        text,
        flags=re.IGNORECASE,
    )
    for amount in amount_matches:
        detected.append({"entity": amount.strip().lower(), "amount": amount.strip()})

    return detected


def detect_intent(text: str, previous_intent: str = "Financial Conversation"):
    lowered = text.lower()
    best_intent = previous_intent or "Financial Conversation"
    best_score = 0

    for intent, keywords in INTENT_RULES.items():
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score > best_score:
            best_score = score
            best_intent = intent

    return best_intent


def estimate_sentiment(text: str):
    positive = {
        "confident",
        "comfortable",
        "good",
        "great",
        "optimistic",
        "secure",
        "happy",
        "strong",
        "profit",
        "gain",
    }
    negative = {
        "worried",
        "concerned",
        "anxious",
        "fear",
        "risk",
        "loss",
        "stress",
        "hesitant",
        "uncertain",
        "debt",
    }

    words = re.findall(r"[a-zA-Z']+", text.lower())
    positive_hits = sum(1 for word in words if word in positive)
    negative_hits = sum(1 for word in words if word in negative)

    score = 50 + (positive_hits * 8) - (negative_hits * 10)
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


def estimate_risk(entities, sentiment):
    score = 0
    entity_keywords = [entity.get("entity", "") for entity in entities]

    if any(keyword in entity_keywords for keyword in ["loan", "emi"]):
        score += 30
    if any(keyword in entity_keywords for keyword in ["investment", "invest", "portfolio"]):
        score += 10
    if sentiment["label"] == "NEGATIVE":
        score += 20

    if score < 20:
        level = "Low Risk"
    elif score < 50:
        level = "Moderate Risk"
    else:
        level = "High Risk"

    return {"score": score, "risk_level": level}


def build_summary(text: str, intent: str):
    sentences = [
        sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()
    ]
    decisions = [
        sentence
        for sentence in sentences
        if any(
            keyword in sentence.lower()
            for keyword in ["should", "plan", "start", "increase", "reduce", "invest", "buy"]
        )
    ]
    risks = [
        sentence
        for sentence in sentences
        if any(
            keyword in sentence.lower()
            for keyword in ["risk", "loss", "debt", "interest", "inflation", "uncertain"]
        )
    ]

    topic_map = {
        "Investment Discussion": "Investments",
        "Savings Goal": "Savings",
        "Budget Planning": "Budgeting",
        "Loan Discussion": "Loans",
        "Insurance Planning": "Insurance",
        "Tax Planning": "Tax",
        "Retirement Planning": "Retirement",
        "Stock Market Discussion": "Markets",
        "Mutual Fund Discussion": "Mutual Funds",
        "Portfolio Review": "Portfolio",
        "Risk Assessment": "Risk",
    }

    return {
        "topic": topic_map.get(intent, "Financial Planning"),
        "intent": intent,
        "decisions": decisions[:3],
        "risks": risks[:3],
    }
