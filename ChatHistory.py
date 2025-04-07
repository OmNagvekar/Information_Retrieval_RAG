import json
import os
import logging
from datetime import datetime
from uuid import uuid4
from typing import List, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage

logger = logging.getLogger(__name__)

class ChatHistoryManager:
    def __init__(self, user_id: str, base_dir: str = 'chat_histories'):
        """
        Initialize ChatHistoryManager for a specific user with support for multiple chats.

        :param user_id: Unique identifier for the user.
        :param base_dir: Directory to store the chat history file.
        """
        self.user_id = user_id
        self.base_dir = base_dir
        # This will store all chats for the current user.
        self.chats: Dict[str, Dict[str, Any]] = {}
        # Active chat id for the current session.
        self.current_chat_id: str = None
        
        logger.info("Initializing ChatHistoryManager for user %s", user_id)
        
        os.makedirs(base_dir, exist_ok=True)
        logger.info("Base directory '%s' ensured for chat histories.", base_dir)
        self._load_history()

    def _get_history_file_path(self) -> str:
        """
        Generate the file path for the chat history.
        :return: Full path to the chat history JSON file.
        """
        path = os.path.join(self.base_dir, "chathistory.json")
        logger.debug("Chat history file path: %s", path)
        return path

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
        Add an Citation message to the active chat session.
        
        :param message: AI's message content.
        :param save_hist: Whether to immediately save the history.
        """
        if not self.current_chat_id:
            logger.error("No active chat session. Create or load a chat first.")
            raise ValueError("No active chat session. Create or load a chat first.")
        logger.info("Adding Citation message to chat %s.", self.current_chat_id)
        self.chats[self.current_chat_id]["history"].append({
            "role": "ai",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        if save_hist:
            self._save_history()

    def get_message_history(self, limit: int = None) -> List[Any]:
        """
        Retrieve message history (converted to LangChain message objects) from the active chat.
        
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
            history_to_convert = history[-limit:] if limit else history
            logger.info("Retrieving message history from chat %s with limit %s", self.current_chat_id, limit)
            return [
                HumanMessage(content=msg['content']) if msg['role'] == 'human'
                else AIMessage(content=msg['content'])
                for msg in history_to_convert
            ]
        except Exception as e:
            logger.error("Error retrieving message history: %s", e, exc_info=True)
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
        Load chat history from the JSON file.
        """
        file_path = self._get_history_file_path()
        logger.info("Loading chat history from %s", file_path)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # Expecting a structure: { user_id: { chat_id: { ... } } }
                    self.chats = data.get(self.user_id, {})
                    logger.info("Loaded %d chats for user %s", len(self.chats), self.user_id)
            except Exception as e:
                logger.error("Failed to load chat history from %s: %s", file_path, e, exc_info=True)
                self.chats = {}
        else:
            self.chats = {}
            self._save_history()

    def _save_history(self):
        """
        Save the current chats (for all users) to the JSON file.
        """
        file_path = self._get_history_file_path()
        try:
            # Read any existing data to avoid overwriting other users' histories
            data = {}
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
            data[self.user_id] = self.chats
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
            logger.info("Chat history saved to %s", file_path)
        except Exception as e:
            logger.error("Failed to save chat history to %s: %s", file_path, e, exc_info=True)

    def export_history(self, export_path: str = None):
        """
        Export the current user's chat history to a specified file.
        
        :param export_path: If None, uses a default filename with a timestamp.
        :return: The path to the exported file.
        """
        logger.info("Exporting chat history for user %s", self.user_id)
        if export_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = os.path.join(self.base_dir, f"{self.user_id}_chat_history_export_{timestamp}.json")
        with open(export_path, 'w') as f:
            json.dump({self.user_id: self.chats}, f, indent=4)
        logger.info("Chat history exported to %s", export_path)
        return export_path

    @classmethod
    def list_user_histories(cls, base_dir: str = 'chat_histories') -> List[str]:
        """
        List all user IDs that have chat histories in the JSON file.
        
        :param base_dir: Directory containing the chat history file.
        :return: List of user IDs.
        """
        file_path = os.path.join(base_dir, "chathistory.json")
        logger.info("Listing all user chat histories in file: %s", file_path)
        if not os.path.exists(file_path):
            os.makedirs(base_dir, exist_ok=True)
            return []
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            user_ids = list(data.keys())
            logger.info("Found %d user chat histories.", len(user_ids))
            return user_ids
        except Exception as e:
            logger.error("An error occurred while listing user histories: %s", e, exc_info=True)
            return []

    def get_history_size(self) -> int:
        """
        Get the number of messages in the active chat session.
        """
        if not self.current_chat_id:
            return 0
        size = len(self.chats[self.current_chat_id]["history"])
        logger.info("Chat history size for chat %s of user %s: %d", self.current_chat_id, self.user_id, size)
        return size

    # Additional helper methods (like search, backup, restore, etc.) can be adapted similarly.

# Example usage:
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    user_id = "user_1234"
    manager = ChatHistoryManager(user_id)
    # Create a new chat session
    new_chat_id = manager.create_new_chat("My First Chat 2")
    
    manager.add_user_message("Hello, how are you?", save_hist=True)
    manager.add_ai_message("I'm doing great, thank you!", save_hist=True)
    
    manager.add_user_message("Hello, how are you? 2", save_hist=True)
    manager.add_ai_message("I'm doing great, thank you! 2", save_hist=True)
    # Load the chat session by id and retrieve history
    
    loaded_chat = manager.load_chat(new_chat_id)
    
    print("Title:",loaded_chat['title'])
    print("Loaded Chat:", loaded_chat)
    message_history = manager.get_message_history()
    for msg in message_history:
        print(msg)
        
    print(manager.get_history_size(),"\n")
    print(manager.list_user_histories(),"\n")
    print(manager.export_history(),"\n")
    print(manager.get_message_history(limit=2),"\n")
