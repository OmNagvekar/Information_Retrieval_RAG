from document_loader import DocLoader
from textsplitter import ProcessText
from tqdm import tqdm
from uuid import uuid4
from langchain_core.documents import Document
import os
from scheme import Data
from general_schema import Genral_Data
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def create_vectors():
    document_loader = DocLoader("./PDF/")
    document = document_loader.pypdf_loader()
    Textprocess = ProcessText()
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

def load_vectors():
    Textprocess = ProcessText()
    vectore_store=Textprocess.load_vectors("faiss_index")
    return vectore_store
    
def main():
    if os.path.exists("./faiss_index"):
        print("\n Skipping creating indexes as local index is present \n")
        vectore_store = load_vectors()
    else:
        print("\n Creating Vectore Index and Storing Locally \n")
        vectore_store = create_vectors()
    prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert extraction algorithm. "
            "Only extract relevant information from the text. "
            "If you do not know the value of an attribute asked to extract, "
            "return null for the attribute's value.",
        ),
        # Please see the how-to about improving performance with
        # reference examples.
        # MessagesPlaceholder('examples'),
        ("human", "{text}"),
    ]
)
        
if __name__=="__main__":
    main()
