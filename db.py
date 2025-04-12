from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError
import os
from dotenv import load_dotenv,find_dotenv
import logging
from typing import List,Dict

logger = logging.getLogger(__name__)

# Loading enviroment variables
load_dotenv(find_dotenv())

# Replace with your own MongoDB connection string or load from a secure location.
# For example, you can store it in the environment or in st.secrets.
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
logger.info("Using MongoDB URI: %s", MONGODB_URI)


# Connect to the MongoDB server and select the database.
client = MongoClient(MONGODB_URI)
db = client["IRAG"]  # Replace 'chat_app' with your desired database name.
users_collection = db["users"]


def init_db():
    """
    Initialize the MongoDB database by creating unique indexes on:
    - oidc_user_id (unique identifier from your OAuth provider)
    - username (unique user-chosen username)
    """
    try:
        # Create a unique index for 'oidc_user_id'
        users_collection.create_index([("oidc_user_id", ASCENDING)], unique=True)
        # Create a unique index for 'username'
        users_collection.create_index([("username", ASCENDING)], unique=True)
        logger.info("Database initialized with unique indexes.")
    except Exception as e:
        logger.error("Error initializing database indexes: %s", e)


def get_user(oidc_user_id):
    """
    Retrieve a user document based on the unique OIDC user ID.
    Args:
        oidc_user_id (str): The unique user ID from the OIDC provider.
    Returns:
        dict or None: The user document if found, otherwise None.
    """
    try:
        user = users_collection.find_one({"oidc_user_id": oidc_user_id})
        if user:
            logger.info("User found for oidc_user_id: %s", oidc_user_id)
        else:
            logger.info("No user found for oidc_user_id: %s", oidc_user_id)
        return user
    except Exception as e:
        logger.error("Error retrieving user for oidc_user_id %s: %s", oidc_user_id, e)
        return None

def create_user(oidc_user_id, username, full_name,email, profession,picture,chat_ids=None):
    """
    Create a new user document in the users collection.
    Args:
        oidc_user_id (str): The unique user ID from the OIDC provider.
        username (str): A unique username chosen by the user.
        email (str): The user's email address.
        hashed_password (str): The hashed password (use empty string if not used).
        chat_ids (list, optional): A list of chat IDs for the user (default is empty list).
    Returns:
        The inserted document's ID if creation is successful.
    Raises:
        DuplicateKeyError if the oidc_user_id or username already exists.
    """
    if chat_ids is None:
        chat_ids = []
    user_data = {
        "oidc_user_id": oidc_user_id,
        "username": username,
        "full_name": full_name,
        "email": email,
        "profession": profession,
        "picture":picture,
        "chat_ids": chat_ids
    }
    try:
        result = users_collection.insert_one(user_data)
        logger.info("User created with oidc_user_id: %s", oidc_user_id)
        return result.inserted_id
    except DuplicateKeyError as e:
        logger.error("Duplicate key error when creating user: %s", e)
        raise
    except Exception as e:
        logger.error("Error creating user: %s", e)


def update_chat_ids(oidc_user_id, chat_ids):
    """
    Update the chat IDs list for a given user.
    Args:
        oidc_user_id (str): The unique user ID from the OIDC provider.
        chat_ids (list): The new list of chat IDs.
    Returns:
        int: The count of documents modified.
    """
    try:
        result = users_collection.update_one(
            {"oidc_user_id": oidc_user_id}, {"$set": {"chat_ids": chat_ids}}
        )
        logger.info("Updated chat_ids for oidc_user_id %s. Modified count: %d", oidc_user_id, result.modified_count)
        return result.modified_count
    except Exception as e:
        logger.error("Error updating chat_ids for oidc_user_id %s: %s", oidc_user_id, e)
        return 0
def get_chat_titles_and_ids(user_id: str) -> List[Dict[str, str]]:
    """
    Retrieve the list of chat titles along with their corresponding chat IDs for the given user.
    Each dictionary in the returned list has the keys "chat_id" and "title".

    :param user_id: The user ID whose chat histories are to be fetched.
    :return: A list of dictionaries, each containing 'chat_id' and 'title'.
    """
    chat_collection_name = os.getenv("CHAT_HISTORY_COLLECTION_NAME", "chat_history")
    chat_collection = db[chat_collection_name]
    logger.info("Getting chat titles and chat IDs for user: %s", user_id)
    
    result = chat_collection.find_one({"user_id": user_id})
    
    chats_list = []
    if result and "chats" in result:
        for chat_id, chat in result["chats"].items():
            chats_list.append({
                "chat_id": chat_id,
                "title": chat.get("title", "Untitled")
            })
        logger.info("Found %d chats for user %s", len(chats_list), user_id)
    else:
        logger.info("No chat history found for user: %s", user_id)
        
    return chats_list

        
# For testing purposes only: run this module to initialize the database.
# if __name__ == "__main__":
#     init_db()
