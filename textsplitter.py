from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
import faiss
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS

import logging
import warnings
warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

class ProcessText:
    def __init__(self,chunk_size:int=750,chunk_overlap:int=20,embed_model:str = 'BAAI/bge-base-en',device='cpu'):
        self.chunk_size= chunk_size
        self.chunk_overlap= chunk_overlap
        try:
            self.embed_model = HuggingFaceEmbeddings(
                model_name=embed_model,
                model_kwargs= {'device':f'{device}'}
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
        index = faiss.IndexFlatL2(len(self.embed_model.embed_query("hello world")))

        vector_store = FAISS(
            embedding_function=self.embed_model,
            index=index,
            docstore=InMemoryDocstore(),
            index_to_docstore_id={},
        )
        logger.info("FAISS vector store initialized successfully")
        return vector_store
    
    def load_vectors(self,dirpath:str):
        logger.info("Loading FAISS vectors from directory: %s", dirpath)
        try:
            vector_store = FAISS.load_local(
                folder_path=dirpath,
                embeddings= self.embed_model,
                allow_dangerous_deserialization=True
            )
            logger.info("Successfully loaded FAISS vector store from %s", dirpath)
            return vector_store
        except Exception as e:
            logger.error("Error loading FAISS vector store: %s", str(e), exc_info=True)
            raise