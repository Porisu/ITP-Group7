import streamlit as st
from llm_chains import load_normal_chain, load_pdf_chat_chain
from langchain.memory import StreamlitChatMessageHistory
from utils import save_chat_history_json, get_timestamp, load_chat_history_json
import yaml
import os

# Voice and audio handling
from streamlit_mic_recorder import mic_recorder
from audio_handler import transcribe_audio

# PDF files to db
from pdf_handler import add_documents_to_db

# Load config file once
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

def load_chain(chat_history):
    return load_pdf_chat_chain(chat_history) if st.session_state.pdf_chat else load_normal_chain(chat_history)

def save_chat_history():
    if st.session_state.history:
        session_key = st.session_state.session_key
        chat_history_path = config["chat_history_path"]
        file_name = get_timestamp() + ".json" if session_key == "new_session" else session_key
        save_chat_history_json(st.session_state.history, os.path.join(chat_history_path, file_name))


def main():
    st.title("AI Helper")
    chat_container = st.container()
    chat_sessions = ["new_session"] + os.listdir(config["chat_history_path"])
    st.session_state.setdefault("send_input", False)
    st.session_state.setdefault("pdf_chat", False)
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("session_key", "new_session")
    st.session_state.setdefault("new_session_key", "")
    st.session_state.setdefault("session_index_tracker", "new_session")
    st.session_state.setdefault("uploaded_files", set())

    chat_history = StreamlitChatMessageHistory(key="chat_history")
    if st.session_state.history:
        chat_history.chat_memory.messages = st.session_state.history

    llm_chain = load_chain(chat_history)

    uploaded_pdf = st.file_uploader("Upload a PDF file", accept_multiple_files=True, key="pdf_upload", type=["pdf"])
    if uploaded_pdf:
        for pdf in uploaded_pdf:
            if pdf.name in st.session_state.uploaded_files:
                st.warning(f"File '{pdf.name}' has already been uploaded.")
                print("PDF exist")
            else:
                st.session_state.uploaded_files.add(pdf.name)
                with st.spinner("Processing PDF"):
                    add_documents_to_db([pdf])  # Assuming this is the correct function to handle PDF uploads
                st.success(f"PDF '{pdf.name}' has been uploaded and processed.")
                print("PDF Uploaded")

    if st.session_state.send_input and st.session_state.user_question:
        llm_response = llm_chain.run(st.session_state.user_question)
        st.session_state.user_question = ""
        st.session_state.send_input = False


if __name__ == "__main__":
    main()
