from document_loader import DocLoader
from textsplitter import ProcessText
from tqdm import tqdm
from uuid import uuid4
from langchain_core.documents import Document
import os
from scheme import Data,Extract_Text
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from typing import List, Dict, Any
from langchain_ollama.chat_models import ChatOllama
from langchain_core.output_parsers import PydanticOutputParser
import torch
import json
from datetime import datetime

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
        
        # Create base directory if it doesn't exist
        os.makedirs(base_dir, exist_ok=True)
        
        # Load existing history if it exists
        self._load_history()

    def _get_history_file_path(self) -> str:
        """
        Generate the file path for the user's chat history
        
        :return: Full path to the user's chat history JSON file
        """
        return os.path.join(self.base_dir, f"{self.user_id}_chat_history.json")

    def add_user_message(self, message: str,save_hist=False):
        """
        Add a user message to the chat history and save
        
        :param message: User's message content
        """
        self.history.append({
            "role": "human",
            "content": message,
            "timestamp": str(datetime.now())
        })

        if save_hist:
            self._save_history()

    def add_ai_message(self, message: str,save_hist=False):
        """
        Add an AI message to the chat history and save
        
        :param message: AI's message content
        """
        self.history.append({
            "role": "ai",
            "content": message,
            "timestamp": str(datetime.now())
        })

        if save_hist:
            self._save_history()

    def save_history(self):
        self._save_history()

    def _load_history(self):
        """
        Load chat history from JSON file
        """
        file_path = self._get_history_file_path()
        try:
            with open(file_path, 'r') as f:
                self.history = json.load(f)
        except FileNotFoundError:
            # Initialize empty history if file doesn't exist
            self.history = []

    def _save_history(self):
        """
        Save chat history to JSON file
        """
        file_path = self._get_history_file_path()
        with open(file_path, 'w') as f:
            json.dump(self.history, f, indent=4)

    def get_message_history(self, limit: int = None):
        """
        Convert history to LangChain message objects
        
        :param limit: Optional limit on number of messages to return
        :return: List of message objects
        """
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
        self.history = []
        file_path = self._get_history_file_path()
        
        # Remove the history file if it exists
        if os.path.exists(file_path):
            os.remove(file_path)

    @classmethod
    def list_user_histories(cls, base_dir: str = 'chat_histories') -> List[str]:
        """
        List all user chat history files
        
        :param base_dir: Directory containing chat history files
        :return: List of user IDs with chat histories
        """
        try:
            # Check if base directory exists
            if not os.path.exists(base_dir):
                os.makedirs(base_dir)
                return []

            # List all files in the directory
            files = os.listdir(base_dir)
            
            # Filter and extract user IDs
            user_histories = [
                filename.replace('_chat_history.json', '') 
                for filename in files 
                if filename.endswith('_chat_history.json')
            ]
            
            return user_histories
        
        except PermissionError:
            print(f"Permission denied to access directory: {base_dir}")
            return []
        
        except Exception as e:
            print(f"An error occurred while listing user histories: {e}")
            return []
    
    def get_history_size(self) -> int:
        """
        Get the number of messages in the chat history
        
        :return: Total number of messages in history
        """
        return len(self.history)

    def get_last_message(self,n_messages:int=2) -> Dict[str, str]:
        """
        Retrieve the most recent message from the history
        
        :return: Last message dictionary or None if history is empty
        """
        return self.history[-(n_messages)] if self.history else None

    def search_history(self, keyword: str, case_sensitive: bool = False) -> List[Dict[str, str]]:
        """
        Search through chat history for messages containing a specific keyword
        
        :param keyword: Keyword to search for
        :param case_sensitive: Whether the search should be case-sensitive
        :return: List of messages matching the keyword
        """
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
        if export_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = os.path.join(
                self.base_dir, 
                f"{self.user_id}_chat_history_export_{timestamp}.json"
            )
        
        with open(export_path, 'w') as f:
            json.dump(self.history, f, indent=4)
        
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
        # Create an instance of the class
        history_manager = cls(user_id, base_dir)
        
        # Read the imported file
        with open(import_path, 'r') as f:
            imported_history = json.load(f)
        
        # Set the history and save
        history_manager.history = imported_history
        history_manager._save_history()
        
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

        return filtered_history

    def analyze_history_stats(self) -> Dict[str, Any]:
        """
        Provide statistics about the chat history
        
        :return: Dictionary of chat history statistics
        """
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
        if len(self.history) <= compression_threshold:
            return self.history

        # Use an LLM to summarize older messages
        from langchain.chains.summarize import load_summarize_chain
        from langchain.docstore.document import Document

        llm = ChatOllama(model='phi3:mini',temperature = 0.5,request_timeout=360.0)
        
        # Convert older messages to Documents
        docs = [
            Document(page_content=msg['content'], metadata={'role': msg['role']}) 
            for msg in self.history[:len(self.history) - compression_threshold]
        ]

        # Summarize the documents
        chain = load_summarize_chain(llm, chain_type="map_reduce")
        summary = chain.run(docs)

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
        return self.history

    def detect_conversation_topics(self, top_n: int = 3):
        """
        Detect and extract main conversation topics
        
        :param top_n: Number of top topics to return
        :return: List of detected conversation topics
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import NMF

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
        
        return backup_path

    def restore_from_backup(self, backup_path: str):
        """
        Restore chat history from a backup file
        
        :param backup_path: Path to the backup file to restore
        """
        # Validate backup file exists
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        # Read backup file
        with open(backup_path, 'r') as f:
            backup_history = json.load(f)
        
        # Restore history
        self.history = backup_history
        self._save_history()

    def get_conversation_context(self, num_recent_messages: int = 5) -> List[Dict[str, str]]:
        """
        Retrieve recent conversation context
        
        :param num_recent_messages: Number of most recent messages to return
        :return: List of recent messages
        """
        return self.history[-num_recent_messages:]

    def anonymize_history(self) -> List[Dict[str, str]]:
        """
        Anonymize the chat history by removing potentially sensitive information
        
        :return: Anonymized chat history
        """
        import re
        
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
        
        return anonymized_history





class RAGChatAssistant:
    def __init__(self,user_id:str,dirpath:str="./PDF/"):
        # path to uploaded/local pdf's
        self.dirpath = dirpath
        # device agnostic code
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        # chat History manager
        self.chat_history_manager = ChatHistoryManager(user_id=user_id)
        #LLM
        self.llm = ChatOllama(model='phi3:mini',device=self.device,temperature = 0.5,request_timeout=360.0,format='json')
        # Pydantic output parser
        self.output_parser = PydanticOutputParser(pydantic_object=Data)
        # Structured LLM
        self.structured_llm = self.llm.with_structured_output(schema=Data)
        # Loading vectore store
        if os.path.exists("./faiss_index"):
            print("\n Skipping creating indexes as local index is present \n")
            self.vectore_store = self.load_vectors()
        else:
            print("\n Creating Vectore Index and Storing Locally \n")
            self.vectore_store = self.create_vectors()

    def create_vectors(self):
        document_loader = DocLoader(self.dirpath)
        document = document_loader.pypdf_loader()
        Textprocess = ProcessText(device=self.device)
        vector_store = Textprocess.vectore_store()
        for doc in tqdm(document):
            for page in doc:
                processed_text =  Textprocess.splitter(page.page_content)
                page_metadata = page.metadata
                doc_objects = [
                    Document(
                        page_content=chunk,
                        metadata={"id": str(uuid4()),
                                "source":page_metadata.get("source", "unknown"),
                                "category": page_metadata.get("category", "None"),
                                "page_number": page_metadata.get("page_number", -1)})
                    for chunk in processed_text
                ]
                vector_store.add_documents(doc_objects)
        vector_store.save_local("faiss_index")
        return vector_store

    def create_prompt_template(self):
        
        examples = [
            {
                "input": "Extract the following data from the provided PDF and present it in a table: "
                    "(1) Input Data: switching layer material (TYM_Class), Synthesis method (SM_Class), Top electrode (TE_Class), "
                    "Thickness of Top electrode (TTE in nm), Bottom electrode (BE_Class), Thickness of bottom electrode (TBE in nm), "
                    "Thickness of switching layer (TSL in nm); "
                    "(2) Output Data: Type of Switching (TSUB_Class), Endurance (Cycles) (EC), Retention Time (RT in seconds), "
                    "Memory Window (MW in V), No. of states (MRS_Class), Conduction mechanism type (CM_Class), "
                    "Resistive Switching mechanism (RSM_Class); "
                    "(3) Reference Information: Name of the paper, DOI, Year.",
                "output": {
                    "input_data": {
                        "switching_layer_material": "CuO Nanoparticles",
                        "synthesis_method": "Chemical",
                        "top_electrode": "Platinum",
                        "thickness_of_top_electrode": 10,
                        "bottom_electrode": "Gold",
                        "thickness_of_bottom_electrode": 20,
                        "thickness_of_switching_layer": 5000
                    },
                    "output_data": {
                        "type_of_switching": "Resistive",
                        "endurance_cycles": 50,
                        "retention_time": 10000,
                        "memory_window": 1.2,
                        "number_of_states": "Binary",
                        "conduction_mechanism_type": "Space-Charge Limited Conduction",
                        "resistive_switching_mechanism": "Filamentary"
                    },
                    "reference_information": {
                        "name_of_paper": "Switching Properties of CuO Nanoparticles",
                        "doi": "https://doi.org/10.1234/exampledoi",
                        "year": 2022,
                        "source":"C:\\Users\\Om Nagvekar\\OneDrive\\Documents\\KIT Assaignment & Notes& ISRO\\Shivaji University Nanoscience Dept. Projects\\IRP\\PDF\\1.pdf"
                    }
                }
            },

            {
                "input": "Analyze the switching characteristics of a material synthesized via chemical methods",
                "output": {
                    "material_type": "CuO Nanoparticles",
                    "synthesis_method": "Chemical",
                    "switching_type": "Resistive",
                    "endurance_cycles": 50,
                    "retention_time": 1000,
                    "memory_window": 1000,
                    "paper_details": {
                        "title": "Memristive Devices from CuO Nanoparticles",
                        "doi": "https://doi.org/10.3390/nano10091677",
                        "year": 2020,
                        "source":"8.pdf"
                    }
                }
            },
            {
                "input": "Provide retention time and endurance cycles for a material using p-type CuO",
                "output": {
                    "material_type": "p-type CuO",
                    "endurance_cycles": 18,
                    "retention_time": 10000,
                    "memory_window": 10000000,
                    "paper_details": {
                        "title": "Resistive switching memory effects in p-type h-CuI/CuO heterojunctions",
                        "doi": "https://doi.org/10.1063/5.0010839",
                        "year": 2020,
                        "source":"C:\\Users\\User\\OneDrive\\Documents\\KIT Assaignment & Notes& ISRO\\PDF\\8.pdf"
                    }
                }
            },
            {
                "input": "Details about switching layer with 5000 nm thickness and its mechanisms",
                "output": {
                    "switching_layer_thickness": 5000,
                    "conduction_mechanism": "Type 1",
                    "switching_mechanism": "Resistive",
                    "paper_details": {
                        "title": "Facile synthesis and nanoscale related physical properties of CuO nanostructures",
                        "doi": "https://doi.org/10.1016/j.apsusc.2019.144903",
                        "year": 2020,
                        "source":"C:\\Users\\User\\Documents\\KIT Assaignment & Notes& ISRO\\PDF\\8.pdf"
                    }
                }
            },
            {
                "input": "Analyze the performance of a resistive switching device with a switching layer synthesized via ALD and a top electrode of Pt.",
                "output": {
                    "material_type": "HfO2",
                    "synthesis_method": "Atomic Layer Deposition",
                    "switching_type": "Bipolar",
                    "endurance_cycles": 1_000_000,
                    "retention_time": 3600,
                    "memory_window": 2.5,
                    "paper_details": {
                        "title": "Resistive Switching in HfO2-Based Devices",
                        "doi": "https://doi.org/10.1016/j.jmatpro.2021.03.012",
                        "year": 2021,
                        "source":"4.pdf"
                    }
                }
            },
            {
                "input": "Provide details of a device with an 8 nm Al2O3 switching layer synthesized via Sol-Gel.",
                "output": {
                    "material_type": "Al2O3",
                    "switching_layer_thickness": 8,
                    "synthesis_method": "Sol-Gel",
                    "switching_type": "Unipolar",
                    "endurance_cycles": 500_000,
                    "retention_time": 7200,
                    "memory_window": 1.8,
                    "paper_details": {
                        "title": "Switching Characteristics of Al2O3 Layers",
                        "doi": "https://doi.org/10.5678/j.matsci.2020.045",
                        "year": 2020,
                        "source":"Switching.pdf"
                    }
                }
            },
            {
                "input": "Details of a resistive switching device using TiO2 synthesized via PLD, with a switching layer thickness of 15 nm.",
                "output": {
                    "material_type": "TiO2",
                    "switching_layer_thickness": 15,
                    "synthesis_method": "Pulsed Laser Deposition",
                    "switching_type": "Bipolar",
                    "endurance_cycles": 2_000_000,
                    "retention_time": 10_800,
                    "memory_window": 3.2,
                    "paper_details": {
                        "title": "Advances in TiO2-Based Resistive Switching",
                        "doi": "https://doi.org/10.9101/j.nano2020.112",
                        "year": 2020,
                        "source":"Resistive_Switching.pdf"
                    }
                }
            },
            {
                "input": "Analyze the switching mechanisms of a device with a 5000 nm thick CuO switching layer.",
                "output": {
                    "switching_layer_thickness": 5000,
                    "material_type": "CuO",
                    "conduction_mechanism": "Space Charge Limited Conduction",
                    "switching_mechanism": "Filamentary",
                    "paper_details": {
                        "title": "Synthesis and Applications of CuO Nanostructures",
                        "doi": "https://doi.org/10.1021/acsnano.2020.1234",
                        "year": 2020,
                        "source":"Synthesis_and_Applications_of_CuO_Nanostructures.pdf"
                    }
                }
            },
            {
                "input": "Provide endurance cycles and retention time for a resistive switching device with Au top electrode and Al2O3 switching layer.",
                "output": {
                    "material_type": "Al2O3",
                    "top_electrode": "Au",
                    "endurance_cycles": 750_000,
                    "retention_time": 5400,
                    "paper_details": {
                        "title": "Unipolar Switching in Al2O3 Devices",
                        "doi": "https://doi.org/10.1007/snano.2022.008",
                        "year": 2022,
                        "source":"paper.pdf"
                    }
                }
            },
        ]
        # Convert examples to message format
        example_messages = []
        for example in examples:
            example_messages.extend([
                HumanMessage(content=example["input"]),
                AIMessage(content=str(example["output"]))
            ])
        prompt_template = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=(
                    "You are a specialized AI algorithm for scientific data extraction, designed to analyze research papers. "
                    "Your role is to extract only the relevant information from the provided text. "
                    "If an attribute's value cannot be determined from the context, return 'null' for that attribute. "
                    "Rely solely on the given context to extract information and generate responses. "
                    "Do not use example content to influence the response's content."
                )),
                # Please see the how-to about improving performance with
                # reference examples.
                ("history:"),
                MessagesPlaceholder(variable_name='history',n_messages=2),
                ("examples"),
                MessagesPlaceholder(variable_name='examples',n_messages=1),
                ("human", "Query: {query}"),
                ("context:"),
                MessagesPlaceholder(variable_name='context'),
            ]
        ).partial(format_instructions=self.output_parser.get_format_instructions())
        
        return prompt_template,example_messages

    def load_vectors(self):
        Textprocess = ProcessText(device=self.device)
        vectore_store=Textprocess.load_vectors("faiss_index")
        return vectore_store
    
    def retrieve_context(self, query:str, top_k=5,simalirity=False):
        """Retrieve relevant documents from vector store"""
        if simalirity:
            return self.vectore_store.similarity_search(query,k=top_k)
        retriever = self.vectore_store.as_retriever(search_type="mmr", search_kwargs={"k": top_k})
        return retriever.invoke(query)
    
    def generate_response(self, query:str):
        """Generate response with RAG and chat history"""
        # Retrieve context
        context_docs = self.retrieve_context(query)
        context_messages = [
                HumanMessage(content=doc.page_content)
                for doc in context_docs
        ]

        # Create prompt template
        prompt_template, example_messages = self.create_prompt_template()
        # Prepare chain
        chain = prompt_template | self.llm
        
        try:
            response = chain.invoke({
                "history": self.chat_history_manager.get_message_history(limit=2),
                "examples": example_messages,
                "context":context_messages,
                "query": query
            })
            # parse the JSON response
            raw_response = json.loads(response.content)
            data= Data(data=[Extract_Text(**raw_response)])
            # parse the output by schema
            parser_output=self.output_parser.invoke(data.to_json_string())
            # Add messages to chat history
            self.chat_history_manager.add_user_message(query)
            self.chat_history_manager.add_ai_message(response.content)
            self.chat_history_manager.save_history()
            return {
                "response": response.content,
                "context_docs": context_docs,
                "validated_output":parser_output
            }
        except Exception as e:
            print(f"Error generating response: {e}")
            return {
                "response": "I'm sorry, I couldn't process your request.",
                "context_docs": []
            }
        
if __name__=="__main__":
    obj = RAGChatAssistant(user_id="abc_123")
    result = obj.generate_response("""
        Extract the following data from the provided PDF and present it in a table: 
        (1) Input Data: switching layer material (TYM_Class), Synthesis method (SM_Class), Top electrode (TE_Class), Thickness of Top electrode (TTE in nm), Bottom electrode (BE_Class), Thickness of bottom electrode (TBE in nm), Thickness of switching layer (TSL in nm); (2) Output Data: Type of Switching (TSUB_Class), Endurance (Cycles) (EC), Retention Time (RT in seconds), Memory Window (MW in V), No. of states (MRS_Class), Conduction mechanism type (CM_Class), Resistive Switching mechanism (RSM_Class);
        (3) Reference Information: Name of the paper, DOI, Year. Ensure all data is extracted in the specified categories and format
    """
    )
    print("\nAssistant:", result['response'])
    print("\nContext:",result["context_docs"])
    print("\nValidated_output:",result["validated_output"])
