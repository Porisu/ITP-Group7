import streamlit as st
from llm_chains import load_normal_chain, load_pdf_chat_chain
from langchain.memory import StreamlitChatMessageHistory
from utils import save_chat_history_json, get_timestamp, load_chat_history_json
import yaml
import os

#voice and audio handling
from streamlit_mic_recorder import mic_recorder
from audio_handler import transcribe_audio

#pdf files to db
from pdf_handler import add_documents_to_db
import pandas as pd

#config file
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

def load_chain(chat_history):
    return load_pdf_chat_chain(chat_history)    
    

#UI for chatbot
def clear_input_field():
    st.session_state.user_question = st.session_state.user_input
    st.session_state.user_input = ""

def set_send_input():
    st.session_state.send_input = True
    clear_input_field()

def toggle_pdf_chat():
    st.session_state.pdf_chat = True

#side bar to save history
def save_chat_history(user_path):
    if st.session_state.history != []:
        print(st.session_state.history)
        if st.session_state.session_key == "new_session":
            st.session_state.new_session_key = get_timestamp() + ".json"
            
            print("creating new chat session history")
            file_path = os.path.join(user_path, st.session_state.new_session_key)
            print(file_path)
            save_chat_history_json(st.session_state.history, file_path)
        else:
            print("writing in existing chat session history")
            file_path = os.path.join(user_path, st.session_state.session_key)
            print(file_path)
            save_chat_history_json(st.session_state.history,  file_path)

def track_index():
    st.session_state.session_index_tracker = st.session_state.session_key
    print("Current session: ", st.session_state.session_index_tracker)


#Authentication
def login_authenticate(username, password):
    # Simple username and password check
    if username == "user" and password == "password":
        st.session_state.logged_in = True
        st.session_state.username = username
    else:
        st.error("Invalid username or password")

def logout():
    st.session_state.logged_in = False
    st.session_state.username = None

def initialize_session_state():
    if "send_input" not in st.session_state:
        st.session_state.session_key = "new_session"
        st.session_state.send_input = False
        st.session_state.user_question = ""
        st.session_state.new_session_key = None 
        st.session_state.session_index_tracker = "new_session"

    if 'history' not in st.session_state:
        st.session_state.history = []

def get_button_label(chat_id):
    if chat_id == "new_session":
        return "New Session"
    else:
        return chat_id 

def main():
    st.title("AI Helper")
    chat_container = st.container()
    st.sidebar.title("Chat Sessions")

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

      # Sidebar content for login/logout
    if st.session_state.logged_in:
        st.sidebar.write(f"Welcome, {st.session_state.username}")
        if st.sidebar.button("Logout"):
            logout()
            st.experimental_rerun()
    else:
        with st.sidebar.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                login_authenticate(username, password)
                st.experimental_rerun()

    

    if st.session_state.logged_in:
        initialize_session_state()

        #create chat history list
        user_chat_path = os.path.join(config["chat_history_path"], st.session_state.username)
        if not os.path.exists(user_chat_path):
            os.makedirs(user_chat_path)

        chat_sessions = ["new_session"] + os.listdir(user_chat_path)
        print("List of chat sessions:")
        print(chat_sessions)
        #end of create chat history list

        #Change index tracker to newly created session
        if st.session_state.session_key == "new_session" and st.session_state.new_session_key != None:
            st.session_state.session_index_tracker = st.session_state.new_session_key
            st.session_state.new_session_key = None

        #create UI for User to select a session

        #buttons that display the sessions to user
        for chat_id in chat_sessions:
            button_label = get_button_label(chat_id)
            if st.sidebar.button(button_label):
            # Perform actions when the button is clicked
                st.session_state.session_key = chat_id

        index = chat_sessions.index(st.session_state.session_index_tracker)
        st.sidebar.selectbox("Select a chat session", chat_sessions, key="session_key", index=index, on_change=track_index)
        print("session key changed: " + st.session_state.session_key)


        # Potential improvement of chat history
        # 1.Allow user to save chat_session if user chooses
        # 2.Chat_session can be summarised by the LLM as a title instead of using date as the name for session

        #load selected session of chat history when user selects a session
        if st.session_state.session_key != "new_session":
            session_path = os.path.join(user_chat_path, st.session_state.session_key)
            st.session_state.history = load_chat_history_json(session_path)
            print(chat_sessions)
            print(st.session_state.history)
        else:
            st.session_state.history = []
            print(chat_sessions)
            print(st.session_state.history)


        chat_history = StreamlitChatMessageHistory(key="history")
        llm_chain = load_chain(chat_history)


        #textbox for user to input text
        #this creates a textbox that when you press enter will send prompt to AI,
        #however streamlit design make it so that clicking will work which is not that ideal
        user_input = st.text_input("Type your message here", key="user_input", on_change=set_send_input)

        voice_recording_column, send_button_column = st.columns(2)

        #voice prompt
        with voice_recording_column:
            voice_recording = mic_recorder(start_prompt="Start Recording", stop_prompt="Stop Recording", just_once=True)
        #text prompt
        with send_button_column:
            send_button = st.button("Send", key="send_button", on_click=clear_input_field)
        #Function to detect voice input
        if voice_recording:
            transcribed_audio = transcribe_audio(voice_recording["bytes"])
            print(transcribed_audio)
            llm_chain.run(transcribed_audio)
        #end of voice prompt

        #Function to detect text input
        if send_button or st.session_state.send_input:
            if st.session_state.user_question != "":
                    llm_chain.run(st.session_state.user_question)
                    st.session_state.user_question = ""

        #function to display AI responses to user    
        if chat_history.messages != []:
                st.write("Chat History:")
                for message in chat_history.messages:
                    st.chat_message(message.type).write(message.content)
        print(chat_history.messages)

        #this is used to track save session similar to previous history of user queries in chatGPT
        save_chat_history(user_chat_path)


#Initialize the Application
if __name__ == "__main__":
    main()
        