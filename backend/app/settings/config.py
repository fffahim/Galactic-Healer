import logging
import os
from langchain.llms import OpenAIChat
import pymongo
import certifi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    _instance = None

    @staticmethod
    def get_instance():
        """Return the singleton instance of Config"""
        if Config._instance is None:
            Config._instance = Config()
        return Config._instance

    def __init__(self):
        if Config._instance is not None:
            raise Exception(
                "Config is a singleton class, use get_instance() to get the instance."
            )

        try:
            self.open_ai_key= os.environ["OPENAI_API_KEY"]
            self.mongo_uri = os.environ["MONGO_URI"]
            self.sql_uri = os.environ["SQL_URI"]
            self.sql_pass= os.environ["SQL_PASS"]
            self.milvus_host="https://in03-e5bab4e640f79fb.api.gcp-us-west1.zillizcloud.com"

        except KeyError as e:
            logger.error(f"Missing environment variable: {e}")
            raise e



    def get_mongo_client(self):
        try:
            logger.info("Connecting to MongoDB")
            client = pymongo.MongoClient(os.environ['MONGO_URI'], ssl=True, tlsCAFile=certifi.where())
            client.admin.command('ping')
            logger.info(f"Connected to MongoDB")
            return client
        except Exception as e:
            logger.error(f"Error in connecting to MongoDB: {str(e)}")
            raise e

    # def get_sql_connection(self):
    #     try:
    #         logger.info("Connecting to SQL")
    #         conn = psycopg2.connect(
    #             database="user_info",
    #             host="aws-0-us-west-1.pooler.supabase.com",
    #             user="postgres.skrdgxogwdlxdbphncup",
    #             password=self.sql_pass,
    #             port="5432"
    #             )
    #         logger.info(f"Connected to SQL")
    #         return conn
    #     except Exception as e:
    #         logger.error(f"Error in connecting to SQL: {str(e)}")
    #         raise e

    def get_openai_chat_connection(self):
        try:
            logger.info("Connecting to GPT-3.5")
            chat_llm = OpenAIChat(max_tokens=4000, temperature=0.2, model='gpt-3.5-turbo-0125')
            return chat_llm
        except Exception as e:
            logger.error(f"Error in connecting to GPT-3.5: {str(e)}")
            raise e



