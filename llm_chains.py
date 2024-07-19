from prompt_templates import memory_prompt_template
from langchain.chains import StuffDocumentsChain, LLMChain, ConversationalRetrievalChain, RetrievalQA
from langchain_community.embeddings import HuggingFaceInstructEmbeddings
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain_community.llms import CTransformers
from langchain_community.vectorstores import Chroma
import chromadb
import yaml
import threading
import json

#load the config file
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Singleton pattern to ensure model and embeddings are loaded only once
class ModelSingleton:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ModelSingleton, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance

    def _initialize(self):
        self.llm = CTransformers(model=config["model_path"]["small"], model_type=config["model_path"]["small"], config=config['model_config'])
        self.embeddings = HuggingFaceInstructEmbeddings(model_name=config["embeddings_path"])


def create_llm(model_path = config["model_path"]["large"], model_type=config["model_path"]["large"], model_config = config['model_config']):
    return ModelSingleton().llm


def create_embeddings():
    return ModelSingleton().embeddings

def create_chat_memory(chat_history):
    return ConversationBufferWindowMemory(memory_key="history", chat_memory=chat_history, k=3)

def create_prompt_from_template(template):
    return PromptTemplate.from_template(template)

def create_llm_chain(llm, chat_prompt, memory):
    return LLMChain(llm=llm, prompt=chat_prompt, memory=memory)

def load_normal_chain(chat_history):
    return chatChain(chat_history)

def load_vectordb(embeddings):
    persistent_client = chromadb.PersistentClient("chroma_db")
    langchain_chroma = Chroma(
        client = persistent_client,
        collection_name = "pdfs",
        embedding_function = embeddings,
    )
    return langchain_chroma

def load_retrieval_chain(llm, memory, vector_db):
    #return RetrievalQA.from_llm(llm=llm, memory=memory, retriever=vector_db.as_retriever())
    return RetrievalQA.from_llm(llm=llm, memory=memory, retriever=vector_db.as_retriever(search_type = "similarity", search_kwargs ={"k":1}))


#Reads the prompt template
def read_prompt_template():
    file_path = config['prompt_template']
    #"chroma_db\prompt_template.json"
    with open(file_path, 'r') as file:
        prompt_template_data = json.load(file)
    return prompt_template_data

#Initialize the AI
def load_pdf_chat_chain(chat_history):
    return pdfChatChain(chat_history)

class pdfChatChain:
    def __init__(self, chat_history):
        self.memory = create_chat_memory(chat_history)
        embeddings = create_embeddings()
        self.vector_db=load_vectordb(embeddings)
        llm = create_llm()

        self.prompt_responses = read_prompt_template()
        self.chat_prompt = create_prompt_from_template(grn_prompt_template)
        self.llm_chain = load_retrieval_chain(llm, self.memory, self.vector_db)

    def run(self, user_input):
        print("AI chat chain is running...")

        if user_input in self.prompt_responses:

            # If user's queries is found, the response is predefined
            response = self.prompt_responses[user_input]
            prompt = self.chat_prompt.format(
                history=self.memory.chat_memory.messages,
                human_input=user_input,
                response=response
            )
            self.memory.chat_memory.add_user_message(user_input)
            self.memory.chat_memory.add_ai_message(response)
            return 
        
        else:
            # If user query not found in prompt template, use the retrieval chain
            return self.llm_chain.run(query=user_input, history=self.memory.chat_memory.messages, stop="Human:")



class chatChain:

    def __init__(self, chat_history):
        self.memory = create_chat_memory(chat_history)
        llm = create_llm() #defined in the config file
        chat_prompt = create_prompt_from_template(memory_prompt_template)
        self.llm_chain = create_llm_chain(llm, chat_prompt, self.memory)

    def run(self, user_input):
        #can use different method to call via langchain, but this can be used to stop to prevent halluciations
        #drawback: need to give it a chathistory
        return self.llm_chain.run(human_input = user_input, history=self.memory.chat_memory.messages, stop="Human:")
    

    