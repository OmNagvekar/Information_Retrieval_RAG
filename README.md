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
├── citation.py            # Handles structured citation extraction and formatting
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
   - **Citation Extraction**: Uses `citation.py` to extract and format structured citations.

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
Need only if using `UnstructuredLoader`
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for OCR processing.
- Note: Do not forgot to add tesseract in enviroment variable after installation (For Windows)
---

## Usage

### Step 1: Prepare Your Documents
Place the research papers (PDFs) in a directory (default: `./PDF/`).

### Step 2: Add Your Gemini API Key
Before running the system, ensure you have a valid Gemini API key in `gemini_key.txt`.

### Step 3: Ollama Model download
If model is not Downloaded then run the following command
`ollama run hf.co/NousResearch/Hermes-3-Llama-3.2-3B-GGUF:Q6_K`
Link to Download Ollama: [Ollama](https://ollama.com/)

### Step 4: Run the RAG Pipeline
Execute the main script to start processing and querying:

```bash
python main.py
```

### Step 4: Query Examples
Interact with the system using natural language queries. Examples include:
- "Provide endurance cycles and retention time for a resistive switching device with p-type CuO."
- "Analyze switching mechanisms for a device with 5000 nm CuO layers."
- "Summarize memory characteristics of devices using TiO2 synthesized via PLD."

### Step 5: Manage and Analyze Chat History
- **Save history**: Automatically saves after every session.
- **Search history**: Use keywords to find past interactions.
- **Summarize history**: Summarize large histories for concise context.

---

## Output Format

The RAG system provides responses in a structured JSON format (Sample output. Output will not be always be in this format):

```json
[
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
  },
  {
    "data": [
        {
            "numeric_value": null,
            "switching_layer_material": "CuO",
            "synthesis_method": null,
            "top_electrode": "Ag",
            "top_electrode_thickness": null,
            "bottom_electrode": "p-Si",
            "bottom_electrode_thickness": null,
            "switching_layer_thickness": null,
            "switching_type": "resistive switching (RS)",
            "endurance_cycles": 50,
            "retention_time": null,
            "memory_window": null,
            "num_states": "2 (HRS and LRS)",
            "conduction_mechanism": null,
            "resistive_switching_mechanism": "Ag filament formation",
            "additionalProperties": null,
            "paper_name": "Memristive Devices from CuO Nanoparticles",
            "source": "1.pdf"
        }
    ]
  }
]

```
For citation response format:

```json
{
    "citations": [
        {
            "Source_ID": 0,
            "Article_ID": "8ca54a6f-30ed-4ef4-9927-700080b8a23b",
            "Article_Snippet": "function of the number of cycles, which show the co nsistency and stability in low resistive state (LRS) \nand high resistive state (HRS). The semi-log I-V curv es in Figure 3d give a more accurate picture of \nNDR and RS with a switching ratio of 103. \n\nFigure 3. (a) Current–voltage (I-V) curve of Ag/CuO/SiO 2/p-Si resistive switching and ( b) multiple \nresistive switching up to 50 cycles depicting reproducibility. The inset shows the formation of \nnegative differential resistance (NDR), ( c) endurance performance of Ag/CuO/SiO 2/p-Si, and ( d) semi-\nlog current–voltage characteristics of a multilayer Ag/CuO/SiO 2/p-Si showing NDR and on-off",
            "Article_Title": "Memristive Devices from CuO Nanoparticles",
            "Article_Source": "1.pdf"
        },
        {
            "Source_ID": 1,
            "Article_ID": "beea0861-2de7-4136-b9da-b7cb3b2212d8",
            "Article_Snippet": "Figure 3b shows a clear cut of the NDR. The current decreases sharply with an increase in potential.\nFigure 3c shows the endurance performance of the device. Resistance was taken as a function of\nthe number of cycles, which show the consistency and stability in low resistive state (LRS) and high\nresistive state (HRS). The semi-log I-V curves in Figure 3d give a more accurate picture of NDR and RS\nwith a switching ratio of 103.\nNanomaterials 2020 , 10, x FOR CONVERSION 4 of 9 \n The I-V characteristics in Figure 3a clearly show  the hysteresis curve, which demonstrates the \nnon-volatile resistive switching along with negative differential resistance. The voltage was swept",
            "Article_Title": "Memristive Devices from CuO Nanoparticles",
            "Article_Source": "1.pdf"
        },
        {
            "Source_ID": 2,
            "Article_ID": "47b089f6-de7a-48dc-92b2-045bbf121156",
            "Article_Snippet": "Nanomaterials 2020 ,10, 1677 4 of 10\nThe I-V characteristics in Figure 3a clearly show the hysteresis curve, which demonstrates the\nnon-volatile resistive switching along with negative di ﬀerential resistance. The voltage was swept from\n0 » 3 V » 0 »−3 V » 0. A stable resistive switching (RS) is observed when the bias voltage sweeps from\n0 V to 3 V; the current switches from 10−6A to 10−3A at a set voltage of 1.7 V . The device maintains\na low resistive state (LRS) when the bias voltage sweeps back from positive (3 V) to negative ( −0.7\nV), NDR is observed at −0.8 V , and the device switches o ﬀ. Figure 3b demonstrates repeatability in\nswitching up to 50 cycles, emphasizing the reproducibility and stability of the device. The inset in",
            "Article_Title": "Memristive Devices from CuO Nanoparticles",
            "Article_Source": "1.pdf"
        },
        {
            "Source_ID": 3,
            "Article_ID": "6edd1459-8aad-4937-bfb6-6d64d1da06f0",
            "Article_Snippet": "To further investigate the role of native oxide, p- Si, and Ag, we fabricated a device consisting of \nITO as the bottom electrode. Figure 6 shows the I-V characteristics of the device with Ag as a top \nelectrode and ITO as a bottom electr ode with CuO nanoparticles acting as an active layer. In the absence \nof SiO 2, the device showed resistive switching with out NDR. The switching was described by the \nformation of Ag filament based on the linear I-V ch aracteristics. The device did not show NDR in the \nabsence of oxide. The abrupt uncont rollable switching also  characterizes the absence of native oxide. \nThe results showed no NDR in the case of Ag/C uO/ITO, and we inferred that NDR in Ag/CuO/SiO 2/p-",
            "Article_Title": "Memristive Devices from CuO Nanoparticles",
            "Article_Source": "1.pdf"
        },
        {
            "Source_ID": 4,
            "Article_ID": "e54da728-8e6e-4cb3-8435-1fd7a22eeabf",
            "Article_Snippet": "injected current in response to applied voltage [27]. The interaction of the injected carriers in defect states affects the magnitude of current, which al so affects the current–vo ltage characteristics. \nFigure 3. (a) Current–voltage (I-V) curve of Ag /CuO/SiO 2/p-Si resistive switching and ( b) multiple\nresistive switching up to 50 cycles depicting reproducibility. The inset shows the formation of negative\ndiﬀerential resistance (NDR), ( c) endurance performance of Ag /CuO/SiO 2/p-Si, and ( d) semi-log\ncurrent–voltage characteristics of a multilayer Ag /CuO/SiO 2/p-Si showing NDR and on-o ﬀconductance\nof 1×103in the positive region. The voltage was swept from −3 V to 3 V . The V setand V reset are 1.5 V\nand−0.65 V .",
            "Article_Title": "Memristive Devices from CuO Nanoparticles",
            "Article_Source": "1.pdf"
        },
        {
            "Source_ID": 5,
            "Article_ID": "93bcf96d-3ef8-4b5c-b891-b33d3716a30f",
            "Article_Snippet": "from 0 » 3 V » 0 » −3 V » 0. A stable resistive switching (RS) is observed when the bias voltage sweeps \nfrom 0 V to 3 V; the current switches from 10−6 A to 10−3 A at a set voltage of 1.7 V. The device \nmaintains a low resistive state (LRS) when the bias  voltage sweeps back from positive (3 V) to \nnegative ( −0.7 V), NDR is observed at −0.8 V, and the device switches off. Figure 3b demonstrates \nrepeatability in switching up to 50 cycles, emphasiz ing the reproducibility and stability of the device. \nThe inset in Figure 3b shows a clear cut of the ND R. The current decreases sharply with an increase \nin potential. Figure 3c shows the endurance perf ormance of the device. Resistance was taken as a",
            "Article_Title": "Memristive Devices from CuO Nanoparticles",
            "Article_Source": "1.pdf"
        },
        {
            "Source_ID": 6,
            "Article_ID": "bd69dcf5-6c25-4bc8-9e08-9a61550eefbe",
            "Article_Snippet": "ITO as the bottom electrode. Figure 6 shows the I-V characteristics of the device with Ag as a top \nelectrode and ITO as a bottom electrode with CuO nanopa rticles acting as an active layer. In the absence \nof SiO\n2, the device showed resistive switching with out NDR. The switching was described by the \nformation of Ag filament based on the linear I-V ch aracteristics. The device did not show NDR in the \nabsence of oxide. The abrupt uncont rollable switching also characteri zes the absence of native oxide. \nThe results showed no NDR in the case of Ag/C uO/ITO, and we inferred that NDR in Ag/CuO/SiO 2/p-",
            "Article_Title": "Memristive Devices from CuO Nanoparticles",
            "Article_Source": "1.pdf"
        },
        {
            "Source_ID": 7,
            "Article_ID": "7d481d67-b8b9-44e6-bdad-a97284670549",
            "Article_Snippet": "Received: 17 July 2020; Accepted: 23 August 2020; Published: 26 August 2020\n/gid00030/gid00035/gid00032/gid00030/gid00038/gid00001/gid00033/gid00042/gid00045 /gid00001\n/gid00048/gid00043/gid00031/gid00028/gid00047/gid00032/gid00046\nAbstract: Memristive systems can provide a novel strategy to conquer the von Neumann bottleneck\nby evaluating information where data are located in situ. To meet the rising of artiﬁcial neural\nnetwork (ANN) demand, the implementation of memristor arrays capable of performing matrix\nmultiplication requires highly reproducible devices with low variability and high reliability. Hence,\nwe present an Ag /CuO/SiO 2/p-Si heterostructure device that exhibits both resistive switching (RS)",
            "Article_Title": "Memristive Devices from CuO Nanoparticles",
            "Article_Source": "1.pdf"
        },
        {
            "Source_ID": 8,
            "Article_ID": "4e58a51e-be24-473c-a7ca-dd70657ebe8f",
            "Article_Snippet": "conﬁned the ﬁlament rupture and reduced the reset variability. Reset was primarily inﬂuenced by\nthe ﬁlament rupture and detrapping in the native oxide that facilitated smooth reset and NDR in\nthe device. The resistive switching originated from traps in the localized states of amorphous CuO.\nThe set process was mainly dominated by the trap-controlled space-charge-limited; this led to a\ntransition into a Poole–Frenkel conduction. This research opens up new possibilities to improve the\nswitching parameters and promote the application of RS along with NDR.\nKeywords: CuO nanomaterials; negative di ﬀerential resistance; Poole–Frenkel conduction; switching\nratio; resistive switching; space charge limited current\n2. Materials and Methods",
            "Article_Title": "Memristive Devices from CuO Nanoparticles",
            "Article_Source": "1.pdf"
        }
    ]
}

```
---

## Key Classes and Methods

### **`rag_assistant.py (Core RAG System)`**
- **`RAGChatAssistant`**: Handles document retrieval and response generation.
- **`Methods:`**:
    - `create_vectors()`: Processes PDFs, extracts text, generates embeddings, and stores them in ChromaDB.
    - `retrieve_context()`: Implements Self-Query Retriever, Multi-Query Retriever, and Ensemble Retriever for accurate document retrieval.
    - `generate_response()`: Uses ChatOllama or Gemini API to produce structured, schema-validated responses and extracts structured citations.
    - `create_prompt_template()`: Generates contextual prompts for better response accuracy.
    - `preprocess_text()`: Improved text processing and data normalization.
    - `extract_citations()`: Uses Kor-based processing to extract citation data.


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

### **`citation.py`**
- Defines schemas for structured citation extraction.
  - Models include `Citation` and `Citations` for validated output.

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

- Implement dynamic schema generation for custom queries.
- Develop Full Stack Application with Frontend for user intreaction on the web.

---

## Contributing

Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a new branch.
3. Submit a pull request with your changes.

---

## Contact

For any questions or suggestions, feel free to contact on below Contact details:

- Om Nagvekar Portfolio Website, Email: https://omnagvekar.github.io/ , omnagvekar29@gmail.com
- GitHub Profile:
   - Om Nagvekar: https://github.com/OmNagvekar

---

## Citing the project
To cite this repository in publications:

```bibtex
@misc{Information_Retrieval_RAG,
  author = {Om Nagvekar},
  title = {Information Retrieval RAG For Data Extraction from Research Papers},
  year = {2025},
  howpublished = {\url{https://github.com/OmNagvekar/Information_Retrieval_RAG/}},
  note = {GitHub repository},
}
```
---

## License

This project is licensed under the [GPL-3.0 license](LICENSE).

---