from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError
import os
from dotenv import load_dotenv,find_dotenv
import logging
from typing import List,Dict,Any
from dynamic_schema import DynamicGenSchema
# import pickle
# import io
# import hmac
# import hashlib
# import base64
# import json
# from gemini_scheme import Data_Objects
# code to securely exchange pickle file for future refrence
# pickled_schema = pickle.dumps(Data_Objects)
# signature = sign_pickle_data(pickled_schema)
# Store as a dictionary with signature and pickled data
# schema_package = {"sig": signature, "data": pickled_schema}

logger = logging.getLogger(__name__)

# Loading enviroment variables
load_dotenv(find_dotenv())


default_field_descriptions = {
    "numeric_value": (
        "A numeric value extracted from the research paper. This may represent a measured "
        "parameter such as thickness, retention time, or endurance cycles. Stored as a string "
        "to accommodate diverse numeric formats or additional formatting (e.g., including units)."
    ),
    "switching_layer_material": (
        "The material used in the switching layer of the device. For example, it could be a metal "
        "oxide such as TiO2 or HfO2, or another compound known for resistive switching behavior."
    ),
    "synthesis_method": (
        "The method or process used to synthesize or fabricate the material. Common examples include "
        "chemical vapor deposition (CVD), sol–gel processes, sputtering, or thermal evaporation."
    ),
    "top_electrode": (
        "The material of the top electrode in the device. This typically includes metals like platinum, "
        "gold, or other conductive materials used to form the top contact."
    ),
    "top_electrode_thickness": (
        "The thickness of the top electrode. Typically measured in nanometers (nm), this field supports both "
        "numerical values and string representations (if units or additional comments are included)."
    ),
    "bottom_electrode": (
        "The material of the bottom electrode, which is another key component in the device structure. "
        "Common materials might include metals or metal oxides depending on the device design."
    ),
    "bottom_electrode_thickness": (
        "The thickness of the bottom electrode, measured in nanometers (nm). As with the top electrode, "
        "this field can be either a numeric value or a string if additional context is needed."
    ),
    "switching_layer_thickness": (
        "The thickness of the switching layer, which is critical for device performance. "
        "Typically expressed in nanometers (nm), this parameter influences the device's electrical characteristics."
    ),
    "switching_type": (
        "The mode or type of switching observed in the device. Examples include bipolar or unipolar switching, "
        "or other specific classifications used to describe the resistive behavior."
    ),
    "endurance_cycles": (
        "The number of switching cycles the device can endure before failure. This integer value indicates "
        "the durability and reliability of the device under repeated use."
    ),
    "retention_time": (
        "The duration for which the device can retain its resistive state, usually measured in seconds. "
        "This field can be provided as an integer or a string, especially if additional units or qualifiers are included."
    ),
    "memory_window": (
        "The voltage difference between the high-resistance state and low-resistance state of the device, "
        "commonly known as the memory window. It is typically measured in volts (V) and may be expressed "
        "as a numerical value or a string with units."
    ),
    "num_states": (
        "The number of distinct resistive states that the device can exhibit. This may be represented as a "
        "string to allow for descriptive categorizations such as 'binary', 'multilevel', etc."
    ),
    "conduction_mechanism": (
        "A description of the conduction mechanism observed in the device. Examples include filamentary conduction, "
        "interface conduction, or other theories that explain how electrical current passes through the device."
    ),
    "resistive_switching_mechanism": (
        "A detailed explanation of the resistive switching mechanism. This field may describe processes such as "
        "oxygen vacancy migration, redox reactions, or the formation and rupture of conductive filaments."
    ),
    "additional_properties": (
        "Additional information or notes that do not fit into the predefined fields but are relevant to the user's query. "
        "This field is used for capturing any extra details from the research paper."
    ),
    "paper_name": "The title or name of the research paper from which the data is extracted.",
    "source": (
        "The filename of the PDF document from which the data was extracted. Examples might include "
        "'Memory_characteristic.pdf' or simply '1.pdf'."
    ),
}


# --- Safe Unpickler Section ---
# ALLOWED_MODULE_PREFIXES = ("builtins", "pydantic", "typing", "json","gemini_scheme","dynamic_schema")

# class SafeUnpickler(pickle.Unpickler):
#     def find_class(self, module, name):
#         if any(module.startswith(prefix) for prefix in ALLOWED_MODULE_PREFIXES):
#             return super().find_class(module, name)
#         else:
#             msg = f"Unsafe class requested: {module}.{name}"
#             logger.error(msg)
#             raise pickle.UnpicklingError(msg)

# def safe_load(data: bytes) -> object:
#     """
#     Safely unpickle data from a bytes object using SafeUnpickler.
#     """
#     file_like_object = io.BytesIO(data)
#     return SafeUnpickler(file_like_object).load()
# # --- End of Safe Unpickler Section ---

# # --- Pickle Signing Helpers ---
# def sign_pickle_data(pickle_data: bytes) -> str:
#     """
#     Create an HMAC-SHA256 signature for the given pickle data using the secret key.
    
