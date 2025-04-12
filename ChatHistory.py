import os
import logging
from datetime import datetime
from uuid import uuid4
from typing import List, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from pymongo import MongoClient
from dotenv import find_dotenv,load_dotenv
logger = logging.getLogger(__name__)
# Loading enviroment variables
load_dotenv(find_dotenv())

class ChatHistoryManager:
    def __init__(self, user_id: str):
        """
        Initialize ChatHistoryManager for a specific user with support for multiple chats.
        Chat histories are stored in a MongoDB collection. The structure of the document is:
        {
            "user_id": <user_id>,
            "chats": {
                chat_id1: {
                    "title": <title>,
                    "timestamp": <creation timestamp>,
                    "history": [ { message dict }, ... ]
                },
                chat_id2: { ... }
            }
        }
        
        :param user_id: Unique identifier for the user.
        """
        self.user_id = user_id
        self.mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        self.db_name = os.getenv("DATABASE_NAME", "IRAG")
        self.collection_name = os.getenv("CHAT_HISTORY_COLLECTION_NAME", "chat_history")
        self.current_chat_id: str = None
        self.chats: Dict[str, Dict[str, Any]] = {}

        logger.info("Initializing ChatHistoryManager for user %s", user_id)
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]

        self._load_history()

    def init_db(self):
        """
        Initialize the MongoDB database by creating unique indexes on
        (But only Run one time when intializing the database):
        - oidc_user_id (unique identifier from your OAuth provider)
        - username (unique user-chosen username)
        """
        try:
            # Create a unique index for 'oidc_user_id'
            self.collection.create_index([("user_id")], unique=True)
            # Create a unique index for 'username'
            self.collection.create_index([("chat_id")], unique=True)
            logger.info("Database initialized with unique indexes.")
        except Exception as e:
            logger.error("Error initializing database indexes: %s", e)

    def create_new_chat(self, title: str = "New Chat") -> str:
        """
        Create a new chat session with a unique chat id.
        
        :param title: Title for the chat session.
        :return: The newly generated chat id.
        """
        chat_id = str(uuid4())
        chat_session = {
            "title": title,
            "timestamp": datetime.now().isoformat(),
            "history": []
        }
        self.chats[chat_id] = chat_session
        self.current_chat_id = chat_id
        logger.info("New chat created with id %s and title '%s'", chat_id, title)
        self._save_history()
        return chat_id

    def load_chat(self, chat_id: str) -> Dict[str, Any]:
        """
        Load a chat session by its chat id.
        
        :param chat_id: The unique chat id.
        :return: The chat session dictionary.
        """
        if chat_id in self.chats:
            self.current_chat_id = chat_id
            logger.info("Chat with id %s loaded.", chat_id)
            return self.chats[chat_id]
        else:
            logger.error("Chat id %s not found.", chat_id)
            raise ValueError(f"Chat id {chat_id} not found.")

    def add_user_message(self, message: str, save_hist: bool = False):
        """
        Add a user message to the active chat session.
        
        :param message: User's message content.
        :param save_hist: Whether to immediately save the history.
        """
        if not self.current_chat_id:
            logger.error("No active chat session. Create or load a chat first.")
            raise ValueError("No active chat session. Create or load a chat first.")
        logger.info("Adding user message to chat %s.", self.current_chat_id)
        self.chats[self.current_chat_id]["history"].append({
            "role": "human",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        if save_hist:
            self._save_history()

    def add_ai_message(self, message: str, save_hist: bool = False):
        """
        Add an AI message to the active chat session.
        
        :param message: AI's message content.
        :param save_hist: Whether to immediately save the history.
        """
        if not self.current_chat_id:
            logger.error("No active chat session. Create or load a chat first.")
            raise ValueError("No active chat session. Create or load a chat first.")
        logger.info("Adding AI message to chat %s.", self.current_chat_id)
        self.chats[self.current_chat_id]["history"].append({
            "role": "ai",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        if save_hist:
            self._save_history()

    def add_citation_message(self, message: str, save_hist: bool = False):
        """
        Add a citation message to the active chat session.
        
        :param message: Citation message content.
        :param save_hist: Whether to immediately save the history.
        """
        if not self.current_chat_id:
            logger.error("No active chat session. Create or load a chat first.")
            raise ValueError("No active chat session. Create or load a chat first.")
        logger.info("Adding citation message to chat %s.", self.current_chat_id)
        self.chats[self.current_chat_id]["history"].append({
            "role": "citation",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        if save_hist:
            self._save_history()

    def get_message_history(self, limit: int = None) -> List[Any]:
        """
        Retrieve message history (converted to LangChain message objects) from the active chat.
        Only messages with role 'human' or 'ai' are returned.
        
        :param limit: Optional limit on the number of messages to return.
        :return: List of message objects.
        """
        try:
            if not self.current_chat_id:
                logger.error("No active chat session. Create or load a chat first.")
                return []
            history = self.chats[self.current_chat_id].get("history", [])
            if not history:
                logger.info("No messages in the active chat session.")
                return []
            # Filter only messages with role 'human' or 'ai'
            valid_history = [msg for msg in history if msg["role"] in ("human", "ai")]
            history_to_convert = valid_history[-limit:] if limit else valid_history
            logger.info("Retrieving message history from chat %s with limit %s", self.current_chat_id, limit)
            return [
                HumanMessage(content=msg['content']) if msg['role'] == 'human'
                else AIMessage(content=msg['content'])
                for msg in history_to_convert
            ]
        except Exception as e:
            logger.error("Error retrieving message history: %s", e, exc_info=True)
            return []

    def get_citation_message(self, limit: int = 1) -> List[Any]:
        """
        Retrieve citation message(s) (converted to AIMessage objects) from the active chat.
        
        If limit == 1, the method searches backwards through the complete history until
        the first message with role 'citation' is found and returns it. If no citation message is found,
        an empty list is returned.
        
        For limit > 1, the last 'limit' citation messages are returned.
        
        :param limit: Number of citation messages to return.
        :return: List of citation message objects.
        """
        try:
            if not self.current_chat_id:
                logger.error("No active chat session. Create or load a chat first.")
                return []
            history = self.chats[self.current_chat_id].get("history", [])
            if not history:
                logger.info("No messages in the active chat session.")
                return []
            # For limit == 1, search backwards until the first citation message is found
            if limit == 1:
                for msg in reversed(history):
                    if msg.get("role") == "citation":
                        logger.info("Citation message found in chat %s", self.current_chat_id)
                        return [AIMessage(content=msg["content"])]
                logger.info("No citation message found in chat %s", self.current_chat_id)
                return []
            else:
                # For limit > 1, filter all citation messages and return the last 'limit' citations
                citation_msgs = [msg for msg in history if msg.get("role") == "citation"]
                if not citation_msgs:
                    logger.info("No citation messages found in chat %s", self.current_chat_id)
                    return []
                return [AIMessage(content=msg["content"]) for msg in citation_msgs[-limit:]]
        except Exception as e:
            logger.error("Error retrieving citation message: %s", e, exc_info=True)
            return []

    def clear_history(self):
        """
        Clear the history of the active chat session.
        """
        if not self.current_chat_id:
            logger.error("No active chat session to clear.")
            return
        logger.info("Clearing chat history for chat %s of user %s", self.current_chat_id, self.user_id)
        self.chats[self.current_chat_id]["history"] = []
        self._save_history()

    def _load_history(self):
        """
        Load chat history for the user from MongoDB.
        """
        logger.info("Loading chat history for user %s from MongoDB", self.user_id)
        doc = self.collection.find_one({"user_id": self.user_id})
        if doc:
            self.chats = doc.get("chats", {})
            logger.info("Loaded %d chats for user %s", len(self.chats), self.user_id)
        else:
            self.chats = {}
            self._save_history()  # Create a new document for this user

    def _save_history(self):
        """
        Save the current chats (for the user) to MongoDB.
        """
        logger.info("Saving chat history for user %s to MongoDB", self.user_id)
        self.collection.update_one(
            {"user_id": self.user_id},
            {"$set": {"chats": self.chats}},
            upsert=True
        )
        logger.info("Chat history saved to MongoDB.")

    def export_history(self) -> Dict[str, Any]:
        """
        Export the current user's chat history.
        
        :return: The user's chat history data.
        """
        logger.info("Exporting chat history for user %s", self.user_id)
        return {"user_id": self.user_id, "chats": self.chats}

    @classmethod
    def list_user_histories(cls) -> List[str]:
        """
        List all user IDs that have chat histories in MongoDB.
        
        :return: List of user IDs.
        """
        mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        db_name = os.getenv("DATABASE_NAME", "IRAG")
        collection_name = os.getenv("CHAT_HISTORY_COLLECTION_NAME", "chat_history")
        client = MongoClient(mongo_uri)
        db = client[db_name]
        collection = db[collection_name]
        user_ids = collection.distinct("user_id")
        logger.info("Found %d user chat histories.", len(user_ids))
        return user_ids

    def get_history_size(self) -> int:
        """
        Get the number of messages in the active chat session.
        """
        if not self.current_chat_id:
            return 0
        size = len(self.chats[self.current_chat_id]["history"])
        logger.info("Chat history size for chat %s of user %s: %d", self.current_chat_id, self.user_id, size)
        return size

# Example usage:
if __name__ == "__main__":
    user_id = "104363079999574289592"
    manager = ChatHistoryManager(user_id)    
    # Create a new chat session
    new_chat_id = manager.create_new_chat("My First Chat 2")
    print("chat_id ",new_chat_id,"\n=================\n")
    manager.add_citation_message("Citation: Reference XYZ")
    manager.add_user_message("Hello, how are you?")
    manager.add_ai_message("I'm doing great, thank you!", save_hist=True)
    
    
    manager.add_citation_message("Citation: Reference ABC ==============2")
    manager.add_user_message("Hello, how are you =====2?")
    manager.add_ai_message("I'm doing great, thank you! =========2", save_hist=True)
    
    # # Load the chat session by id and retrieve history
    loaded_chat = manager.load_chat(new_chat_id)
    print("Title:", loaded_chat['title'],"\n============================\n")
    print("Loaded Chat:", loaded_chat,"\n================================\n")
    
    message_history = manager.get_message_history()
    for msg in message_history:
        print(msg,"\n#=======================#\n")
    
    citation_message = manager.get_citation_message(limit=1)
    print("Citation Message:", citation_message,"\n==============================\n")
        
    print("History size:", manager.get_history_size(),"\n===========================\n")
    print("User IDs with histories:", ChatHistoryManager.list_user_histories(),"\n=======================\n")
    print("Exported History:", manager.export_history(),"\n===========================\n")
    print("Last 2 messages:", manager.get_message_history(limit=2),"\n===================\n")
