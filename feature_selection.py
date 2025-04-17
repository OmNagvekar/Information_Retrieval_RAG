import streamlit as st
from utils import profile_page_loader
import logging
logger = logging.getLogger(__name__)

# Load the user's profile page (navigation, authentication, etc.)
profile_page_loader(logger)

st.markdown("# Feature Selection")
st.markdown("Explore and try out our available features:")

# ------------------------------------------------------------------------------
st.markdown("---")
st.markdown("## 1. Chat with PDFs")
st.markdown(
    """
    **Description:**
    Interact with PDF documents by uploading your files and querying their content.
    
    **How It Works:**
    - **Step 1:** Upload one or more PDF files.
    - **Step 2:** The system extracts text and relevant data from these PDFs.
    - **Step 3:** Ask questions based on the pdf's content and receive insightful responses.
    
    **Additional Info:**
    - The uploaded PDFs can later be reused for generating structured outputs.
    - This feature is particularly useful for handling multiple documents at once.
    
    **Use Case:**
    Ideal for quickly extracting insights from academic papers, research documents, and bulk reports.
    """
)

if st.button("Chat with PDFs"):
    st.info("Feature under development: Soon you will be able to upload PDF files and chat with their content.")

# ------------------------------------------------------------------------------
st.markdown("---")
st.markdown("## 2. Structured Output Feature")
st.markdown(
    """
    **Description:**
    This feature produces a structured JSON output according to a JSON schema provided by the user.
    
    **How It Works:**
    - **Step 1:** Enter your desired JSON schema in a form. For example:
        You have to enter the extracting feature name in snake case and the description of the feature to be extracted so the results will be better.
        For example:
        - **feature name:** switching_layer_material
        - **description:** "The material used in the switching layer of the device. For example, it could be a metal oxide such as TiO2 or HfO2, or another compound known for resistive switching behavior."
    
    - **Example Output:**
    ```json
    {
        "data": [
            {
                "numeric_value": null,
                "switching_layer_material": "Copper Oxide (CuxO)",
                "synthesis_method": "solution-processed",
                "top_electrode": "Au",
                "top_electrode_thickness": null,
                "bottom_electrode": "ITO",
                "bottom_electrode_thickness": null,
                "switching_layer_thickness": null,
                "switching_type": "bipolar",
                "endurance_cycles": "200 cycles",
                "retention_time": "10<sup>4</sup> sec",
                "memory_window": null,
                "num_states": "2",
                "conduction_mechanism": "mixed ionic electronic conduction (MIEC)",
                "resistive_switching_mechanism": "filamentary, interface",
                "additionalProperties": null,
                "paper_name": "Resistive Switching Characteristics in Solution-Processed Copper Oxide (CuxO) by Stoichiometry Tuning",
                "source": "10.pdf"
            }
        ]
    }
    ```
    
    - **Step 2:** Upload one or multiple PDF files (bulk upload is supported).
    - **Step 3:** The system processes the PDFs, which may take around one minute, to extract and generate data that conforms to your provided JSON schema.
    - **Step 4:** The final structured JSON output is displayed.
    
    **Additional Info:**
    - The PDFs uploaded in this process can also be later used for the "Chat with PDFs" feature, and vice versa.
    
    **Use Case:**
    Ideal for transforming unstructured text from PDFs into well-organized JSON data for analysis or further automation.
    """
)


if st.button("Structured Output Feature"):
    st.switch_page("form.py")
    
# ------------------------------------------------------------------------------
st.markdown("---")
st.markdown("## 3. AgenticRAG Feature")
st.markdown(
    """
    **Description:**
    AgenticRAG integrates real-time web search with retrieval augmented generation (RAG)
    to deliver responses enriched with the latest available information.
    
    **How It Works:**
    - **Step 1:** Submit your query.
    - **Step 2:** The system fetches updated data from the web.
    - **Step 3:** The assistant blends this external information with its internal models to generate a detailed response.
    
    **Use Case:**
    Perfect for when you need answers that incorporate current, ever-changing information (such as news or live data).
    """
)

if st.button("AgenticRAG Feature"):
    st.info("Feature under development: Web-enhanced response generation using AgenticRAG will be available soon!")
