from document_loader import DocLoader
from textsplitter import ProcessText
from tqdm import tqdm
from uuid import uuid4
from langchain_core.documents import Document
import os
from scheme import Data
from general_schema import Genral_Data
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from typing import List, Dict, Any
from langchain_ollama import OllamaLLM
from langchain.chains.llm import LLMChain
from langchain_core.output_parsers import PydanticOutputParser
import torch


class ChatHistoryManager:
    def __init__(self, max_history_length=15):
        self.max_history_length = max_history_length
        self.history: List[Dict[str, Any]] = []

    def add_user_message(self, message: str):
        """Add a user message to the chat history"""
        self.history.append({
            "role": "human",
            "content": message
        })
        self._trim_history()

    def add_ai_message(self, message: str):
        """Add an AI message to the chat history"""
        self.history.append({
            "role": "ai",
            "content": message
        })
        self._trim_history()

    def _trim_history(self):
        """Trim history to maintain maximum length"""
        if len(self.history) > self.max_history_length:
            self.history = self.history[-self.max_history_length:]

    def get_message_history(self):
        """Convert history to LangChain message objects"""
        return [
            HumanMessage(content=msg['content']) if msg['role'] == 'human' 
            else AIMessage(content=msg['content']) 
            for msg in self.history
        ]

    def clear_history(self):
        """Clear the entire chat history"""
        self.history = []

class RAGChatAssistant:
    def __init__(self,dirpath:str="./PDF/"):
        # path to uploaded/local pdf's
        self.dirpath = dirpath
        # device agnostic code
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        # chat History manager
        self.chat_history_manager = ChatHistoryManager()
        #LLM
        self.llm = OllamaLLM(model='phi3:mini',device=device,temperature = 0.5,request_timeout=360.0,format="json")
        # Create a Pydantic output parser
        self.output_parser = PydanticOutputParser(pydantic_object=Data)
        # Loading vectore store
        if os.path.exists("./faiss_index"):
            print("\n Skipping creating indexes as local index is present \n")
            self.vectore_store = self.load_vectors()
        else:
            print("\n Creating Vectore Index and Storing Locally \n")
            self.vectore_store = self.create_vectors()

    def create_vectors(self):
        document_loader = DocLoader(self.dirpath)
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

    def create_prompt_template(self):
        
        examples = [
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
                        "source":"Nanoparticles.pdf"
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
                        "source":"10.pdf"
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
                        "source":"12.pdf"
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
                        "source":"1.pdf"
                    }
                }
            }
        ]
        # Convert examples to message format
        example_messages = []
        for example in examples:
            example_messages.extend([
                HumanMessage(content=example["input"]),
                AIMessage(content=str(example["output"]))
            ])
        prompt_template = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=(
                    "system",
                    "You are an expert extraction algorithm. "
                    "Only extract relevant information from the text. "
                    "If you do not know the value of an attribute asked to extract, "
                    "return null for the attribute's value.",
                )),
                # Please see the how-to about improving performance with
                # reference examples.
                MessagesPlaceholder(variable_name='history',n_messages=2),
                MessagesPlaceholder(variable_name='examples',n_messages=1),
                MessagesPlaceholder(variable_name='context'),
                ("human", "{query}")
            ]
        ).partial(format_instructions=self.output_parser.get_format_instructions())
        
        return prompt_template,example_messages

    def load_vectors(self):
        Textprocess = ProcessText()
        vectore_store=Textprocess.load_vectors("faiss_index")
        return vectore_store
    
    def retrieve_context(self, query:str, top_k=3):
        """Retrieve relevant documents from vector store"""
        return self.vectore_store.similarity_search(query, k=top_k)
    
    def generate_response(self, query:str):
        """Generate response with RAG and chat history"""
        # Retrieve context
        context_docs = self.retrieve_context(query)
        context_messages = [
                HumanMessage(content=doc.page_content) 
                for doc in context_docs
        ]

        # Create prompt template
        prompt_template, example_messages = self.create_prompt_template()

        # Prepare chain
        chain = prompt_template | self.llm | self.output_parser
        
        try:
            response = chain.invoke({
                "history": self.chat_history_manager.get_message_history(),
                "examples": example_messages,
                "context":context_messages,
                "query": query
            })
            # Add messages to chat history
            self.chat_history_manager.add_user_message(query)
            self.chat_history_manager.add_ai_message(response.content)
            return {
                "response": response.content,
                "context_docs": context_docs
            }
        except Exception as e:
            print(f"Error generating response: {e}")
            return {
                "response": "I'm sorry, I couldn't process your request.",
                "context_docs": []
            }
        
if __name__=="__main__":
    obj = RAGChatAssistant()
    result = obj.generate_response("Analyze the switching characteristics of a material synthesized via chemical methods")
    print("\nAssistant:", result['response'])
