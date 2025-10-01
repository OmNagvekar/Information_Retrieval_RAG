import streamlit as st
import os
from datetime import datetime
from pathlib import Path
# from utils import profile_page_loader
import logging


if st.session_state.logged_in:
    logger = logging.getLogger(__name__)
    DEMO_DIR = Path("./PDF")
    UPLOAD_DIR = Path(f"./upload/{st.session_state.user_id}")

    # profile_page_loader(logger)
    st.title("Upload PDFs or Select a Dataset")
    with st.sidebar:
        st.markdown("# Upload PDFs")
        uploaded_files = st.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True)
        if uploaded_files:
            for file in uploaded_files:
                filename = file.name
                
    st.markdown("# Uploaded PDFs")
