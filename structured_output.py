from rag_assistant import RAGChatAssistant
import logging
import streamlit as st
import json
from ChatHistory import ChatHistoryManager
from utils import profile_page_loader
from db import update_chat_ids

logger = logging.getLogger(__name__)

def chat_with_assistant(query: str,manager: ChatHistoryManager,assistant: RAGChatAssistant):
        """
        This function receives a user query, calls the generate_response method of the assistant,
        and returns the structured response, non-structured response, and citations.
        """
        try:
            result = assistant.generate_structured_response(query,manager.get_message_history(limit=2))
            # Extract the different parts from the returned dictionary.
            structured_response = result.get("structured_response", "No structured response returned.")
            non_structured_response = result.get("non_Structured_response", "No non-structured response returned.")
            citations = result.get("citations", "No citations returned.")
            manager.add_citation_message(citations)
            manager.add_ai_message(non_structured_response)
            manager.add_user_message(query)
            manager.add_ai_message(structured_response,save_hist=True)
            return structured_response, non_structured_response, citations
        except Exception as e:
            logger.error("Error in chat_with_assistant: %s", e)
            return "Error generating response.", "", ""
        
def generate_response(manager: ChatHistoryManager,assistant: RAGChatAssistant):
    with st.spinner("Generating response..."):
        structured_response, non_structured_response, citations = chat_with_assistant(st.session_state.prompt, manager,assistant)

    st.subheader("Structured Response (JSON)")
    try:
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

def _load_chat(history,history_placeholder):
    st.markdown("### History")
    st.subheader(f"Chat Title: {history['title']}")
    st.subheader("Prompt")
    st.markdown(history['history'][-2]['content'])
    st.subheader("Structured Response (JSON)")
    try:
        structured_json = json.loads(history['history'][-1]['content'])
        st.json(structured_json)
    except Exception as e:
        st.error("Error parsing structured response: " + str(e))

    st.subheader("Non-Structured Response (Markdown)")
    st.markdown(history['history'][-3]['content'])

    st.subheader("Citations (JSON)")
    try:
        citations_json = json.loads(history['history'][-4]['content'])
        st.json(citations_json)
    except Exception as e:
        st.error("Error parsing citations: " + str(e))
    if st.button("Clear UI Content"):
        history_placeholder.empty()

# sample_prompt = """
# Please read the provided PDF thoroughly and extract the following quantities. Your output must be a table with two columns: "Quantity" and "Extracted Value". For each of the items listed below, provide the extracted value exactly as it appears in the document. If an item is not found, simply enter "N/A" for that field. Ensure that any numerical values include their associated units (if applicable) and that you handle multiple values consistently.

# Extract the following items:
# - switching layer material
# - synthesis method
# - top electrode
# - thickness of top electrode in nanometers
# - bottom electrode
# - thickness of bottom electrode in nanometers
# - thickness of switching layer in nanometers
# - type of switching
# - endurance
# - retention time in seconds
# - memory window in volts
# - number of states
# - conduction mechanism type
# - resistive switching mechanism
# - paper name
# - source (pdf file name)

# Instructions:
# 1. Analyze the entire PDF document to locate all references to the above items.
# 2. Extract each quantity with precision; include any units and relevant details.
# 3. If multiple values are present for a single item, list them clearly (e.g., separated by commas).
# 4. Format your output strictly as a table with two columns: one for the "Quantity" and one for the "Extracted Value".
# 5. Do not include any extra text, headings, or commentary—only the table is required.
# 6. If an item cannot be found, record it as "N/A" in the "Extracted Value" column.
# """
if st.session_state.logged_in:
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = ""
    profile_page_loader(logger,on_chat_page=True)
    st.title("RAG Chat Assistant")
    assistant = RAGChatAssistant(
        user_id=st.session_state.user_id,
        Data_Objects=st.session_state.current_schema,
        mapping=st.session_state.mapping,
        remote_llm=True
    )
    manager = ChatHistoryManager(user_id=st.session_state.user_id)

    # Display history if current chat exists
    if st.session_state.current_chat_id != "" and len(st.session_state.chat_id) != 0:
        history = manager.load_chat(chat_id=st.session_state.current_chat_id)
        history_placeholder = st.empty()
        with history_placeholder.container():
            _load_chat(history,history_placeholder)

    # Buttons for interaction
    if st.button("Generate New Response"):
        if st.session_state.prompt.strip() != "":
            generate_response(manager,assistant)
        else:
            st.warning("Prompt cannot be empty.")

    if st.button("Create New Chat"):
        if st.session_state.prompt.strip() != "":
            new_title = assistant.generate_title(st.session_state.prompt)
            new_chat_id = manager.create_new_chat(new_title)
            st.session_state.chat_id.append(new_chat_id)
            st.session_state.current_chat_id = new_chat_id
            update_chat_ids(st.session_state.user_id, st.session_state.chat_id)
            generate_response(manager,assistant)
        else:
            st.warning("Prompt cannot be empty.")
else:
    st.error("You need to be logged in to access this feature.")
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.chat_id = []
    st.session_state.title = []
    st.session_state.current_chat_id = ""
    st.switch_page("login.py")