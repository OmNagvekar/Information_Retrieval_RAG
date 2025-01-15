from document_loader import DocLoader
from textsplitter import ProcessText
from tqdm import tqdm

document_loader = DocLoader("./PDF/")
document = document_loader.pypdf_loader()
Textprocess = ProcessText()
for doc in tqdm(document):
    doc_text = " ".join([page.page_content for page in doc])
    processed_text = Textprocess.splitter(doc_text)
    embedded_text = Textprocess.embeded_documents(processed_text)
    print(f"\nprocessed text:{processed_text}\n embedded text:{embedded_text}\n")

