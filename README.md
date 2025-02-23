# Information Retrieval RAG For Data Extraction from Research Papers

This project is a **Retrieval-Augmented Generation (RAG)** system designed to extract scientific and technical information from research papers. The system is built to handle large-scale document processing, embedding-based retrieval, and context-aware responses, leveraging **LangChain**, **ChromaDB**, and **LLMs** for robust data extraction and conversational AI.The system supports **Gemini API** and **Ollama** for LLM.

---

## Directory Structure

```plaintext
omnagvekar-information_retrieval_rag/
├── document_loader.py     # Handles document loading and parsing from PDFs
├── general_schema.py      # Defines data schemas for extracted information
├── rag_assistant.py       # Core RAG Assistant
├── main.py                # Execution script
├── scheme.py              # ontains Pydantic models for data validation and Defines data schemas for extracted information
├── textsplitter.py        # Processes and embeds text chunks for vector storage
├── ChatHistory.py         # Contains code to manage history
├── gemini_scheme.py       # New schema for Gemini API integration
├── gemini_key.txt         # Stores API key for Gemini LLM (Looking for API KEY Not available in Repo as it is API KEY 😊)
├── LICENSE                # Added LICENSE File
```

---

## Features

### 1. **Document Loading**
   - **Flexible Input Handling**:  
     - **`PyPDFLoader`**: Fast processing for text-heavy PDFs.
     - **`UnstructuredLoader`**: Extracts data from complex layouts, including OCR for image-based PDFs.
     - **`DoclingLoader`**: Ideal for metadata-driven structured extraction.
   - **Batch Processing**: Automatically scans directories for PDFs and loads them into memory.

### 2. **Text Processing**
   - **Chunking**: Uses `RecursiveCharacterTextSplitter` to split documents into smaller, manageable chunks for better embedding and retrieval.
   - **Embedding**: Utilizes HuggingFace's `BAAI/bge-base-en` model for generating dense embeddings compatible with FAISS.

### 3. **Vector Storage and Retrieval**
   - **Storage**: Implements ChromaDB for fast similarity searches on vectorized document chunks.
   - **Search Modes**: Supports Maximum Marginal Relevance (MMR) and similarity-based retrieval.
   - **Local Storage**: Local Storage: Saves and loads ChromaDB indices for persistent retrieval capabilities..

### 4. **RAG Pipeline**
   - **LLM Integration**: Leverages LangChain's `ChatOllama` and also supports `Gemini API LLM ` for structured query responses.
   - **Prompt Engineering**: Constructs custom prompts with examples, ensuring high accuracy in responses for `ChatOllama` Instance LLM.
   - **Schema Validation**: Ensures extracted data adheres to well-defined Pydantic models, reducing inconsistencies.
   - **Context Retrieval**: Implements Self-Query Retriever, Multi-Query Retriever, and Ensemble Retriever for more accurate document retrieval.

### 5. **Chat History Management**
   - **Context-Aware Conversations**: Maintains chat history for relevant and coherent multi-turn dialogues.
   - **Persistence**: Saves chat history as JSON files, ensuring continuity between sessions.
   - **Search and Export**:
     - Search past conversations by keywords.
     - Export and backup chat history for future reference.

### 6. **Analytics and Summarization**
   - **Conversation Summarization**: Compresses older messages into concise summaries using LLMs.
   - **Topic Modeling**: Extracts main topics using TF-IDF and NMF for better insight into chat history.
   - **Statistics**: Provides analytics like total messages, average message length, and distribution between human and AI messages.

### 7. **Scientific Data Extraction**
   - Supports queries to extract structured information like:
     - **Input Data**: Materials, synthesis methods, electrode types, and thicknesses.
     - **Output Data**: Switching types, endurance cycles, retention times, memory windows, and mechanisms.
     - **Reference Information**: Paper title, DOI, publication year, and source file path.

### 8. **Custom Enhancements**
   - **Sensitive Data Handling**:
     - Anonymizes chat history by masking emails, phone numbers, and names.
   - **Backup and Restore**:
     - Automatically backs up chat histories and allows restoration from backups.
   - **Compression**:
     - Reduces chat history size by summarizing older messages using LangChain's summarization chains.
  
### 9. **Logging & Error Handling**
  - Implements structured logging for debugging and performance monitoring.
  - Deletes old logs automatically if they do not contain errors.
  - If log is older than 3 days then it deletes the log even if log contain errors

---

## Installation

### Prerequisites
- Python 3.11+
- CUDA-enabled GPU (optional for faster processing with LLMs)
- Libraries (install via `requirements.txt`):
  
```bash
pip install -r requirements.txt
```

### Additional Tools
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for OCR processing.
- Note: Do not forgot to add tesseract in enviroment variable after installation (For Windows)
---

## Usage

### Step 1: Prepare Your Documents
Place the research papers (PDFs) in a directory (default: `./PDF/`).

### Step 2: Run the RAG Pipeline
Execute the main script to start processing and querying:

```bash
python main.py
```

### Step 3: Query Examples
Interact with the system using natural language queries. Examples include:
- "Provide endurance cycles and retention time for a resistive switching device with p-type CuO."
- "Analyze switching mechanisms for a device with 5000 nm CuO layers."
- "Summarize memory characteristics of devices using TiO2 synthesized via PLD."

