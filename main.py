from rag_assistant import RAGChatAssistant
import logging
import streamlit as st
import json
from ChatHistory import ChatHistoryManager
from db import get_user,get_chat_titles_and_ids
import requests
from io import BytesIO
from PIL import Image

logger = logging.getLogger(__name__)

# Define the sample prompt (pre-populated default prompt)
if st.session_state.logged_in:
    # Sidebar for profile details appears as usual.
     # Display user details and chat titles.
    user_record = get_user(st.session_state.user_id)
    chat_history = get_chat_titles_and_ids(st.session_state.user_id)
    with st.sidebar:
        st.markdown("## Profile")
        if user_record:
            profile_username = user_record.get("username","No username found")
            profile_email = user_record.get("email", "No email found")
            picture = user_record.get("picture",None)
            logger.info("Loaded user record from DB for oidc_user_id: %s", st.session_state.user_id)
        else:
            logger.info("No user record found in DB for oidc_user_id: %s", st.session_state.user_id)
    
        if picture:
            response = requests.get(picture)
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                st.image(image, width=100,caption="Profile Picture")
            else:
                st.image(picture, width=100,caption="Profile Picture")
        else:
            st.info("No profile picture available.")
        st.write(f"**Username:** {profile_username}")
        st.write(f"**Email:** {profile_email}")
    
        if st.button("Log Out"):
            logger.info("User requested logout from Login tab.")
            st.session_state.logged_in = False
            st.logout()
            st.rerun()
    
        st.markdown("## Chat Titles")
        if chat_history:
            for chat in chat_history:
                st.markdown(f"- **{chat['title']} (Chat ID: **{chat['chat_id']})**")
        else:
            st.info("No chat titles available.")
    sample_prompt = """
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

    assistant = RAGChatAssistant(user_id=st.session_state.user_id,remote_llm=True)
    manager = ChatHistoryManager(user_id=st.session_state.user_id)
    if st.session_state.chat_id ==0:
        manager.create_new_chat("New Chat History created")
    else:
        history=manager.load_chat(chat_id=st.session_state.chat_id[0])

    def chat_with_assistant(query: str):
        """
        This function receives a user query, calls the generate_response method of the assistant,
        and returns the structured response, non-structured response, and citations.
        """
        try:
            result = assistant.generate_response(query,manager.get_message_history(limit=2))
            # Extract the different parts from the returned dictionary.
            structured_response = result.get("structured_response", "No structured response returned.")
            non_structured_response = result.get("non_Structured_response", "No non-structured response returned.")
            citations = result.get("citations", "No citations returned.")
            manager.add_citation_message(citations)
            manager.add_user_message(query)
            manager.add_ai_message(structured_response,save_hist=True)
            return structured_response, non_structured_response, citations
        except Exception as e:
            logger.error("Error in chat_with_assistant: %s", e)
            return "Error generating response.", "", ""

    st.set_page_config(page_title="RAG Chat Assistant", layout="wide")
    st.title("RAG Chat Assistant")
    st.markdown("Enter a query and get responses generated by the RAG Chat Assistant. The sample prompt is pre-populated below.")

    # Input area for the prompt
    query_input = st.text_area("User Query", value=sample_prompt, height=300)

    # When the user clicks the "Submit" button, run the assistant
    if st.button("Submit"):
        with st.spinner("Generating response...",show_time=True):
            structured_response, non_structured_response, citations = chat_with_assistant(query_input)
        
        st.subheader("Structured Response (JSON)")
        try:
            # Try loading the structured response as JSON
            structured_json = json.loads(structured_response)
        except Exception:
            structured_json = {"response": structured_response}
        st.json(structured_json)
        
        st.subheader("Non-Structured Response (Markdown)")
        st.markdown(non_structured_response)
        
        st.subheader("Citations (JSON)")
        try:
            citations_json = json.loads(citations)
        except Exception:
            citations_json = {"citations": citations}
        st.json(citations_json)
else:
    st.info("Please log in to proceed.")
    st.switch_page("login.py")