from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
import faiss
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS

class ProcessText:
    def __init__(self,chunk_size:int=300,chunk_overlap:int=5,embed_model:str = 'BAAI/bge-base-en',device='cpu'):
        self.chunk_size= chunk_size
        self.chunk_overlap= chunk_overlap
        self.embed_model = HuggingFaceEmbeddings(
            model_name=embed_model,
            model_kwargs= {'device':f'{device}'}
        )
        
        
    def splitter(self,document):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        chunks = text_splitter.split_text(document)
        return chunks
    
    def embeded_documents(self,chunks):
        return self.embed_model.embed_documents(chunks)
    