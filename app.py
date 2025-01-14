from langchain_community.document_loaders import PyPDFLoader
from langchain_docling import DoclingLoader
import os
from tqdm import tqdm

def load_pdf_files(directory:str):
    pdf_files = []
    for filename in tqdm(os.listdir(directory)):
        if filename.endswith(".pdf"):
            filepath = os.path.join(directory, filename)
            pdf_files.append(os.path.abspath(filepath))
    return pdf_files

def load_pdf_pypdfloader(file_path: list):
    document=[]
    for path in tqdm(file_path):
        pages =[]
        loader = PyPDFLoader(path)
        for page in loader.load():
            pages.append(page)
        document.append(pages)
    return document

def load_pdf_docling(file_path_:list):
    """_summary_
    When to Use Docling
        1.Projects involving NLP pipelines where structured text extraction is needed.
        2.When working with a mix of file formats beyond just PDFs.
        3.In scenarios where document metadata is as important as the content itself.
        4.For extracting domain-specific data from unstructured documents, like legal, medical, or financial reports.
    """
    document=[]
    for path in tqdm(file_path_):
        loader = DoclingLoader(file_path=path)
        document.append(loader.load())
    return document


if __name__=="__main__":
    path=load_pdf_files("./PDF/")
    path = [p for p in path if os.path.isfile(p)]  # Validate paths
    document=load_pdf_pypdfloader(path)
    print(f"{document[0][0].metadata}\n")
    print(document[0][0].page_content,"\n")
    print("--------------------Docling------------------------\n")
    document2 = load_pdf_docling(path)
    for d in document2[0][:3]:
        print(f"- {d.page_content=}")