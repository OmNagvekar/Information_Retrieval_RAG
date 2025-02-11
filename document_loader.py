from langchain_community.document_loaders import PyPDFLoader
from langchain_unstructured import UnstructuredLoader
from langchain_core.documents import Document
import os
from tqdm import tqdm
import re
import logging
import sys
from datetime import datetime
# Configure logging
TODAY_DATE = datetime.now().strftime("%Y-%m-%d")
LOG_DIR='Logs'
os.makedirs(LOG_DIR, exist_ok=True)  # Ensure log directory exists
LOG_FILE = os.path.join(LOG_DIR, f"logs_{TODAY_DATE}.log")
logger = logging.getLogger(__name__)

# Remove all existing handlers (if any)
for handler in logger.handlers[:]:
    logger.removeHandler(handler)
    
# File handler (writes logs to a file)
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s - %(message)s"))
logger.addHandler(file_handler)
logger.propagate = False

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
    
    def __init__(self,dirpath:str,filter_text: bool=False):
        self.dirpath=dirpath
        logger.info(f"Initializing DocLoader with directory: {dirpath}")
        self.file_path=self.load_pdf_files()
        self.__section_state = {"active_removal": False, "current_section": None}
        self.filter_text = filter_text

    def load_pdf_files(self)-> list:
        """sumary_line
        Return: return list of path of pdf's in specific directory
        """
        logger.info("Loading PDF files from directory...")
        pdf_files = []
        for filename in tqdm(os.listdir(self.dirpath)):
            if filename.endswith(".pdf"):
                filepath = os.path.join(self.dirpath, filename)
                pdf_files.append(os.path.abspath(filepath))
        pdf_files = [p for p in pdf_files if os.path.isfile(p)]  # Validate paths
        logger.info(f"Found {len(pdf_files)} PDF files.")
        return pdf_files
    
    def filter_sections(self, text: str) -> str:
        """
        Removes unwanted sections from the provided text.
        If an unwanted section (e.g., References, Bibliography, Acknowledgments, Appendix,
        Author Contributions, Funding, Literature Review, Introduction) is detected on a page,
        the function returns an empty string for that page and any subsequent page until
        a preserved section header (e.g., Abstract, Conclusion, etc.) is encountered.
        
        This function works line‐by‐line and uses persistent state across pages.
        """
        logger.info("Filtering sections from extracted text.")
        # Define unwanted and preserved section names (all in lowercase)
        UNWANTED = [
            "references", "bibliography", "acknowledgments", "appendix",
            "conflicts of interest", "author contributions", "funding", 
            "literature review", "introduction", "just accepted",
            "supporting information", "references and notes","releated work","ethical consideration",
            "literature","contributions"
        ]
        PRESERVED = [
            "abstract", "conclusion", "results and discussion", "results", "characterization",
            "materials and methods", "methodology", "experiments", "conclusions", "keywords",
            "experimental details", "experimental section","software discription","research contributions",
            "proposed methodology","implementation","datasets","motivation and significance","discussion"
        ]
        
        # Initialize persistent state if needed.
        if not hasattr(self, "__section_state"):
            self.__section_state = {"active_removal": False, "current_section": None}
        
        output_lines = []
        for line in text.splitlines():
            # Clean up the line: trim, lower-case, remove trailing punctuation.
            candidate = line.strip().lower()
            candidate = re.sub(r"[:.,;]+$", "", candidate)
            # Remove any numeric prefix (e.g., "1. " or "1 - ") to normalize headers.
            candidate = re.sub(r"^\d+\s*[\.\-]?\s*", "", candidate)
            
            # Check if the candidate line starts with an unwanted header.
            if any(candidate.startswith(header) for header in UNWANTED):
                logger.info(f"Ignoring section: {candidate}")
                self.__section_state["active_removal"] = True
                self.__section_state["current_section"] = candidate
                # Do not include this header in output.
                continue
            
            # Check if the candidate line starts with a preserved header.
            if any(candidate.startswith(header) for header in PRESERVED):
                # Stop removal mode.
                logger.info(f"Preserving section: {candidate}")
                self.__section_state["active_removal"] = False
                self.__section_state["current_section"] = candidate
                output_lines.append(line)  # Keep the header as-is.
                continue
            
            # If we're in active removal mode, skip the line.
            if self.__section_state["active_removal"]:
                continue
            
            # Otherwise, include the line.
            output_lines.append(line)
        
        return "\n".join(output_lines).strip()
    


    def pypdf_loader(self):
        """sumary_line
        Simple and Fast document loader
        """
        logger.info("Loading PDFs using PyPDFLoader...")
        document=[]

        for path in tqdm(self.file_path):
            try:
                loader = PyPDFLoader(file_path=path)
                combined_content =[]
                metadata=None
                for page in loader.load():
                    if metadata is None:
                        metadata=page.metadata
                        del metadata['page'],metadata['page_label']
                        metadata.update({'source':os.path.basename(metadata['source'])})
                    combined_content.append(page.page_content)

                combined_content = "\n\n".join(combined_content)
                if self.filter_text:
                    document.append(Document(page_content=self.filter_sections(combined_content),metadata=metadata))
                    logging.info(f"Processed file: {path}")
                else:
                    document.append(Document(page_content=combined_content,metadata=metadata))
                    logging.info(f"Processed file: {path}")
            except Exception as e:
                logger.error(f"Error processing {path}: {e}")

        logger.info(f"Total documents loaded: {len(document)}")      
        return document

    def unstructured_loader(self):
        """_summary_
        better than simple pdf loader as it also includes images and other content which uses
        tesseract OCR so it takes more time than simple pdf loader
        """
        logger.info("Loading PDFs using UnstructuredLoader...")
        document=[]
        for path in tqdm(self.file_path):
            try:
                loader = UnstructuredLoader(file_path=path, strategy="hi_res")
                fcombined_content =[]
                metadata=None
                for page in loader.load():
                    if metadata is None:
                        metadata=page.metadata
                        del metadata['page'],metadata['page_label']
                        metadata.update({'source':os.path.basename(metadata['source'])})
                    combined_content.append(page.page_content)

                combined_content = "\n\n".join(combined_content)
                if self.filter_text:
                    document.append(Document(page_content=self.filter_sections(combined_content),metadata=metadata))
                else:
                    document.append(Document(page_content=combined_content,metadata=metadata))
            except Exception as e:
                logger.error(f"Error processing {path}: {e}")
                
        logger.info(f"Total documents loaded: {len(document)}")
        return document

    def docling_loader(self):
        """_summary_
        When to Use Docling
            1.Projects involving NLP pipelines where structured text extraction is needed.
            2.When working with a mix of file formats beyond just PDFs.
            3.In scenarios where document metadata is as important as the content itself.
            4.For extracting domain-specific data from unstructured documents, like legal, medical, or financial reports.
        """
        from langchain_docling import DoclingLoader
        document=[]
        for path in tqdm(self.file_path):
            loader = DoclingLoader(file_path=path)
            document.append(loader.load())
        return document