### Step 4: Manage and Analyze Chat History
- **Save history**: Automatically saves after every session.
- **Search history**: Use keywords to find past interactions.
- **Summarize history**: Summarize large histories for concise context.

---

## Output Format

The RAG system provides responses in a structured JSON format (Sample output. Output will not be always be in this format):

```json
  [{
    "input_data": {
      "switching_layer_material": "CuO",
      "synthesis_method": "Chemical",
      "top_electrode": "Pt",
      "bottom_electrode": "Au",
      "switching_layer_thickness": 5000
    },
    "output_data": {
      "type_of_switching": "Resistive",
      "endurance_cycles": 50000,
      "retention_time": 10000,
      "memory_window": 1.2
    },
    "reference_information": {
      "name_of_paper": "Switching Properties of CuO Nanoparticles",
      "doi": "https://doi.org/10.1234/exampledoi",
      "year": 2022,
      "source": "paper.pdf"
    }
  },

  {
      "data": [
          {
              "numeric_value": null,
              "switching_layer_material": "CuO",
              "synthesis_method": "null",
              "top_electrode": "Ag",
              "top_electrode_thickness": null,
              "bottom_electrode": null,
              "bottom_electrode_thickness": null,
              "switching_layer_thickness": null,
              "switching_type": null,
              "endurance_cycles": null,
              "retention_time": null,
              "memory_window": null,
              "num_states": null,
              "conduction_mechanism": null,
              "resistive_switching_mechanism": null,
              "paper_name": null,
              "doi": null,
              "year": 2020,
              "source": null,
              "additionalProperties": null
          }
      ]
  }
]


```

---

## Key Classes and Methods

### **`rag_assistant.py (Core RAG System)`**
- **`RAGChatAssistant`**: Handles document retrieval and response generation.
- **`Methods:`**:
    - `create_vectors()`: Processes PDFs, extracts text, generates embeddings, and stores them in ChromaDB.
    - `retrieve_context()`: Implements Self-Query Retriever, Multi-Query Retriever, and Ensemble Retriever for accurate document retrieval.
    - `generate_response()`: Uses ChatOllama to produce structured, schema-validated responses.
    - `create_prompt_template()`: Generates contextual prompts for better response accuracy.

### **`document_loader.py`**
- **`DocLoader`**: Handles PDF loading and parsing.
  - `pypdf_loader`: Basic loader for text-heavy PDFs.
  - `unstructured_loader`: Advanced OCR-based loader.
  - `docling_loader`: Extracts structured metadata.

### **`gemini_scheme.py`**
- Defines response structure and ensures schema validation for Gemini API responses.

### **`textsplitter.py`**
- **`ProcessText`**: Manages text splitting, embedding, and vector store creation.
  - `splitter`: Splits documents into chunks.
  - `embeded_documents`: Converts chunks into embeddings.
  - `vectore_store`: Creates ChromaDB vector storage.

### **`scheme.py`**
- Defines schemas for structured data extraction.
  - Models include `Extract_Text` and `Data` for validated output.

### **`main.py`**
- Initializes RAGChatAssistant and executes sample queries.
- Manages log cleanup and error handling.

### **`general_schema.py`**
- Houses schemas for high-level text extraction.
  - Models include `General_Extract_Text` for basic numeric value extraction.

### **`ChatHistory.py`**
- **`ChatHistoryManager`**: Manages user chat history and provides tools for context-aware conversation handling.
  - **Initialization**:
    - `__init__`: Sets up user-specific chat history, ensuring persistence in the `chat_histories` directory.
  - **Chat Management**:
    - `add_user_message`: Adds a human message to the history.
    - `add_ai_message`: Adds an AI-generated response.
    - `clear_history`: Deletes all messages in the chat history.
    - `get_message_history`: Retrieves the last `n` messages in LangChain format.
    - `compress_history`: Summarizes older messages to reduce storage size.
  - **History Insights**:
    - `analyze_history_stats`: Provides statistics, such as total messages, average lengths, and timestamps.
    - `detect_conversation_topics`: Extracts key topics using TF-IDF and NMF.
  - **Persistence**:
    - `save_history`/`_save_history`: Saves history to a JSON file.
    - `export_history`: Exports chat history to a specified path.
    - `restore_from_backup`: Restores history from a backup file.
  - **Search and Filtering**:
    - `search_history`: Searches messages by keyword, with optional case sensitivity.
    - `get_history_by_date_range`: Filters messages within a specific date range.
  - **Privacy and Security**:
    - `anonymize_history`: Redacts personal data (emails, phone numbers, and names).
  - **Backup and Restore**:
    - `backup_history`: Backs up chat history to a timestamped file.
    - `import_history`: Imports chat history from a backup file.

---

## Future Work

- Extend support for additional document formats (e.g., Word, Excel).
- Implement dynamic schema generation for custom queries.
- Integrate advanced summarization and sentiment analysis for chat histories.
- Add visualization tools for insights like topic distributions.
- Develop Full Stack Application with Frontend for user intreaction on the web.

---

## Contributing

Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a new branch.
3. Submit a pull request with your changes.

---

## License

This project is licensed under the [GPL-3.0 license](LICENSE).

---

## Contact

For any questions or suggestions, feel free to contact on below Contact details:

- Om Nagvekar Portfolio Website, Email: https://omnagvekar.github.io/ , omnagvekar29@gmail.com
- GitHub Profile:
   - Om Nagvekar: https://github.com/OmNagvekar

---