
import json
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage
from typing import List, Dict, Any
from langchain_ollama.chat_models import ChatOllama
import os
import logging
logger = logging.getLogger(__name__)

class ChatHistoryManager:
    def __init__(self, user_id: str, base_dir: str = 'chat_histories'):
        """
        Initialize ChatHistoryManager for a specific user
        
        :param user_id: Unique identifier for the user
        :param base_dir: Directory to store chat history files
        """
        self.user_id = user_id
        self.base_dir = base_dir
        self.history: List[Dict[str, Any]] = []
        logger.info("Initializing ChatHistoryManager for user %s", user_id)
        
        # Create base directory if it doesn't exist
        os.makedirs(base_dir, exist_ok=True)
        logger.info("Base directory '%s' ensured for chat histories.", base_dir)
        # Load existing history if it exists
        self._load_history()

    def _get_history_file_path(self) -> str:
        """
        Generate the file path for the user's chat history
        
        :return: Full path to the user's chat history JSON file
        """
        logger.debug("Chat history file path: %s", os.path.join(self.base_dir, f"{self.user_id}_chat_history.json"))
        return os.path.join(self.base_dir, f"{self.user_id}_chat_history.json")

    def add_user_message(self, message: str,save_hist=False):
        """
        Add a user message to the chat history and save
        
        :param message: User's message content
        """
        logger.info("Adding user message.")
        self.history.append({
            "role": "human",
            "content": message,
            "timestamp": str(datetime.now())
        })

        if save_hist:
            self._save_history()
            logger.info("Chat history saved after adding user message.")

    def add_ai_message(self, message: str,save_hist=False):
        """
        Add an AI message to the chat history and save
        
        :param message: AI's message content
        """
        logger.info("Adding AI message.")
        self.history.append({
            "role": "ai",
            "content": message,
            "timestamp": str(datetime.now())
        })

        if save_hist:
            self._save_history()
            logger.info("Chat history saved after adding AI message.")

    def save_history(self):
        logger.info("Saving chat history.")
        self._save_history()
        logger.info("Chat history saved.")

    def _load_history(self):
        """
        Load chat history from JSON file
        """
        file_path = self._get_history_file_path()
        logger.info("Loading chat history from %s", file_path)
        try:
            with open(file_path, 'r') as f:
                self.history = json.load(f)
                logger.info("Chat history loaded successfully. Total messages: %d", len(self.history))
        except FileNotFoundError as e:
            # Initialize empty history if file doesn't exist
            self.history = []
            logger.error("Error loading chat history: %s", e, exc_info=True)

    def _save_history(self):
        """
        Save chat history to JSON file
        """
        file_path = self._get_history_file_path()
        try:
            with open(file_path, 'w') as f:
                json.dump(self.history, f, indent=4)
            logger.info("Chat history saved to %s", file_path)
        except Exception as e:
            logger.error("Failed to save chat history to %s: %s", file_path, e, exc_info=True)

    def get_message_history(self, limit: int = None):
        """
        Convert history to LangChain message objects
        
        :param limit: Optional limit on number of messages to return
        :return: List of message objects
        """
        logger.info("Retrieving message history with limit: %s", limit)
        # If limit is specified, slice the history
        history_to_convert = self.history[-limit:] if limit else self.history
        return [
            HumanMessage(content=msg['content']) if msg['role'] == 'human' 
            else AIMessage(content=msg['content']) 
            for msg in history_to_convert
        ]

    def clear_history(self):
        """
        Clear the entire chat history for the user
        """
        logger.info("Clearing chat history for user %s", self.user_id)
        self.history = []
        file_path = self._get_history_file_path()
        
        # Remove the history file if it exists
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info("Chat history file %s removed.", file_path)
        else:
            logger.info("No chat history file found to remove.")

    @classmethod
    def list_user_histories(cls, base_dir: str = 'chat_histories') -> List[str]:
        """
        List all user chat history files
        
        :param base_dir: Directory containing chat history files
        :return: List of user IDs with chat histories
        """
        logger.info("Listing all user chat histories in directory: %s", base_dir)
        try:
            # Check if base directory exists
            if not os.path.exists(base_dir):
                os.makedirs(base_dir)
                logger.info("Base directory '%s' did not exist. Created new one.", base_dir)
                return []

            # List all files in the directory
            files = os.listdir(base_dir)
            
            # Filter and extract user IDs
            user_histories = [
                filename.replace('_chat_history.json', '') 
                for filename in files 
                if filename.endswith('_chat_history.json')
            ]
            logger.info("Found %d user chat histories.", len(user_histories))
            return user_histories
        
        except PermissionError:
            logger.error("Permission denied to access directory: %s", base_dir)
            print(f"Permission denied to access directory: {base_dir}")
            return []
        
        except Exception as e:
            logger.error("An error occurred while listing user histories: %s", e, exc_info=True)
            print(f"An error occurred while listing user histories: {e}")
            return []
    
    def get_history_size(self) -> int:
        """
        Get the number of messages in the chat history
        
        :return: Total number of messages in history
        """
        logger.info("Chat history size for user %s: %d", self.user_id, len(self.history))
        return len(self.history)

    def get_last_message(self,n_messages:int=2) -> Dict[str, str]:
        """
        Retrieve the most recent message from the history
        
        :return: Last message dictionary or None if history is empty
        """
        logger.info("Retrieving last %d message(s) for user %s", n_messages, self.user_id)
        return self.history[-(n_messages)] if self.history else None

    def search_history(self, keyword: str, case_sensitive: bool = False) -> List[Dict[str, str]]:
        """
        Search through chat history for messages containing a specific keyword
        
        :param keyword: Keyword to search for
        :param case_sensitive: Whether the search should be case-sensitive
        :return: List of messages matching the keyword
        """
        logger.info("Searching chat history for keyword '%s' (case_sensitive=%s)", keyword, case_sensitive)
        if not case_sensitive:
            keyword = keyword.lower()
        
        return [
            msg for msg in self.history 
            if (keyword in msg['content'].lower() if not case_sensitive 
                else keyword in msg['content'])
        ]

    def export_history(self, export_path: str = None):
        """
        Export chat history to a specified file
        
        :param export_path: Path to export the history file. 
                             If None, uses a default path with timestamp
        :return: Path of the exported file
        """
        logger.info("Exporting chat history for user %s", self.user_id)
        if export_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = os.path.join(
                self.base_dir, 
                f"{self.user_id}_chat_history_export_{timestamp}.json"
            )
        
        with open(export_path, 'w') as f:
            json.dump(self.history, f, indent=4)
        logger.info("Chat history exported to %s", export_path)
        return export_path

    @classmethod
    def import_history(cls, user_id: str, import_path: str, base_dir: str = 'chat_histories'):
        """
        Import chat history from a JSON file for a specific user
        
        :param user_id: User ID to associate with the imported history
        :param import_path: Path to the JSON file to import
        :param base_dir: Base directory for storing chat histories
        :return: ChatHistoryManager instance with imported history
        """
        logger.info("Importing chat history for user %s from %s", user_id, import_path)
        # Create an instance of the class
        history_manager = cls(user_id, base_dir)
        
        # Read the imported file
        with open(import_path, 'r') as f:
            imported_history = json.load(f)
        
        # Set the history and save
        history_manager.history = imported_history
        history_manager._save_history()
        logger.info("Chat history imported and saved for user %s", user_id)
        return history_manager

    def get_history_by_date_range(self, start_date: str = None, end_date: str = None) -> List[Dict[str, str]]:
        """
        Retrieve chat history within a specific date range
        
        :param start_date: Start date (inclusive) in ISO format
        :param end_date: End date (inclusive) in ISO format
        :return: List of messages within the specified date range
        """
        from datetime import datetime

        filtered_history = self.history
        logger.info("Filtering chat history for user %s by date range: %s to %s", self.user_id, start_date, end_date)

        if start_date:
            start = datetime.fromisoformat(start_date)
            filtered_history = [
                msg for msg in filtered_history 
                if datetime.fromisoformat(msg.get('timestamp', '')) >= start
            ]

        if end_date:
            end = datetime.fromisoformat(end_date)
            filtered_history = [
                msg for msg in filtered_history 
                if datetime.fromisoformat(msg.get('timestamp', '')) <= end
            ]
        logger.info("Filtered history contains %d messages", len(filtered_history))
        return filtered_history

    def analyze_history_stats(self) -> Dict[str, Any]:
        """
        Provide statistics about the chat history
        
        :return: Dictionary of chat history statistics
        """
        logger.info("Analyzing chat history statistics for user %s", self.user_id)
        return {
            'total_messages': len(self.history),
                        'human_messages': sum(1 for msg in self.history if msg['role'] == 'human'),
            'ai_messages': sum(1 for msg in self.history if msg['role'] == 'ai'),
            'first_message_timestamp': self.history[[0]]("https://python.langchain.com/docs/integrations/retrievers/asknews/")['timestamp'] if self.history else None,
            'last_message_timestamp': self.history[-1]['timestamp'] if self.history else None,
            'average_message_length': {
                'human': sum(len(msg['content']) for msg in self.history if msg['role'] == 'human') / 
                         max(sum(1 for msg in self.history if msg['role'] == 'human'), 1),
                'ai': sum(len(msg['content']) for msg in self.history if msg['role'] == 'ai') / 
                      max(sum(1 for msg in self.history if msg['role'] == 'ai'), 1)
            }
        }

    def compress_history(self, compression_threshold: int = 100):
        """
        Compress chat history by summarizing older messages
        
        :param compression_threshold: Number of messages after which compression begins
        :return: Compressed history
        """
        logger.info("Compressing chat history for user %s with threshold %d", self.user_id, compression_threshold)
        if len(self.history) <= compression_threshold:
            return self.history
        try:
            # Use an LLM to summarize older messages
            from langchain.chains.summarize import load_summarize_chain
            from langchain.docstore.document import Document

            llm = ChatOllama(model='phi3:mini',temperature = 0.5,request_timeout=360.0)
            
            # Convert older messages to Documents
            docs = [
                Document(page_content=msg['content'], metadata={'role': msg['role']}) 
                for msg in self.history[:len(self.history) - compression_threshold]
            ]
            logger.info("Summarizing %d messages for compression", len(docs))
            # Summarize the documents
            chain = load_summarize_chain(llm, chain_type="map_reduce")
            summary = chain.run(docs)
            logger.info("Summary obtained: %s", summary)
            # Keep the recent messages and add the summary
            compressed_history = [
                {
                    'role': 'system',
                    'content': f"Compressed history summary: {summary}",
                    'timestamp': self.history[compression_threshold-1]['timestamp']
                }
            ] + self.history[compression_threshold:]

            self.history = compressed_history
            self._save_history()
            logger.info("Chat history compressed and saved successfully")
            return self.history
        except Exception as e:
            logger.error("Error compressing chat history: %s", e, exc_info=True)
            return self.history

    def detect_conversation_topics(self, top_n: int = 3):
        """
        Detect and extract main conversation topics
        
        :param top_n: Number of top topics to return
        :return: List of detected conversation topics
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import NMF
        logger.info("Detecting conversation topics for user %s with top_n=%d", self.user_id, top_n)
        # Prepare text for topic modeling
        texts = [msg['content'] for msg in self.history]
        
        # Use TF-IDF and Non-Negative Matrix Factorization for topic extraction
        vectorizer = TfidfVectorizer(max_df=0.95, min_df=2, stop_words='english')
        tfidf = vectorizer.fit_transform(texts)
        
        # Extract topics
        nmf_model = NMF(n_components=top_n, random_state=42)
        nmf_output = nmf_model.fit_transform(tfidf)
        
        # Get feature names
        feature_names = vectorizer.get_feature_names_out()
        
        # Extract top words for each topic
        topics = []
        for topic_idx, topic in enumerate(nmf_model.components_):
            top_words = [feature_names[i] for i in topic.argsort()[:-10 - 1:-1]]
            topics.append({
                'topic_number': topic_idx + 1,
                'top_words': top_words
            })
        
        return topics

    def backup_history(self, backup_dir: str = None):
        """
        Create a backup of the current chat history
        
        :param backup_dir: Directory to store backup files
        :return: Path to the backup file
        """
        from datetime import datetime
        import shutil
        logger.info("Creating backup of chat history for user %s", self.user_id)
        # Use default backup directory if not specified
        if backup_dir is None:
            backup_dir = os.path.join(self.base_dir, 'backups')
        
        # Create backup directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{self.user_id}_backup_{timestamp}.json"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Copy the current history file to backup location
        original_file = self._get_history_file_path()
        shutil.copy2(original_file, backup_path)
        logger.info("Backup created at %s", backup_path)
        return backup_path

    def restore_from_backup(self, backup_path: str):
        """
        Restore chat history from a backup file
        
        :param backup_path: Path to the backup file to restore
        """
        logger.info("Restoring chat history for user %s from backup %s", self.user_id, backup_path)
        # Validate backup file exists
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        # Read backup file
        with open(backup_path, 'r') as f:
            backup_history = json.load(f)
        
        # Restore history
        self.history = backup_history
        self._save_history()
        logger.info("Chat history restored successfully from %s", backup_path)

    def get_conversation_context(self, num_recent_messages: int = 5) -> List[Dict[str, str]]:
        """
        Retrieve recent conversation context
        
        :param num_recent_messages: Number of most recent messages to return
        :return: List of recent messages
        """
        logger.info("Retrieving conversation context for user %s, last %d messages", self.user_id, num_recent_messages)
        return self.history[-num_recent_messages:]

    def anonymize_history(self) -> List[Dict[str, str]]:
        """
        Anonymize the chat history by removing potentially sensitive information
        
        :return: Anonymized chat history
        """
        import re
        logger.info("Anonymizing chat history for user %s", self.user_id)
        anonymized_history = []
        for msg in self.history:
            anonymized_msg = msg.copy()
            
            # Remove email addresses
            anonymized_msg['content'] = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL REDACTED]', anonymized_msg['content'])
            
            # Remove phone numbers
            anonymized_msg['content'] = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE REDACTED]', anonymized_msg['content'])
            
            # Remove potential personal identifiers (this is a simple example and might need more sophisticated NER)
            anonymized_msg['content'] = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[NAME REDACTED]', anonymized_msg['content'])
            
            anonymized_history.append(anonymized_msg)
        logger.info("Anonymization complete for user %s", self.user_id)
        return anonymized_history

