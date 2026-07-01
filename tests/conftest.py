import os


os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
os.environ.setdefault("DATABASE_NAME", "armor")
os.environ.setdefault("COLLECTION_NAME", "conversations")
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("STREAMING_WINDOW_SIZE", "8")
os.environ.setdefault("WHISPER_MODEL", "base")
