from document_loader import DocLoader
from textsplitter import ProcessText
from tqdm import tqdm
from uuid import uuid4
from langchain_core.documents import Document
import os
from scheme import Data,Extract_Text
from citation import Citations
from gemini_scheme import Data_Objects, Extract_Data
from ratelimit import limits, sleep_and_retry
from tenacity import retry, stop_after_attempt, wait_exponential
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from typing import List, Dict, Any
# from langchain_ollama.chat_models import ChatOllama #delete this later on
from langchain_huggingface import HuggingFacePipeline,ChatHuggingFace
from langchain_core.output_parsers import PydanticOutputParser
import torch
import json
import logging
import difflib
from ChatHistory import ChatHistoryManager
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.retrievers import SelfQueryRetriever, MultiQueryRetriever, EnsembleRetriever
from langchain.chains.query_constructor.base import AttributeInfo
import asyncio
import time
import re
from typing import Optional
from kor.extraction import create_extraction_chain
from kor import from_pydantic


logger = logging.getLogger(__name__)
# Define rate limiter (2 requests per minute)
REQUESTS = 2
PERIOD = 60  # seconds

class RAGChatAssistant:
    def __init__(self,user_id:str,dirpath:str="./PDF/",remote_llm:bool=False,hf_model:str='NousResearch/Hermes-3-Llama-3.2-3B'):
        logger.info("Initializing RAGChatAssistant")
        # path to uploaded/local pdf's
        self.dirpath = dirpath
        # device agnostic code
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Using device: {self.device}")
        # chat History manager
        self.chat_history_manager = ChatHistoryManager(user_id=user_id)
        #LLM
        self.remote_llm =remote_llm
        if remote_llm:
            try:
                with open("gemini_key.txt",'r') as f:
                    key = f.read()
                llm = ChatGoogleGenerativeAI(model='gemini-1.5-flash',max_retries=2,google_api_key=key,disable_streaming=False,convert_system_message_to_human=True,temperature=0.5,cache=False)
                self.llm = llm.with_structured_output(Data_Objects)
                self.llm_citation = llm #llm.with_structured_output(Citations)
                self.llm2 = llm
                # Pydantic output parser
                self.output_parser = PydanticOutputParser(pydantic_object=Data_Objects)
                logger.info("LLM initialized with gemini-1.5-flash")
            except Exception as e:
                logger.error("Failed to intialize the Gemini LLM gemini-1.5-flash %s",str(e))
                llm = HuggingFacePipeline.from_model_id(
                    model_id=hf_model,
                    task="text-generation",
                    model_kwargs={"temperature": 0.5,"device":self.device}
                )
                chat_model = ChatHuggingFace(llm=llm)
                self.llm = chat_model.with_structured_output(Data_Objects)
                self.llm_citation = chat_model
                self.llm2 = chat_model
                logger.info(f"LLM initialized with {hf_model}")
                # Pydantic output parser
                self.output_parser = PydanticOutputParser(pydantic_object=Data_Objects)
                self.remote_llm=False
        else:
            llm = HuggingFacePipeline.from_model_id(
                model_id=hf_model,
                task="text-generation",
                model_kwargs={"temperature": 0.5,"device":self.device}
            )
            chat_model = ChatHuggingFace(llm=llm)
            self.llm = chat_model.with_structured_output(Data_Objects)
            self.llm_citation = chat_model
            self.llm2 = chat_model
            logger.info(f"LLM initialized with {hf_model}")
            # Pydantic output parser
            self.output_parser = PydanticOutputParser(pydantic_object=Data_Objects)

        # Loading vectore store
        if os.path.exists("./chroma_db"):
            print("\n Skipping creating indexes as local index is present \n")
            logger.info("Local Chroma index found. Loading existing vectors.")
            # Intializing objects
            self.Textprocess = ProcessText(device=self.device)
            self.document_loader = DocLoader(self.dirpath,filter_text=True)
            self.pdf_files =[os.path.basename(pdfs) for pdfs in self.document_loader.file_path]
            # Loading vectore store
            self.vectore_store = self.load_vectors(self.Textprocess)
        else:
            print("\n Creating Vectore Index and Storing Locally \n")
            logger.info("No existing Chroma index found. Creating new vector index.")
            # Intializing objects
            self.Textprocess = ProcessText(device=self.device)
            self.document_loader = DocLoader(self.dirpath,filter_text=True)
            self.pdf_files =[os.path.basename(pdfs) for pdfs in self.document_loader.file_path]
            # Creating Vectore Store
            self.vectore_store = self.create_vectors(self.document_loader,self.Textprocess)

    def create_vectors(self,document_loader: DocLoader,Textprocess: ProcessText):
        logger.info("Starting vector creation process.")
        document = document_loader.pypdf_loader()
        vector_store = Textprocess.vectore_store()
        
        for doc in tqdm(document):
            processed_text =  Textprocess.splitter(doc.page_content)
            page_metadata = doc.metadata.copy()
            doc_objects = [
                Document(
                    page_content=chunk,
                    metadata={
                        "id":str(uuid4()),
                        "source":page_metadata.get("source", "unknown"),
                        "title":page_metadata.get("title", "unknown"),
                        "total_pages":page_metadata.get('total_pages',"unknown"),
                        "doi":page_metadata.get('doi','unknown')
                    })
                for chunk in processed_text
            ]
            vector_store.add_documents(doc_objects)
        logger.info("Vector store saved locally as 'Chromadb'.")
        return vector_store

    def create_prompt_template(self):
        logger.info("Creating prompt template.")
        examples = [
            {
                "query":"""
                        Please read the provided PDF thoroughly and extract the following quantities. Your output must be a table with two columns: "Quantity" and "Extracted Value". For each of the items listed below, provide the extracted value exactly as it appears in the document. If an item is not found, simply enter "N/A" for that field. Ensure that any numerical values include their associated units (if applicable) and that you handle multiple values consistently.

                        Extract the following items:
                        - switching layer material
                        - synthesis method
                        - top electrode
                        - thickness of top electrode in nanometers
                        - bottom electrode
                        - thickness of bottom electrode in nanometers
                        - thickness of switching layer in nanometers
                        - type of switching
                        - endurance
                        - retention time in seconds
                        - memory window in volts
                        - number of states
                        - conduction mechanism type
                        - resistive switching mechanism
                        - paper name
                        - source (pdf file name)

                        Instructions:
                        1. Analyze the entire PDF document to locate all references to the above items.
                        2. Extract each quantity with precision; include any units and relevant details.
                        3. If multiple values are present for a single item, list them clearly (e.g., separated by commas).
                        4. Format your output strictly as a table with two columns: one for the "Quantity" and one for the "Extracted Value".
                        5. Do not include any extra text, headings, or commentary—only the table is required.
                        6. If an item cannot be found, record it as "N/A" in the "Extracted Value" column.

                        """
                ,"data": [
                    {
                        "numeric_value": "Set voltage 1.5v and Reset Voltage -0.65v",
                        "switching_layer_material": "CuO",
                        "synthesis_method": "Soluton Processable",
                        "top_electrode": "Ag",
                        "top_electrode_thickness": 500,
                        "bottom_electrode": "p-Si",
                        "bottom_electrode_thickness": 100,
                        "switching_layer_thickness": 250,
                        "switching_type": "resistive switching (RS)",
                        "endurance_cycles": 50,
                        "retention_time": 1000,
                        "memory_window": 1000,
                        "num_states": "2 (HRS and LRS)",
                        "conduction_mechanism": "Bulk",
                        "resistive_switching_mechanism": "Ag filament formation",
                        "additionalProperties": "Type of Switching Bipolar",
                        "paper_name": "Memristive Devices from CuO Nanoparticles",
                        "source": "1.pdf"
                    }
                ]
            },
        ]
        # Convert examples to message format
        example_messages = []
        for example in examples:
            example_messages.extend([
                HumanMessage(content=example["query"]),
                AIMessage(content=str(example["data"]))
            ])
        if not self.remote_llm:
            prompt_template = ChatPromptTemplate.from_messages(
                [
                    SystemMessage(content=(
                        "You are a specialized AI algorithm for scientific data extraction, designed to analyze research papers. "
                        "Your role is to extract only the relevant information from the provided text. "
                        "If an attribute's value cannot be determined from the context, return 'null' for that attribute. "
                        "Rely solely on the given context to extract information and generate responses. "
                        "Do not use example content to influence the response's content."
                    )),
                    # Please see the how-to about improving performance with
                    # reference examples.
                    ("history:"),
                    MessagesPlaceholder(variable_name='history',n_messages=2),
                    ("examples"),
                    MessagesPlaceholder(variable_name='examples',n_messages=1),
                    ("human", "Query: {query}"),
                    ("system","context:"),
                    MessagesPlaceholder(variable_name='context'),
                ]
            ).partial(format_instructions=self.output_parser.get_format_instructions())
        else:
            prompt_template = ChatPromptTemplate.from_messages(
                [
                    SystemMessage(content=(
                        "You are a specialized AI algorithm for scientific data extraction, designed to analyze research papers. "
                        "Your role is to extract only the relevant information from the provided text. "
                        "If an attribute's value cannot be determined from the context, return 'null' for that attribute. "
                        "Rely solely on the given context to extract information and generate responses. "
                        "Do not use example content to influence the response's content."
                    )),
                    # Please see the how-to about improving performance with
                    # reference examples.
                    ("human","History:{history}"),
                    ("human", "Query: {query}"),
                    ("human","context:{context} "),
                ]
            ).partial(format_instructions=self.output_parser.get_format_instructions())
        return prompt_template,example_messages

    def load_vectors(self,Textprocess: ProcessText):
        vectore_store=Textprocess.load_vectors()
        logger.info("Loading vectors from Chroma index.")
        return vectore_store
    
    def preprocess_text(self,text:str) ->dict:
        def markdown_table_to_dict(table_str: str) -> dict:
            """
            Converts a markdown table to a dictionary.
            Assumes the first column contains keys and the second column the values.
            """
            # Split the input string into lines
            lines = table_str.strip().split("\n")
            # Ignore header and divider lines
            data_lines = lines[2:]
            result = {}
            for line in data_lines:
                # Split by the pipe character and strip extra spaces
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 2:
                    key = parts[0]
                    value = parts[1]
                    result[key] = value
            return result

        def map_and_clean_data(raw_data: dict) -> dict:
            """
            Map raw keys from the markdown table to the Pydantic model field names,
            while cleaning up values. This function ignores the case of the keys.
            """
            from typing import Optional
            import re
            # Normalize raw data keys to lowercase
            normalized_data = { key.lower(): value for key, value in raw_data.items() }
            
            # Mapping keys are provided in lowercase
            mapping = {
                "switching layer material": "switching_layer_material",
                "synthesis method": "synthesis_method",
                "top electrode": "top_electrode",
                "thickness of top electrode in nanometers": "top_electrode_thickness",
                "bottom electrode": "bottom_electrode",
                "thickness of bottom electrode in nanometers": "bottom_electrode_thickness",
                "thickness of switching layer in nanometers": "switching_layer_thickness",
                "type of switching": "switching_type",
                "endurance": "endurance_cycles",
                "retention time in seconds": "retention_time",
                "memory window in volts": "memory_window",
                "number of states": "num_states",
                "conduction mechanism type": "conduction_mechanism",
                "resistive switching mechanism": "resistive_switching_mechanism",
                "paper name": "paper_name",
                "source (pdf file name)": "source"
            }
            
            def clean_numeric_value(value: str) -> Optional[str]:
                """Removes non-numeric characters (except for a decimal point) from a value."""
                if value.strip().lower() in ["n/a", "null"]:
                    return None
                match = re.search(r"([\d.]+)", value)
                return match.group(1) if match else value

            def convert_na(value: str) -> Optional[str]:
                """Convert 'N/A' or 'null' to None and return the trimmed value otherwise."""
                return None if value.strip().lower() in ["n/a", "null"] else value.strip()
            
            cleaned = {}
            for raw_key, field_name in mapping.items():
                # Look up the raw key (already normalized) in the normalized data
                raw_value = normalized_data.get(raw_key, "").strip()
                cleaned_value = convert_na(raw_value)
                
                if field_name in ["endurance_cycles", "retention_time"]:
                    cleaned_value = clean_numeric_value(raw_value)
                    try:
                        cleaned_value = int(float(cleaned_value)) if cleaned_value is not None else None
                    except ValueError:
                        pass
                elif field_name in ["top_electrode_thickness", "bottom_electrode_thickness", "switching_layer_thickness", "memory_window"]:
                    cleaned_value = clean_numeric_value(raw_value)
                    try:
                        cleaned_value = float(cleaned_value) if cleaned_value is not None else None
                    except ValueError:
                        pass
                
                cleaned[field_name] = cleaned_value
            return cleaned
        return map_and_clean_data(markdown_table_to_dict(text))
    
    def retrieve_context(self, query:str, top_k=7):
        """Retrieve relevant documents from vector store"""
        logger.info("Retrieving context")
        # 🧠 **Self-Query Retriever (Filtering)**
        metadata_field_info = [
            AttributeInfo(
                name="id",
                description="The unique identifier of the document page.",
                type="string",
            ),
            AttributeInfo(
                name="source",
                description="The filename or source of the document, typically in PDF format.",
                type="string",
            ),
            AttributeInfo(
                name="title",
                description="The title of the document or research paper.",
                type="string",
            ),
            AttributeInfo(
                name="total_pages",
                description="The total number of pages in the document.",
                type="integer",
            ),
            AttributeInfo(
                name="doi",
                description="The Digital Object Identifier (DOI) of the research paper, if available.",
                type="string",
            ),
        ]
        @sleep_and_retry
        @limits(calls=REQUESTS, period=PERIOD)
        @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=1, max=30))
        def _invoke_llm(ensemble_retriever, query: str):
            """Helper to invoke LLM with rate limiting and retry logic."""
            return ensemble_retriever.invoke(query)
        doc =[]
        print("\nLoading context from\n")
        for pdf in tqdm(self.pdf_files[:2]):
            try:
                query_retriever = SelfQueryRetriever.from_llm(
                    llm=self.llm2,
                    vectorstore=self.vectore_store,
                    document_contents="Extracted text from a comprehensive chemistry research paper covering the abstract, experimental methods, results, discussion, and supplementary data.",
                    metadata_field_info=metadata_field_info,
                    search_kwargs={"k": top_k, "filter": {"source": pdf}}
                )
                # 🔍 **Multi-Query Retriever (Diverse Queries)**
                multi_query_retriever = MultiQueryRetriever.from_llm(
                    retriever=query_retriever,
                    llm=self.llm2
                )
                # 🎯 **Ensemble Retriever (Combining Both)**
                ensemble_retriever = EnsembleRetriever(
                    retrievers=[query_retriever, multi_query_retriever],
                    weights=[0.5, 0.5]
                )
                # Retrieve documents
                documents = _invoke_llm(ensemble_retriever,query)
                # print(f"Total documents retrieved from 1.pdf: {len(documents)}\n")
                # print(documents)
                doc.append(documents)
            except Exception as e:
                if "429" in str(e) or "ResourceExhausted" in str(e):
                    logger.warning("Rate limit exceeded. Retrying with exponential backoff...")
                    raise e  # Let tenacity handle retries
                else:
                    logger.error(f"Error retrieving context for file {pdf}: {str(e)}")
        return doc
    
    def clear_chat_history(self):
        self.chat_history_manager.clear_history()
    
    def retrieve_best_example(self, query: str, examples: List[Any]) -> List[Any]:
        """
        Select the best matching example pair from the provided examples based on the query.
        The examples list is expected to have pairs of messages (HumanMessage then AIMessage).
        
        :param query: The user's query.
        :param examples: List of example messages (alternating Human and AI messages).
        :return: A list containing a pair [HumanMessage, AIMessage] that best matches the query.
        """
        logger.info("Retrieving best matching example for query")
        best_example = None
        best_ratio = 0.0
        
        # Iterate over examples in pairs (even index = HumanMessage, odd index = AIMessage)
        for i in range(0, len(examples), 2):
            human_msg = examples[i]
            ratio = difflib.SequenceMatcher(None, query.lower(), human_msg.content.lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_example = examples[i:i+2]
                
        if best_example:
            logger.info("Selected example with similarity ratio %.2f", best_ratio)
            return best_example
        else:
            logger.warning("No matching example found; returning default example.")
            return examples[0:2]
    
    def extract_citations(self, context: list[SystemMessage]) -> str:
        """
        Extract citations from the provided context messages using Kor.
        
        This function concatenates the content of the context messages into a single text block
        and uses Kor to extract citation details. For each citation, the extraction schema expects:
        - Source_ID: an integer (from "Source ID:")
        - Article_ID: a unique identifier for the citation (UUID format)
        - Article_Snippet: a short excerpt from the "Article Snippet:" field
        - Article_Title: the text following "Article Title:"
        - Article_Source: the text following "Article Source:"
        
        The output is a JSON object with a key "citations" mapping to a list of citation objects.
        """
        def parse_citations(kor_response: dict) -> dict:
            """
            Parse the Kor output response into a dictionary without remapping keys.
            
            The function attempts multiple strategies to extract a valid JSON:
            1. Extract a JSON block wrapped in triple backticks (```json ... ```).
            2. Remove <json> and </json> tags if present.
            3. Use the raw text as-is.
            4. Convert the "data" field to a JSON string.
            
            If parsing fails due to extra trailing characters, the function trims the candidate
            at the last '}' and retries. It iterates over these candidate strings until it finds
            a valid parsed response with non-empty citation data, or raises an error.
            """
            
            def try_parse(candidate: str) -> dict:
                logger.debug("Attempting to parse candidate JSON: %s", candidate[:100])
                try:
                    logger.debug("Candidate parsed successfully.")
                    return json.loads(candidate)
                except json.JSONDecodeError as e:
                    # If there's extra trailing data, trim candidate to last '}'
                    logger.warning("JSONDecodeError encountered: %s", e)
                    pos = candidate.rfind("}")
                    if pos != -1:
                        try:
                            trimmed = candidate[:pos+1]
                            logger.debug("Attempting to parse trimmed candidate: %s", trimmed[:100])
                            return json.loads(trimmed)
                        except Exception :
                            pass
                    raise e

            candidates = []
            raw_text = kor_response.get("raw", "").strip()
            logger.info("Raw text from Kor response: %s", raw_text[:100])
            # Candidate 1: Extract JSON block wrapped in triple backticks.
            match = re.search(r"```json\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
            if match:
                candidates.append(match.group(1))
                logger.info("Candidate 1 extracted from triple backticks:")
            # Candidate 2: If raw_text starts with <json>, extract up to the first occurrence of </json>
            if raw_text.startswith("<json>"):
                # Split on </json> and take the first part after <json>
                temp = raw_text[len("<json>"):].split("</json>")[0].strip()
                candidates.append(temp)
                logger.info("Candidate 2 extracted by stripping <json> tags: %s", temp[:100])
            
            # Candidate 3: Use the raw text itself.
            if raw_text:
                candidates.append(raw_text)
                logger.info("Candidate 3 using raw text itself.")
            # Candidate 4: If "data" exists in the response, try to use its JSON representation.
            data_part = kor_response.get("data")
            if data_part:
                try:
                    candidates.append(json.dumps(data_part))
                    temp12=json.dumps(data_part)
                    logger.info("Candidate 4 from data field:")
                except Exception:
                    pass

            parsed = None
            for candidate in candidates:
                try:
                    candidate_obj = try_parse(candidate)
                    # Check if candidate_obj contains a citations list
                    if isinstance(candidate_obj, dict):
                        # Handle nested structure: {"citations": {"citations": [...]}}
                        if "citations" in candidate_obj:
                            inner = candidate_obj["citations"]
                            if isinstance(inner, dict) and "citations" in inner and inner["citations"]:
                                parsed = {"citations": inner["citations"]}
                                break
                            elif isinstance(inner, list) and inner:
                                parsed = candidate_obj
                                break
                        else:
                            # If no "citations" key exists but candidate_obj is non-empty, accept it.
                            if candidate_obj:
                                parsed = candidate_obj
                                break
                except Exception as e:
                    continue

            if parsed is None or not parsed:
                logger.error("All candidates failed to produce valid citation data.")
                raise ValueError("Failed to parse a valid JSON with citation data from the Kor response.")
            logger.info("Successfully parsed citation data.")
            return parsed
        
        
        logger.info("Citation chain executing")
        try:
            # Concatenate the context messages into a single string.
            context_text = "\n\n".join(msg.content for msg in context)

            # Convert the Citations Pydantic model into a Kor schema.
            schema, validator = from_pydantic(
                Citations,
                description="Extract citation details from the given context. Each citation should include Source_ID, Article_ID, Article_Snippet, Article_Title, and Article_Source.",
                examples=[
                    (
                        "Source ID: 0\nArticle ID: 5a88139a-d5bf-4a83-96ed-2ad5f57b978d\nArticle Title: Memristive Devices from CuO Nanoparticles\nArticle Snippet: The device exhibits robust switching with a ratio of 103, supporting stable memory.\nArticle Source: 1.pdf\nmetadata: {...}",
                        {
                            "citations": [
                                {
                                    "Source_ID": 0,
                                    "Article_ID": "5a88139a-d5bf-4a83-96ed-2ad5f57b978d",
                                    "Article_Snippet": "The device exhibits robust switching with a ratio of 103",
                                    "Article_Title": "Memristive Devices from CuO Nanoparticles",
                                    "Article_Source": "1.pdf"
                                }
                            ]
                        }
                    )
                ],
                many=False
            )
            
            # Create an extraction chain using Kor.
            # Use the LLM configured for citations (self.llm_citation).
            chain = create_extraction_chain(
                self.llm_citation,
                schema,
                encoder_or_encoder_class="json",
                validator=validator
            )
            
            # Invoke the chain with the concatenated context text.
            result = chain.invoke(context_text)
            logger.info("Citation chain execution complete")
            # Return the extracted citations as a JSON string.
            return json.dumps(parse_citations(result), indent=4, ensure_ascii=False)
        
        except Exception as e:
            logger.error("Exception in Kor citation extraction: %s", str(e))
            return "{}"


    @sleep_and_retry
    @limits(calls=REQUESTS, period=PERIOD)
    def generate_response(self, query:str):
        logger.info(f"Generating response")
        """Generate response with RAG and chat history"""
        # Retrieve context
        context_docs = self.retrieve_context(query)
        context_docs = context_docs[0]
        context_messages = [
                SystemMessage(content=f"Source ID: {i}\nArticle ID: {doc.metadata['id']}\nArticle Title: {doc.metadata['title']}\nArticle Snippet: {doc.page_content}\nArticle Source: {doc.metadata['source']}\nmetadata: {doc.metadata}\n")
                for i,doc in enumerate(context_docs)
        ]

        # Create prompt template
        prompt_template, example_messages = self.create_prompt_template()
        best_example = self.retrieve_best_example(query,example_messages)
        
        try:
            # Prepare chain
            non_structured_chain = prompt_template | self.llm2
            chain = prompt_template | self.llm
            if self.remote_llm:
                non_structured_response = non_structured_chain.invoke({
                    "history": self.chat_history_manager.get_message_history(limit=2),
                    "context":context_messages,
                    "query": query
                })
                # Wait before next request to enforce rate limit
                time.sleep(PERIOD / REQUESTS)
                try:
                    structured_response = self.preprocess_text(non_structured_response.content)
                    structured_response = Data_Objects(data=[Extract_Data(**structured_response)])
                    structured_response = structured_response.to_json_string()
                    citations_response = self.extract_citations(context_messages)
                except Exception as e:
                    logger.error("Exception occurred in Parsing: %s", str(e))
                    structured_response = self.llm.invoke(non_structured_response.content)
                    structured_response = structured_response.to_json_string()
                    citations_response = self.extract_citations(context_messages)
                    logger.info("Used Structured LLM on non_structured_response")

                import pathlib
                pathlib.Path("./filtered_output/context" + ".txt").write_bytes(str(context_messages).encode())
                pathlib.Path("./filtered_output/sample_response" + ".json").write_bytes(structured_response.encode())
                pathlib.Path("./filtered_output/citation_response" + ".json").write_bytes(citations_response.encode())
                self.chat_history_manager.add_user_message(query)
                self.chat_history_manager.add_ai_message(structured_response)
                self.chat_history_manager.save_history()

                return {
                    "structured_response":structured_response,
                    "non_Structured_response":non_structured_response.content,
                    "citations":citations_response
                }
            else:
                
                
                try:
                    non_structured_response = non_structured_chain.invoke({
                        "history": self.chat_history_manager.get_message_history(limit=2),
                        "examples": best_example,
                        "context":context_messages,
                        "query": query
                    })
                    structured_response = self.preprocess_text(non_structured_response.content)
                    structured_response = Data_Objects(data=[Extract_Data(**structured_response)])
                    structured_response = structured_response.to_json_string()
                    citations_response = self.extract_citations(context_messages)
                except Exception as e:
                    logger.error("Exception occurred in Parsing: %s", str(e))
                    structured_response = chain.invoke({
                        "history": self.chat_history_manager.get_message_history(limit=2),
                        "examples": best_example,
                        "context":context_messages,
                        "query": query
                    })
                    structured_response = structured_response.to_json_string()
                    citations_response = self.extract_citations(context_messages)
                    logger.info("Used Structured LLM on non_structured_response")

                import pathlib
                pathlib.Path("./filtered_output/context" + ".txt").write_bytes(str(context_messages).encode())
                pathlib.Path("./filtered_output/sample_response" + ".json").write_bytes(structured_response.encode())
                pathlib.Path("./filtered_output/citation_response" + ".json").write_bytes(citations_response.encode())
                self.chat_history_manager.add_user_message(query)
                self.chat_history_manager.add_ai_message(structured_response)
                self.chat_history_manager.save_history()
                return {
                    "structured_response":structured_response,
                    "non_Structured_response":non_structured_response.content,
                    "citations":citations_response
                }
        except Exception as e:
            print(f"Error generating response: {e}")
            logger.error("Exception occurred: %s", str(e))
            return {
                "structured_response":"I'm sorry, I couldn't process your request.",
                "non_Structured_response":"I'm sorry, I couldn't process your request.",
                "citations":"I'm sorry, I couldn't process your request."
            }


