from transformers import pipeline

sentiment_model = pipeline("sentiment-analysis")


def detect_emotion(text):

    result = sentiment_model(text)

    return result[0]