if __name__=="__main__":
    import pathlib
    obj = DocLoader("./PDF/")
    path=obj.load_pdf_files()
    
    document=obj.pypdf_loader()
    print(f"{document[0].metadata}\n")
    print(f"category: {document[0].metadata.get('category')}\n")
    print(document[0].page_content,"\n")
    print(f"No of PDF:{len(path)} No of document:{len(document)}")
    os.makedirs("./filtered_output", exist_ok=True)  # Ensure output directory exists

    # Save the new TXT
    text = document[0].page_content
    llm=obj.filter_sections(text)
    llm2=obj.filter_sections2(text)

    pathlib.Path("./filtered_output/temp_file1" + ".txt").write_bytes(llm.encode())
    pathlib.Path("./filtered_output/temp2_file1" + ".txt").write_bytes(llm2.encode())
    
    text = document[1].page_content
    llm=obj.filter_sections(text)
    llm2=obj.filter_sections2(text)

    pathlib.Path("./filtered_output/temp_file2" + ".txt").write_bytes(llm.encode())
    pathlib.Path("./filtered_output/temp2_file2" + ".txt").write_bytes(llm2.encode())
    
    text = document[2].page_content
    llm=obj.filter_sections(text)
    llm2=obj.filter_sections2(text)

    pathlib.Path("./filtered_output/temp_file3" + ".txt").write_bytes(llm.encode())
    pathlib.Path("./filtered_output/temp2_file3" + ".txt").write_bytes(llm2.encode())

    print("Filtered content saved ")
    # print("--------------------Docling------------------------\n")
    # document2 = obj.docling_loader()
    # for d in document2[0][:3]:
    #     print(f"- {d.page_content=}")
    print("\n--------------------------Unstructred loader-----------------------\n")
    # document2 = obj.unstructured_loader()
    # print(f"{document2[0][0].metadata}\n")
    # for i in range(len(document2[0])):
    #     print(f"category: {document2[0][i].metadata.get('category')}\n")
    #     print(document2[0][i].page_content,"\n")