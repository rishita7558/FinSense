import re


_INTENT_RULES = {
    "Investment Discussion": ["invest", "investment", "mutual fund", "sip", "stock", "portfolio", "etf"],
    "Savings Goal": ["save", "savings", "goal", "emergency fund", "deposit"],
    "Budget Planning": ["budget", "expense", "income", "salary", "spend", "monthly"],
    "Loan Discussion": ["loan", "emi", "interest rate", "refinance", "mortgage"],
    "Insurance Planning": ["insurance", "premium", "policy", "term plan", "health insurance"],
    "Tax Planning": ["tax", "80c", "80d", "tds", "return"],
    "Retirement Planning": ["retirement", "pension", "nps", "pf", "epf"],
    "Stock Market Discussion": ["stock", "nifty", "sensex", "bse", "nse", "share"],
    "Mutual Fund Discussion": ["mutual fund", "sip", "fund", "nav"],
    "Portfolio Review": ["portfolio", "asset allocation", "diversification", "returns"],
    "Financial Advice": ["should i", "advice", "recommend", "suggest"],
    "Risk Assessment": ["risk", "volatile", "safe", "return", "loss"],
}


def _split_sentences(text):
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]
    return sentences or [text.strip()]


def _find_intent(text):
    text_lower = text.lower()
    best_intent = "Financial Conversation"
    best_score = 0

    for intent, keywords in _INTENT_RULES.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > best_score:
            best_score = score
            best_intent = intent

    return best_intent


def _find_topic(text):
    intent = _find_intent(text)
    if intent == "Investment Discussion":
        return "Investments"
    if intent in {"Loan Discussion", "Risk Assessment"}:
        return "Credit and Risk"
    if intent in {"Budget Planning", "Savings Goal"}:
        return "Budget and Savings"
    if intent in {"Insurance Planning", "Tax Planning"}:
        return "Protection and Tax"
    if intent == "Retirement Planning":
        return "Retirement"
    return "General Financial Planning"


def generate_summary(text):
    sentences = _split_sentences(text)
    topic = _find_topic(text)
    intent = _find_intent(text)

    decisions = []
    risks = []
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(keyword in sentence_lower for keyword in ["should", "plan", "start", "buy", "invest", "increase", "reduce"]):
            decisions.append(sentence)
        if any(keyword in sentence_lower for keyword in ["risk", "loss", "debt", "emi", "interest", "inflation", "uncertain"]):
            risks.append(sentence)

    return {
        "topic": topic,
        "intent": intent,
        "decisions": decisions[:3],
        "risks": risks[:3],
    }