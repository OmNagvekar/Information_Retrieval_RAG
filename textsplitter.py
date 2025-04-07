from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import chromadb
from chromadb.config import Settings
import os
import logging
import warnings
warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)
# Define your cache directory and ensure it exists
cache_dir = "./model_cache"
os.makedirs(cache_dir, exist_ok=True)

class ProcessText:
    def __init__(self,chunk_size:int=750,chunk_overlap:int=20,embed_model:str = 'BAAI/bge-base-en',device='cpu',persist_directory: str = "./chroma_db"):
        self.chunk_size= chunk_size
        self.chunk_overlap= chunk_overlap
        self.persist_directory = persist_directory
        # Initialize Chroma client
        os.makedirs(persist_directory, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(path=persist_directory,settings=Settings(anonymized_telemetry=False))
        try:
            self.embed_model = HuggingFaceEmbeddings(
                model_name=embed_model,
                model_kwargs= {'device':f'{device}'},
                # cache_folder = cache_dir
            )
            logger.info("Successfully initialized embedding model: %s", embed_model)
        except Exception as e:
            logger.error("Error initializing embedding model: %s", str(e), exc_info=True)
            raise

    def splitter(self,document):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        chunks = text_splitter.split_text(document)
        return chunks
    
    def embeded_documents(self,chunks):
        try:
            embeddings = self.embed_model.embed_documents(chunks)
            return embeddings
        except Exception as e:
            logger.error("Error embedding documents: %s", str(e), exc_info=True)
            raise
    
    def vectore_store(self):

        vector_store = Chroma(
                collection_name="my_collection",
                client = self.chroma_client,
                embedding_function=self.embed_model,
                persist_directory=self.persist_directory
            )
        logger.info("Chroma vector store initialized successfully")
        return vector_store
    
    def load_vectors(self):
        logger.info("Loading Chroma vectors from directory: %s", self.persist_directory)
        try:
            vector_store = Chroma(
                client = self.chroma_client,
                collection_name="my_collection",
                embedding_function=self.embed_model,
                persist_directory=self.persist_directory
            )
            logger.info("Successfully loaded Chroma vector store from %s", self.persist_directory)
            return vector_store
        except Exception as e:
            logger.error("Error loading FAISS vector store: %s", str(e), exc_info=True)
            raise