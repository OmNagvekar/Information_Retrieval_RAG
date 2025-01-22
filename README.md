# Information Retrieval RAG For Data Extraction from Reserach Papers

This project provides a framework for **Retrieval-Augmented Generation (RAG)** to extract and analyze information from research papers. It uses vector-based retrieval techniques and structured LLMs to process PDF documents and retrieve insights based on user queries.

---

## Directory Structure

```plaintext
omnagvekar-information_retrieval_rag/
├── document_loader.py  # Handles document loading and parsing from PDFs
├── general_schema.py   # Defines basic data schemas for extracted information
├── main.py             # Implements the main RAG workflow
├── scheme.py           # Contains Pydantic models for data validation and Defines data schemas for extracted information
├── textsplitter.py     # Processes documents for embedding and vector storage
```

---

## Features

1. **Document Loading**:
   - Supports structured and unstructured PDF parsing via:
     - `PyPDFLoader` for text-heavy PDFs.
     - `UnstructuredLoader` for complex layouts (including OCR).
     - `DoclingLoader` for structured text extraction.

2. **Text Processing**:
   - Splits documents into manageable chunks using `RecursiveCharacterTextSplitter`.
   - Embeds text chunks for similarity-based retrieval using HuggingFace embeddings.

3. **Vector Storage**:
   - Uses FAISS for efficient vector storage and similarity searches.

4. **RAG Pipeline**:
   - Integrates LangChain's structured LLMs for robust response generation.
   - Maintains chat history for context-aware responses.
   - Extracts and validates information against a well-defined schema.

5. **Custom Features**:
   - Summarizes older chat history for efficient management.
   - Detects conversation topics and provides analytical insights.
   - Anonymizes sensitive data in the chat history.

---

## Installation

### Prerequisites
- Python 3.11+
- CUDA-enabled GPU (optional for faster processing)
- Required libraries (install via `requirements.txt`):

```bash
pip install -r requirements.txt
```

### Additional Tools
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (if using OCR with `UnstructuredLoader`).

- Note: Do not forgot to add tesseract in enviroment variable after installation (For Windows)

---

## Usage

### 1. Document Preparation
Place your PDF documents in the desired directory (default: `./PDF/`).

### 2. Running the RAG Pipeline
Execute the main script:

```bash
python main.py
```

### 3. Query Examples
The system supports complex scientific queries like:
- **Example 1**: "Provide retention time and endurance cycles for a resistive switching device using p-type CuO."
- **Example 2**: "Extract all switching characteristics of a device with a 5000 nm CuO layer."

### 4. Custom Configurations
Modify parameters in `textsplitter.py` or `main.py` to customize:
- Chunk size and overlap.
- Embedding model and device.

---

## Output Structure

The RAG pipeline returns structured JSON output with the following format:

```json
{
  "input_data": {
    "switching_layer_material": "CuO",
    ...
  },
  "output_data": {
    "type_of_switching": "Resistive",
    ...
  },
  "reference_information": {
    "name_of_paper": "Switching Properties of CuO",
    "doi": "https://doi.org/10.1234/exampledoi",
    ...
  }
}
```

---

## Known Limitations

- Processing large PDFs with OCR may be time-intensive.
- Requires substantial memory for handling large document sets.

---

## Future Work

- Implement more advanced topic modeling and summarization techniques.
- Expand support for additional file formats (e.g., Word, Excel).
- Enhance schema validation with nested and hierarchical data extraction.

---

## Contributing

Contributions are welcome! Submit your PRs or open issues to suggest enhancements.

---

## License

This project is licensed under the [MIT License](LICENSE).

---
