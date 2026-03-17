from backend.database.mongo_connection import db
from backend.config import COLLECTION_NAME

collection = db[COLLECTION_NAME]


def save_conversation(data):
    collection.insert_one(data)


from bson import ObjectId

def get_all_conversations():
    conversations = list(collection.find({}))
    # Convert ObjectIds to strings for JSON serialization in the API
    for conv in conversations:
        conv["_id"] = str(conv["_id"])
    return conversations

def update_conversation(doc_id, updated_data):
    # Remove the immutable _id from the payload if it exists
    if "_id" in updated_data:
        del updated_data["_id"]
        
    result = collection.update_one(
        {"_id": ObjectId(doc_id)},
        {"$set": updated_data}
    )
    return result.modified_count > 0

def delete_conversation(doc_id):
    result = collection.delete_one({"_id": ObjectId(doc_id)})
    return result.deleted_count > 0