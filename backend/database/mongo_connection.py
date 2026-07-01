from pymongo import MongoClient

from backend.config import DATABASE_NAME, MONGO_URI

client = MongoClient(MONGO_URI)

db = client[DATABASE_NAME]
