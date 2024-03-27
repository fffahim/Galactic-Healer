import logging
import os
import shutil
import uuid

from fastapi import APIRouter, Form, HTTPException, UploadFile, File
from langchain.chains import RetrievalQA
from langchain.document_loaders import PyPDFLoader
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Milvus
from langchain.text_splitter import RecursiveCharacterTextSplitter

from ..settings.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
config = Config.get_instance()
upload_dir = "./uploads"
openai_llm_chat = config.get_openai_chat_connection()

# replace
ZILLIZ_CLOUD_URI = "https://in03-e5bab4e640f79fb.api.gcp-us-west1.zillizcloud.com"
ZILLIZ_CLOUD_API_KEY = os.environ['MILVUS_KEY']


def text_splitter(docs, chunk_size=1000, chunk_overlap=0):
    """
    Splits the documents into chunks
    :param docs:
    :param chunk_size:
    :param chunk_overlap:
    :return:
    """
    text_splitter_func = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    docs = text_splitter_func.split_documents(docs)
    return docs


def write_to_milvus(documents):
    try:
        docs = text_splitter(documents)
        embeddings = OpenAIEmbeddings()
        Milvus.from_documents(
            docs,
            embeddings,
            collection_name="rare_disease_data",
            connection_args={
                "uri": ZILLIZ_CLOUD_URI,
                "token": ZILLIZ_CLOUD_API_KEY,
                "secure": True,
            },
        )
        return True
    except Exception as e:
        logger.error(f"Error in uploading data to Milvus: {str(e)}")
        return False


def read_from_milvus(query):
    try:
        embeddings = OpenAIEmbeddings()
        vectorstore = Milvus(
            embeddings,
            collection_name="rare_disease_data",
            connection_args={
                "uri": ZILLIZ_CLOUD_URI,
                "token": ZILLIZ_CLOUD_API_KEY,
                "secure": True,
            },
        )
        qa = RetrievalQA.from_chain_type(llm=openai_llm_chat, chain_type="stuff", retriever=vectorstore.as_retriever())
        docs = qa({"query": query})
        print(docs["result"])
        return docs["result"]
    except Exception as e:
        logger.error(f"Error in reading data from Milvus: {str(e)}")
        return None


@router.post("/upload")
async def create_upload_file(file: UploadFile = File(...)):
    """
        Uploads a file to the server
        :param email_id:
        :param file:
        :return:
        """
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    file_location = os.path.join(upload_dir, (str(uuid.uuid4()) + file.filename))
    try:
        if file.filename.endswith('.txt'):
            with open(file_location, "wb") as file_object:
                shutil.copyfileobj(file.file, file_object)
            loader = TextLoader(file_location)
            documents = loader.load()

        elif file.filename.endswith('.pdf'):
            with open(file_location, "wb") as file_object:
                shutil.copyfileobj(file.file, file_object)
            loader = PyPDFLoader(file_location)
            documents = loader.load_and_split()
        else:
            return {"message": "File not supported"}

    except Exception as e:
        logger.error(f"Error in uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail="Error in uploading file")

    if write_to_milvus(documents):
        raise HTTPException(status_code=200, detail="Data uploaded to Milvus successfully")
    else:
        raise HTTPException(status_code=500, detail="Error in uploading data to Milvus")


@router.post("/chat")
async def chat(message: str = Form(...), history: list = Form(...)):
    """
    Chat with the AI
    :param message:
    :param history:
    :return:
    """
    try:
        if history is None:
            history = []

        if "STOP" in message or "Stop" in message or "stop" in message:
            return {"response": "STOPPING CHAT ", "history": history, "stop": True}

        inference = read_from_milvus(message)
        template = """
           CONTEXT: You are a Medic, and you are chatting with a patient/doctor/family member of patient suffering from rare disease who wants to know more 
           about their Query.  Politely answer them. Here is the history of 
           chat {history}, now the user is saying {message}. In case there is no history of chat, just respond to the 
           customer's current message. 
    
           DATA FROM DOCUMENTS OF RQMO: {inference} is the data relevant to message Query fetched from  Documents uploaded by the RQMO,  Your answers should be strictly based on it. 
           
           ANSWER: Keep Answers short and simple, preferable in bullets.
    
           RESPONSE CONSTRAINT: DO NOT OUTPUT HISTORY OF CHAT, JUST OUTPUT RESPONSE TO THE CUSTOMER IN BULLET POINTS.
           """
        prompt = PromptTemplate.from_template(template)
        chain = prompt | openai_llm_chat
        response = chain.invoke({"inference": inference, "message": message, "history": history})

        history.append({"message": message, "response": response})
        return {"response": response, "history": history, "stop": False}
    except Exception as e:
        logger.error(f"Error in chatting with AI: {str(e)}")
        raise HTTPException(status_code=500, detail="Error in chatting with AI")