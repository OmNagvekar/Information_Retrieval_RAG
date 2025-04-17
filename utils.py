import bcrypt
from db import get_user,get_chat_titles_and_ids,delete_chat_id,delete_chat_session
import requests
from io import BytesIO
from PIL import Image
import streamlit as st
from uuid import uuid4

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Define the sample prompt (pre-populated default prompt)
def profile_page_loader(logger,on_chat_page=False):
    """
    This function is the entry point for the Streamlit app. It loads the user profile information from the database and displays it in the sidebar. It also handles the chat history and displays the chat titles in the sidebar. The main part of the page is dedicated to the chat interface, where the user can input a query and receive a response from the RAG Chat Assistant.

    If the user is not logged in, the function redirects them to the login page.

    :return: None
    """
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
                count =0
                for chat in chat_history:
                    with st.popover(f"### Title: {chat['title']}\n ID: {chat['chat_id']}"):
                        if st.button("Delete this Chat",key=str(uuid4())):
                            delete_chat_id(st.session_state.user_id,chat["chat_id"])
                            delete_chat_session(st.session_state.user_id,chat["chat_id"])
                            st.session_state.chat_id.remove(chat["chat_id"])
                            st.session_state.title.remove(chat["title"])
                            st.rerun()
                        if on_chat_page:
                            if st.button("Continue this Chat",key=str(uuid4())):
                                st.session_state.current_chat_id = chat["chat_id"]
                                st.rerun()
                    count+=1
            else:
                st.info("No chat titles available.")
            if st.button("Refresh Chat History"):
                st.rerun()
    else:
        st.info("Please log in to proceed.")
        st.switch_page("login.py")