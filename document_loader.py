from langchain_community.document_loaders import PyPDFLoader
# from langchain_docling import DoclingLoader
from langchain_unstructured import UnstructuredLoader
import os
from tqdm import tqdm

class DocLoader:
    """sumary_line
        Recommendations
            For your specific use case:
            1. Primary Choice: Use UnstructuredLoader with strategy="hi_res".
                This loader handles unstructured text and mixed content effectively.
                It ensures you don't miss data embedded in images or tables.
                Use it to generate raw text and then apply an NLP pipeline for entity-value extraction.
            2. Alternative for Text-Heavy PDFs: Use PyPDFLoader.
                Suitable if your documents are simple and text-heavy.
                Faster but may miss complex layouts or image-based data.
            3. Future Expansion: Consider DoclingLoader for structured data extraction or multi-format scenarios.
                This can be particularly useful for metadata-driven pipelines or multi-format documents.
    """
    
    def __init__(self,dirpath:str):
        self.dirpath=dirpath

    def load_pdf_files(self):
        """sumary_line
        Simple and Fast document loader
        Return: return list of path of pdf's in specific directory
        """
        
        pdf_files = []
        for filename in tqdm(os.listdir(self.dirpath)):
            if filename.endswith(".pdf"):
                filepath = os.path.join(self.dirpath, filename)
                pdf_files.append(os.path.abspath(filepath))
        return pdf_files

    def load_pdf_pypdfloader(self,file_path: list):
        document=[]
        for path in tqdm(file_path):
            pages =[]
            loader = PyPDFLoader(path)
            for page in loader.lazy_load():
                pages.append(page)
            document.append(pages)
        return document

    def unstructured_loading(self,file_path: list):
        """_summary_
        better than simple pdf loader as it also includes images and other content which uses
        tesseract OCR so it takes more time than simple pdf loader
        """
        document=[]
        for path in tqdm(file_path):
            pages=[]
            loader = UnstructuredLoader(file_path=path, strategy="hi_res")
            for page in loader.lazy_load():
                pages.append(page)
            document.append(pages)
        return document

    def load_pdf_docling(self,file_path_:list):
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
    obj = DocLoader("./PDF/")
    path=obj.load_pdf_files()
    path = [p for p in path if os.path.isfile(p)]  # Validate paths
    document=obj.load_pdf_pypdfloader(path)
    print(f"{document[0][0].metadata}\n")
    print(f"category: {document[0][0].metadata.get('category')}\n")
    print(document[0][0].page_content,"\n")
    # print("--------------------Docling------------------------\n")
    # document2 = load_pdf_docling(path)
    # for d in document2[0][:3]:
    #     print(f"- {d.page_content=}")
    print("\n--------------------------Unstructred loader-----------------------\n")
    document2 = obj.unstructured_loading(path)
    print(f"{document2[0][0].metadata}\n")
    for i in range(len(document2[0])):
        print(f"category: {document2[0][i].metadata.get('category')}\n")
        print(document2[0][i].page_content,"\n")