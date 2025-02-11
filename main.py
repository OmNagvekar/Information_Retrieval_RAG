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
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE,encoding="utf-8"),  # Save logs locally
        logging.StreamHandler(sys.stdout),  # Also print logs in console
    ],
)
def delete_old_logs():
    """Delete logs older than 1 day if they contain no errors."""
    while True:
        try:
            now = datetime.now()
            for filename in os.listdir(LOG_DIR):
                if filename.startswith("logs_") and filename.endswith(".log"):
                    file_path = os.path.join(LOG_DIR, filename)

                    # Extract date from filename
                    file_date_str = filename[5:15]  # Extract YYYY-MM-DD
                    file_date = datetime.strptime(file_date_str, "%Y-%m-%d")

                    # If log is older than 1 day
                    if now - file_date > timedelta(days=1):
                        with open(file_path, "r", encoding="utf-8") as log_file:
                            content = log_file.read()
                            if "ERROR" not in content:
                                os.remove(file_path)
                                logging.info(f"Deleted old log: {filename}")

        except Exception as e:
            logging.error(f"Error in log cleanup: {e}")

        time.sleep(3600)  # Run every hour

if __name__=="__main__":
    cleanup_thread = threading.Thread(target=delete_old_logs, daemon=True)
    cleanup_thread.start()
    obj = RAGChatAssistant(user_id="abc_123")
    result = obj.generate_response("""
        Extract the following data from the provided PDF and present it in a table: 
        (1) Input Data: switching layer material (TYM_Class), Synthesis method (SM_Class), Top electrode (TE_Class), Thickness of Top electrode (TTE in nm), Bottom electrode (BE_Class), Thickness of bottom electrode (TBE in nm), Thickness of switching layer (TSL in nm); (2) Output Data: Type of Switching (TSUB_Class), Endurance (Cycles) (EC), Retention Time (RT in seconds), Memory Window (MW in V), No. of states (MRS_Class), Conduction mechanism type (CM_Class), Resistive Switching mechanism (RSM_Class);
        (3) Reference Information: Name of the paper, DOI, Year. Ensure all data is extracted in the specified categories and format
    """
    )
    print("\nAssistant:", result['response'])
    print("\nContext:",result["context_docs"])
    print("\nValidated_output:",result["validated_output"])