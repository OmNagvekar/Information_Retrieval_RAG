from rag_assistant import RAGChatAssistant
import logging
import sys
import os
import time
from datetime import datetime, timedelta
import threading
import gradio as gr

TODAY_DATE = datetime.now().strftime("%Y-%m-%d")
LOG_DIR='Logs'
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"logs_{TODAY_DATE}.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(filename)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE,encoding="utf-8"),  # Save logs locally
        logging.StreamHandler(sys.stdout),  # Also print logs in console
    ],
)
def delete_old_logs():
    """Delete log files older than 1 day if they contain no errors (or only a specific memory error),
    and delete files older than 3 days regardless. Files in use are skipped.
    """
    while True:
        try:
            now = datetime.now()
            for filename in os.listdir(LOG_DIR):
                if filename.startswith("logs_") and filename.endswith(".log"):
                    file_path = os.path.join(LOG_DIR, filename)

                    # Extract date from filename (assumes format "logs_YYYY-MM-DD.log")
                    file_date_str = filename[5:15]
                    try:
                        file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
                    except Exception as e:
                        logging.error("Failed to parse date from filename %s: %s", filename, e)
                        continue

                    # Process files older than 1 day
                    if now - file_date > timedelta(days=1):
                        try:
                            with open(file_path, "r", encoding="utf-8") as log_file:
                                content = log_file.read()
                        except Exception as e:
                            logging.error("Error reading file %s: %s", filename, e)
                            continue

                        if "ERROR" not in content:
                            try:
                                os.remove(file_path)
                                logging.info("Deleted old log: %s", filename)
                            except Exception as e:
                                if hasattr(e, "winerror") and e.winerror == 32:
                                    logging.warning("File %s is in use; skipping deletion.", filename)
                                else:
                                    logging.error("Error deleting file %s: %s", filename, e)
                        else:
                            # Check if errors are only due to the memory issue
                            error_lines = [line for line in content.splitlines() if "ERROR" in line]
                            if error_lines and all("model requires more system memory" in line for line in error_lines):
                                try:
                                    os.remove(file_path)
                                    logging.info("Deleted old log (only memory error present): %s", filename)
                                except Exception as e:
                                    if hasattr(e, "winerror") and e.winerror == 32:
                                        logging.warning("File %s is in use; skipping deletion.", filename)
                                    else:
                                        logging.error("Error deleting file %s: %s", filename, e)

                    # Delete files older than 3 days regardless of content
                    if now - file_date > timedelta(days=3):
                        try:
                            os.remove(file_path)
                            logging.info("Deleted old log (older than 3 days): %s", filename)
                        except Exception as e:
                            if hasattr(e, "winerror") and e.winerror == 32:
                                logging.warning("File %s is in use; skipping deletion.", filename)
                            else:
                                logging.error("Error deleting file %s: %s", filename, e)

        except Exception as e:
            logging.error("Error in log cleanup: %s", e, exc_info=True)

        time.sleep(3600)  # Run every hour
        
        
# Define the sample prompt (pre-populated default prompt)
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

cleanup_thread = threading.Thread(target=delete_old_logs, daemon=True)
cleanup_thread.start()
assistant = RAGChatAssistant(user_id="abc_123",remote_llm=True)

def chat_with_assistant(query: str):
    """
    This function receives a user query, calls the generate_response method of the assistant,
    and returns the structured response, non-structured response, and citations.
    """
    try:
        result = assistant.generate_response(query)
        # Extract the different parts from the returned dictionary.
        structured_response = result.get("structured_response", "No structured response returned.")
        non_structured_response = result.get("non_Structured_response", "No non-structured response returned.")
        citations = result.get("citations", "No citations returned.")
        return structured_response, non_structured_response, citations
    except Exception as e:
        logging.error("Error in chat_with_assistant: %s", e)
        return "Error generating response.", "", ""

# Create a Gradio Interface
iface = gr.Interface(
    fn=chat_with_assistant,
    inputs=gr.Textbox(lines=15, placeholder="Enter your query here...", value=sample_prompt, label="User Query"),
    outputs=[
        gr.Textbox(label="Structured Response"),
        gr.Markdown(label="Non-Structured Response"),
        gr.Textbox(label="Citations")
    ],
    title="RAG Chat Assistant",
    description="Enter a query and get responses generated by the RAG Chat Assistant. The sample prompt is pre-populated below.",
    allow_flagging="never"
)

if __name__ == "__main__":
    iface.launch(server_port=8080,debug=True)