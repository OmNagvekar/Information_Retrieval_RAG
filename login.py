import streamlit as st
import json
import logging
from PIL import Image
import requests
from io import BytesIO
from db import get_user, create_user, users_collection, get_chat_titles_and_ids,update_chat_ids
# from utils import hash_password

# Configure logging
logger = logging.getLogger(__name__)
logger.info("Starting Chat App Login...")


st.title("Information Retrieval RAG App Login")

# initialize session_state
if "flow" not in st.session_state:
    st.session_state.flow = "Login"

# let user switch (and honor programmatic changes)
mode = st.radio(
    "Choose an action",
    ["Login", "Sign Up"],
    index=0 if st.session_state.flow == "Login" else 1,
)

# --- LOGIN TAB ---
if mode == "Login":
    st.header("Login")
    # For the Login tab, we first require OAuth authentication.
    if not st.experimental_user.is_logged_in:
        st.info("Please log in using your OAuth provider.")
        if st.button("Login with Google"):
            logger.info("Initiating OAuth login from Login tab...")
            st.login()  # Uses the [auth] configuration in secrets.toml.
            st.rerun()
        st.stop()
    # OAuth is complete – retrieve claims.
    oidc_user_id = st.experimental_user.get("sub")
    oauth_email = st.experimental_user.get("email")
    oauth_picture = st.experimental_user.get("picture")
    st.session_state["oidc_user_id"] = oidc_user_id
    logger.info("Login OAuth completed. oidc_user_id: %s, email: %s", oidc_user_id, oauth_email)
    
    # Display user details and chat titles.
    user_record = get_user(oidc_user_id)
    chat_history = get_chat_titles_and_ids(oidc_user_id)
    if not user_record:
        st.warning("No profile found. Please switch to the Sign Up tab to register.")
        logger.warning("Login attempted but no profile exists for oidc_user_id: %s", oidc_user_id)
        if st.button("Go to Registration"):
            # Switch to the Sign Up tab by updating session state and rerunning.
            st.session_state["flow"] = "Sign Up"
            st.rerun()
    else:
        st.success(f"Welcome back, {user_record.get('username', 'User')}!")
    
    # Sidebar for profile details appears as usual.
    with st.sidebar:
        st.markdown("## Profile")
        if user_record:
            profile_username = user_record.get("username", oauth_email)
            profile_email = user_record.get("email", oauth_email)
            logger.info("Loaded user record from DB for oidc_user_id: %s", oidc_user_id)
        else:
            profile_username = oauth_email
            profile_email = oauth_email
            logger.info("No user record found in DB for oidc_user_id: %s", oidc_user_id)
    
        if oauth_picture:
            response = requests.get(oauth_picture)
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                st.image(image, width=100,caption="Profile Picture")
            else:
                st.image(oauth_picture, width=100,caption="Profile Picture")
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
    
    st.subheader("Login - Welcome Back!")
    st.write("Your chat IDs:")
    if chat_history:
        for chat in chat_history:
            st.write(f"### ID: {chat['chat_id']}")
            st.session_state.chat_id.append(chat["chat_id"])
        update_chat_ids(oidc_user_id, st.session_state.chat_id)
        logger.info("Updated chat IDs for user %s: %s", oidc_user_id, st.session_state.chat_id)
    else:
        st.info("You have no chat IDs yet.")
    
    if st.button("Proceed to Chat History"):
        st.success("Navigating to Chat History...")  # Placeholder for future navigation.
        st.session_state.logged_in = True
        st.session_state.user_id = oidc_user_id
        st.switch_page("main.py")
        logger.info("User %s proceeding to Chat History.", oidc_user_id)


# --- SIGN UP TAB ---
else:
    st.header("Sign Up")
    # In the Sign Up tab, we need to start with OAuth as well.
    if not st.experimental_user.is_logged_in:
        st.info("To register, please sign up using your OAuth provider first.")
        if st.button("Sign Up with Google"):
            logger.info("Initiating OAuth login from Sign Up tab...")
            st.login()  # Starts OAuth login.
            st.rerun()
        st.stop()
    
    # OAuth is complete for Sign Up tab.
    oidc_user_id = st.experimental_user.get("sub")
    oauth_email = st.experimental_user.get("email")
    oauth_picture = st.experimental_user.get("picture")
    st.session_state["oidc_user_id"] = oidc_user_id
    logger.info("Sign Up OAuth completed. oidc_user_id: %s, email: %s", oidc_user_id, oauth_email)
    
    # Display registration form.
    st.subheader("Complete Your Profile")
    email = st.text_input("Email", value=oauth_email)
    username = st.text_input("Username (default is your email)", value=oauth_email)
    full_name = st.text_input("Full Name")
    profession = st.selectbox("Profession", ["Engineer", "Scientist", "Artist", "Other"])
    if profession == "Other":
        profession = st.text_input("Please specify your profession","Other")
    
    if st.button("Register"):
        logger.info("Register button pressed in Sign Up tab with email: %s, username: %s", email, username)
        if not email or not full_name:
            st.error("Email and Full Name are required for registration.")
            logger.warning("Registration failed: missing email or full name.")
            st.stop()
        # Check if the user has manually changed the username; if so, verify uniqueness.
        if username != oauth_email:
            existing = users_collection.find_one({"username": username})
            if existing:
                st.error("Username already taken. Please try a different username.")
                logger.warning("Registration failed: username %s already taken.", username)
                st.stop()
        final_username = username if username else oauth_email
    
        if get_user(oidc_user_id):
            st.error("Profile already exists. Please log in.")
            logger.warning("Registration attempted but profile exists for oidc_user_id: %s", oidc_user_id)
        else:
            try:
                create_user(oidc_user_id=oidc_user_id, username=final_username, full_name=full_name,email=email, profession=profession, picture=oauth_picture,chat_ids=[])
                st.success("Registration successful! Your profile has been created.")
                st.session_state.flow = "Login"
                logger.info("User registered successfully: oidc_user_id: %s", oidc_user_id)
                st.rerun()  # Reload the app to reflect the new profile.
            except Exception as e:
                st.error(f"Error creating profile: {e}")
                logger.error("Error creating profile for oidc_user_id %s: %s", oidc_user_id, e)