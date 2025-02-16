from document_loader import DocLoader
from textsplitter import ProcessText
from tqdm import tqdm
from uuid import uuid4
from langchain_core.documents import Document
import os
from scheme import Data,Extract_Text
from gemini_scheme import Data_Objects
from ratelimit import limits, sleep_and_retry
from tenacity import retry, stop_after_attempt, wait_exponential
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from typing import List, Dict, Any
from langchain_ollama.chat_models import ChatOllama
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

logger = logging.getLogger(__name__)
# Define rate limiter (2 requests per minute)
REQUESTS = 2
PERIOD = 60  # seconds

class RAGChatAssistant:
    def __init__(self,user_id:str,dirpath:str="./PDF/",remote_llm:bool=False,ollama_model:str='phi3:mini'):
        logger.info("Initializing RAGChatAssistant")
        # path to uploaded/local pdf's
        self.dirpath = dirpath
        # device agnostic code
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Using device: {self.device}")
        # chat History manager
        self.chat_history_manager = ChatHistoryManager(user_id=user_id)
        # Intializing objects
        self.Textprocess = ProcessText(device=self.device)
        self.document_loader = DocLoader(self.dirpath,filter_text=True)
        self.pdf_files =[os.path.basename(pdfs) for pdfs in self.document_loader.file_path]
        #LLM
        self.remote_llm =remote_llm
        if remote_llm:
            try:
                with open("gemini_key.txt",'r') as f:
                    key = f.read()
                llm = ChatGoogleGenerativeAI(model='gemini-1.5-flash',max_retries=2,google_api_key=key,disable_streaming=False,convert_system_message_to_human=True,temperature=0.5,cache=False)
                self.llm = llm.with_structured_output(Data_Objects)
                self.llm2 =llm
                logger.info("LLM initialized with gemini-1.5-flash")
            except Exception as e:
                logger.error("Failed to intialize the Gemini LLM gemini-1.5-flash %s",str(e))
                self.llm = ChatOllama(model=ollama_model,device=self.device,temperature = 0.5,request_timeout=360.0,format='json')
                self.llm2 =ChatOllama(model=ollama_model,device=self.device,temperature = 0.5,request_timeout=360.0)
                logger.info(f"LLM initialized with {ollama_model}")
                self.remote_llm=False
        else:
            self.llm = ChatOllama(model=ollama_model,device=self.device,temperature = 0.5,request_timeout=360.0,format='json')
            self.llm2 =ChatOllama(model=ollama_model,device=self.device,temperature = 0.5,request_timeout=360.0)
            logger.info(f"LLM initialized with {ollama_model}")
            # Pydantic output parser
            self.output_parser = PydanticOutputParser(pydantic_object=Data)
        # Structured LLM
        # self.structured_llm = self.llm.with_structured_output(schema=Data)
        # Loading vectore store
        if os.path.exists("./chroma_db"):
            print("\n Skipping creating indexes as local index is present \n")
            logger.info("Local Chroma index found. Loading existing vectors.")
            self.vectore_store = self.load_vectors(self.Textprocess)
        else:
            print("\n Creating Vectore Index and Storing Locally \n")
            logger.info("No existing Chroma index found. Creating new vector index.")
            self.vectore_store = self.create_vectors(self.document_loader,self.Textprocess)

    def create_vectors(self,document_loader: DocLoader,Textprocess: ProcessText):
        logger.info("Starting vector creation process.")
        document = document_loader.pypdf_loader()
        vector_store = Textprocess.vectore_store()
        
        for doc in tqdm(document):
            processed_text =  Textprocess.splitter(doc.page_content)
            page_metadata = doc.metadata
            page_metadata.update({"id": str(uuid4())})
            doc_objects = [
                Document(
                    page_content=chunk,
                    metadata={
                        "id":page_metadata.get("id"),
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
                "input": "Extract the following data from the provided PDF and present it in a table: "
                    "(1) Input Data: switching layer material (TYM_Class), Synthesis method (SM_Class), Top electrode (TE_Class), "
                    "Thickness of Top electrode (TTE in nm), Bottom electrode (BE_Class), Thickness of bottom electrode (TBE in nm), "
                    "Thickness of switching layer (TSL in nm); "
                    "(2) Output Data: Type of Switching (TSUB_Class), Endurance (Cycles) (EC), Retention Time (RT in seconds), "
                    "Memory Window (MW in V), No. of states (MRS_Class), Conduction mechanism type (CM_Class), "
                    "Resistive Switching mechanism (RSM_Class); "
                    "(3) Reference Information: Name of the paper, DOI, Year.",
                "output": {
                    "input_data": {
                        "switching_layer_material": "CuO Nanoparticles",
                        "synthesis_method": "Chemical",
                        "top_electrode": "Platinum",
                        "thickness_of_top_electrode": 10,
                        "bottom_electrode": "Gold",
                        "thickness_of_bottom_electrode": 20,
                        "thickness_of_switching_layer": 5000
                    },
                    "output_data": {
                        "type_of_switching": "Resistive",
                        "endurance_cycles": 50,
                        "retention_time": 10000,
                        "memory_window": 1.2,
                        "number_of_states": "Binary",
                        "conduction_mechanism_type": "Space-Charge Limited Conduction",
                        "resistive_switching_mechanism": "Filamentary"
                    },
                    "reference_information": {
                        "name_of_paper": "Switching Properties of CuO Nanoparticles",
                        "doi": "https://doi.org/10.1234/exampledoi",
                        "year": 2022,
                        "source":"C:\\Users\\Om Nagvekar\\OneDrive\\Documents\\KIT Assaignment & Notes& ISRO\\Shivaji University Nanoscience Dept. Projects\\IRP\\PDF\\1.pdf"
                    }
                }
            },

            {
                "input": "Analyze the switching characteristics of a material synthesized via chemical methods",
                "output": {
                    "material_type": "CuO Nanoparticles",
                    "synthesis_method": "Chemical",
                    "switching_type": "Resistive",
                    "endurance_cycles": 50,
                    "retention_time": 1000,
                    "memory_window": 1000,
                    "paper_details": {
                        "title": "Memristive Devices from CuO Nanoparticles",
                        "doi": "https://doi.org/10.3390/nano10091677",
                        "year": 2020,
                        "source":"8.pdf"
                    }
                }
            },
            {
                "input": "Provide retention time and endurance cycles for a material using p-type CuO",
                "output": {
                    "material_type": "p-type CuO",
                    "endurance_cycles": 18,
                    "retention_time": 10000,
                    "memory_window": 10000000,
                    "paper_details": {
                        "title": "Resistive switching memory effects in p-type h-CuI/CuO heterojunctions",
                        "doi": "https://doi.org/10.1063/5.0010839",
                        "year": 2020,
                        "source":"C:\\Users\\User\\OneDrive\\Documents\\KIT Assaignment & Notes& ISRO\\PDF\\8.pdf"
                    }
                }
            },
            {
                "input": "Details about switching layer with 5000 nm thickness and its mechanisms",
                "output": {
                    "switching_layer_thickness": 5000,
                    "conduction_mechanism": "Type 1",
                    "switching_mechanism": "Resistive",
                    "paper_details": {
                        "title": "Facile synthesis and nanoscale related physical properties of CuO nanostructures",
                        "doi": "https://doi.org/10.1016/j.apsusc.2019.144903",
                        "year": 2020,
                        "source":"C:\\Users\\User\\Documents\\KIT Assaignment & Notes& ISRO\\PDF\\8.pdf"
                    }
                }
            },
            {
                "input": "Analyze the performance of a resistive switching device with a switching layer synthesized via ALD and a top electrode of Pt.",
                "output": {
                    "material_type": "HfO2",
                    "synthesis_method": "Atomic Layer Deposition",
                    "switching_type": "Bipolar",
                    "endurance_cycles": 1_000_000,
                    "retention_time": 3600,
                    "memory_window": 2.5,
                    "paper_details": {
                        "title": "Resistive Switching in HfO2-Based Devices",
                        "doi": "https://doi.org/10.1016/j.jmatpro.2021.03.012",
                        "year": 2021,
                        "source":"4.pdf"
                    }
                }
            },
            {
                "input": "Provide details of a device with an 8 nm Al2O3 switching layer synthesized via Sol-Gel.",
                "output": {
                    "material_type": "Al2O3",
                    "switching_layer_thickness": 8,
                    "synthesis_method": "Sol-Gel",
                    "switching_type": "Unipolar",
                    "endurance_cycles": 500_000,
                    "retention_time": 7200,
                    "memory_window": 1.8,
                    "paper_details": {
                        "title": "Switching Characteristics of Al2O3 Layers",
                        "doi": "https://doi.org/10.5678/j.matsci.2020.045",
                        "year": 2020,
                        "source":"Switching.pdf"
                    }
                }
            },
            {
                "input": "Details of a resistive switching device using TiO2 synthesized via PLD, with a switching layer thickness of 15 nm.",
                "output": {
                    "material_type": "TiO2",
                    "switching_layer_thickness": 15,
                    "synthesis_method": "Pulsed Laser Deposition",
                    "switching_type": "Bipolar",
                    "endurance_cycles": 2_000_000,
                    "retention_time": 10_800,
                    "memory_window": 3.2,
                    "paper_details": {
                        "title": "Advances in TiO2-Based Resistive Switching",
                        "doi": "https://doi.org/10.9101/j.nano2020.112",
                        "year": 2020,
                        "source":"Resistive_Switching.pdf"
                    }
                }
            },
            {
                "input": "Analyze the switching mechanisms of a device with a 5000 nm thick CuO switching layer.",
                "output": {
                    "switching_layer_thickness": 5000,
                    "material_type": "CuO",
                    "conduction_mechanism": "Space Charge Limited Conduction",
                    "switching_mechanism": "Filamentary",
                    "paper_details": {
                        "title": "Synthesis and Applications of CuO Nanostructures",
                        "doi": "https://doi.org/10.1021/acsnano.2020.1234",
                        "year": 2020,
                        "source":"Synthesis_and_Applications_of_CuO_Nanostructures.pdf"
                    }
                }
            },
            {
                "input": "Provide endurance cycles and retention time for a resistive switching device with Au top electrode and Al2O3 switching layer.",
                "output": {
                    "material_type": "Al2O3",
                    "top_electrode": "Au",
                    "endurance_cycles": 750_000,
                    "retention_time": 5400,
                    "paper_details": {
                        "title": "Unipolar Switching in Al2O3 Devices",
                        "doi": "https://doi.org/10.1007/snano.2022.008",
                        "year": 2022,
                        "source":"paper.pdf"
                    }
                }
            },
        ]
        # Convert examples to message format
        example_messages = []
        for example in examples:
            example_messages.extend([
                HumanMessage(content=example["input"]),
                AIMessage(content=str(example["output"]))
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
                    ("context:"),
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
            )
        return prompt_template,example_messages

    def load_vectors(self,Textprocess: ProcessText):
        vectore_store=Textprocess.load_vectors()
        logger.info("Loading vectors from Chroma index.")
        return vectore_store
    

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
        for pdf in tqdm(self.pdf_files):
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
    
    @sleep_and_retry
    @limits(calls=REQUESTS, period=PERIOD)
    def generate_response(self, query:str):
        logger.info(f"Generating response")
        """Generate response with RAG and chat history"""
        # Retrieve context
        context_docs = self.retrieve_context(query)
        context_docs = context_docs[0]
        context_messages = [
                HumanMessage(content=doc.page_content +"\n" +str(doc.metadata) + " source of this context is:" + str(doc.metadata['source']))
                for doc in context_docs
        ]

        # Create prompt template
        prompt_template, example_messages = self.create_prompt_template()
        best_example = self.retrieve_best_example(query,example_messages)
        
        
        try:
            # Prepare chain
            chain = prompt_template | self.llm
            non_structured_chain = prompt_template | self.llm2
            if self.remote_llm:
                structured_response = chain.invoke({
                    "history": self.chat_history_manager.get_message_history(limit=2),
                    "context":context_messages,
                    "query": query
                })
                non_Structured_response = non_structured_chain.invoke({
                    "history": self.chat_history_manager.get_message_history(limit=2),
                    "context":context_messages,
                    "query": query
                })
                
                structured_response = structured_response.to_json_string()
                self.chat_history_manager.add_user_message(query)
                self.chat_history_manager.add_ai_message(structured_response)
                self.chat_history_manager.save_history()
                # Wait before next request to enforce rate limit
                time.sleep(PERIOD / REQUESTS)
                return {
                    "structured_response":structured_response
                    "non_Structured_response":non_Structured_response.content
                }
            else:
                response = chain.invoke({
                    "history": self.chat_history_manager.get_message_history(limit=2),
                    "examples": best_example,
                    "context":context_messages,
                    "query": query
                })
                # parse the JSON response
                raw_response = json.loads(response.content)
                data= Data(data=[Extract_Text(**raw_response)])
                # parse the output by schema
                parser_output=self.output_parser.invoke(data.to_json_string())
                # Add messages to chat history
                self.chat_history_manager.add_user_message(query)
                self.chat_history_manager.add_ai_message(response.content)
                self.chat_history_manager.save_history()
                return {
                    "response": response.content,
                    "context_docs": context_docs,
                    "validated_output":parser_output
                }
        except Exception as e:
            print(f"Error generating response: {e}")
            logger.error("Exception occurred: %s", str(e))
            return {
                "response": "I'm sorry, I couldn't process your request.",
                "context_docs": [],
                "validated_output":""
            }
        

