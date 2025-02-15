from rag_assistant import RAGChatAssistant
import logging
import sys
import os
import time
from datetime import datetime, timedelta
import threading

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

if __name__=="__main__":
    cleanup_thread = threading.Thread(target=delete_old_logs, daemon=True)
    cleanup_thread.start()
    obj = RAGChatAssistant(user_id="abc_123",remote_llm=True)
    # obj.clear_chat_history()
    result = obj.generate_response("""
        Please read the provided PDF thoroughly and extract the following quantities. Your output must be a table with two columns: "Quantity" and "Extracted Value". For each of the items listed below, provide the extracted value exactly as it appears in the document. If an item is not found, simply enter "N/A" for that field. Ensure that any numerical values include their associated units (if applicable) and that you handle multiple values consistently.

        Extract the following items:
        - Switching layer material
        - Synthesis method
        - Top electrode
        - Thickness of top electrode in nanometers
        - Bottom electrode
        - Thickness of bottom electrode in nanometers
        - Thickness of switching layer in nanometers
        - Type of switching
        - Endurance
        - Retention time in seconds
        - Memory window in volts
        - Number of states
        - Conduction mechanism type
        - Resistive switching mechanism
        - Paper name
        - DOI
        - Publication year
        - Source (pdf file name)

        Instructions:
        1. Analyze the entire PDF document to locate all references to the above items.
        2. Extract each quantity with precision; include any units and relevant details.
        3. If multiple values are present for a single item, list them clearly (e.g., separated by commas).
        4. Format your output strictly as a table with two columns: one for the "Quantity" and one for the "Extracted Value".
        5. Do not include any extra text, headings, or commentary—only the table is required.
        6. If an item cannot be found, record it as "N/A" in the "Extracted Value" column.

        Please provide your final answer as the completed table.
        """
    )
    # print("\nAssistant:", result['response'])
    # print("\nContext:",result["context_docs"])
    # print("\nValidated_output:",result["validated_output"])
    print(result)