#     Returns:
#         The signature as a base64-encoded string.
#     """
#     secret_key = os.getenv("PICKLE_SECRET_KEY")
#     if secret_key is None:
#         raise ValueError("PICKLE_SECRET_KEY is not set in the environment")
#     secret_key_bytes = secret_key.encode()
#     signature = hmac.new(secret_key_bytes, pickle_data, hashlib.sha256).digest()
#     return base64.b64encode(signature).decode()

# def verify_pickle_data(pickle_data: bytes, signature: str) -> bool:
#     """
#     Verify that the provided signature matches the expected signature for the pickle data.
#     """
#     expected_sig = sign_pickle_data(pickle_data)
#     return hmac.compare_digest(expected_sig, signature)
# --- End of Pickle Signing Helpers ---

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
        "Pydantic_Schema": [default_field_descriptions],
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

def get_pydantic_models(oidc_user_id: str) -> List[type]:
    """
    Retrieve and rebuild dynamic Pydantic models from stored JSON schemas.
    """
    try:
        user = users_collection.find_one(
            {"oidc_user_id": oidc_user_id}, {"Pydantic_Schema": 1}
        )
        if not user or "Pydantic_Schema" not in user:
            logger.info("No schemas for user %s", oidc_user_id)
            return []

        models = []
        for idx, schema in enumerate(user["Pydantic_Schema"]):
            if not isinstance(schema, dict):
                logger.warning(
                    "Skipping invalid schema at index %d for user %s: %r",
                    idx, oidc_user_id, schema
                )
                continue
            try:
                model = DynamicGenSchema.create_model(schema)
                models.append(model)
            except Exception as e:
                logger.error(
                    "Failed to build model from schema at index %d for user %s: %s",
                    idx, oidc_user_id, e, exc_info=True
                )
        logger.info(
            "Rebuilt %d dynamic model(s) for user %s",
            len(models), oidc_user_id
        )
        return models
    except Exception as e:
        logger.error(
            "Error fetching models for user %s: %s",
            oidc_user_id, e, exc_info=True
        )
        return []



def update_pydantic_models(oidc_user_id, pydantic_model: List[Dict[str,Any]])->int:
    """
    Update the Pydantic models list for a given user.
    The models are pickled, signed, and stored.
    """
    try:
        result = users_collection.update_one(
            {"oidc_user_id": oidc_user_id}, {"$set": {"Pydantic_Schema": pydantic_model}}
        )
        logger.info("Updated Pydantic models for oidc_user_id %s. Modified count: %d", oidc_user_id, result.modified_count)
        return result.modified_count
    except Exception as e:
        logger.error("Error updating Pydantic models for oidc_user_id %s: %s", oidc_user_id, e)
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

def delete_chat_id(oidc_user_id: str, chat_id: str) -> int:
    """
    Delete a specific chat_id from the 'chat_ids' array of a user's document in the users collection.

    The function uses the $pull operator to remove the chat_id from the array.
    
    Args:
        oidc_user_id (str): The unique OIDC user ID of the user.
        chat_id (str): The chat ID to be removed from the array.

    Returns:
        int: The number of documents modified (0 if no modification occurred).
    """
    try:
        result = users_collection.update_one(
            {"oidc_user_id": oidc_user_id},
            {"$pull": {"chat_ids": chat_id}}
        )
        logger.info("Deleted chat_id '%s' for user '%s'. Modified count: %d", 
                    chat_id, oidc_user_id, result.modified_count)
        return result.modified_count
    except Exception as e:
        logger.error("Error deleting chat_id '%s' for user '%s': %s", 
                     chat_id, oidc_user_id, e)
        return 0

def delete_chat_session(user_id: str, chat_id: str) -> int:
    """
    Delete a specific chat session (its chat_id and its chat_history content) from the user's document in the MongoDB collection.

    The function uses the $unset operator to remove the field corresponding to the chat_id from the "chats" dictionary.
    
    Args:
        user_id (str): The unique user identifier.
        chat_id (str): The chat session ID to be deleted.
    
    Returns:
        int: The number of documents modified (0 if no modifications occur).
    """
    try:
        chat_collection_name = os.getenv("CHAT_HISTORY_COLLECTION_NAME", "chat_history")
        chat_collection = db[chat_collection_name]
        result = chat_collection.update_one(
            {"user_id": user_id},
            {"$unset": {f"chats.{chat_id}": ""}}
        )
        logger.info("Deleted chat session '%s' for user '%s'. Modified count: %d", chat_id, user_id, result.modified_count)
        return result.modified_count
    except Exception as e:
        logger.error("Error deleting chat session '%s' for user '%s': %s", chat_id, user_id, e, exc_info=True)
        return 0

def delete_pydantic_model(oidc_user_id: str, schema: Dict[str,Any]) -> int:
    """
    Delete a specific Pydantic model from the user's document.
    """
    try:
        result = users_collection.update_one(
            {"oidc_user_id": oidc_user_id},
            {"$pull": {"Pydantic_Schema": schema}}
        )
        logger.info("Deleted Pydantic model for user '%s'. Modified count: %d", oidc_user_id, result.modified_count)
        return result.modified_count
    except Exception as e:
        logger.error("Error deleting Pydantic model for user '%s': %s", oidc_user_id, e, exc_info=True)
        return 0

        
# For testing purposes only: run this module to initialize the database.
# if __name__ == "__main__":
#     init_db()
