import os

from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "armor")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "conversations")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
REDIS_URL = os.getenv("REDIS_URL", "")
STREAMING_WINDOW_SIZE = int(os.getenv("STREAMING_WINDOW_SIZE", "8"))
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
STT_LANGUAGE = os.getenv("STT_LANGUAGE", "")
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501").split(
        ","
    )
    if origin.strip()
]
