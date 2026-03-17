financial_keywords = [
    "loan",
    "sip",
    "emi",
    "investment",
    "mutual fund",
    "interest",
    "insurance"
]

def detect_topic(text):

    topics = []

    for word in financial_keywords:
        if word in text.lower():
            topics.append(word)

    return topics