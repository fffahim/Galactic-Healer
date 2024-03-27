import logging

from fastapi import APIRouter, HTTPException, status

from app.Models.userInfo import UserInfo
from ..settings.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
config = Config.get_instance()
mongo_connection = config.get_mongo_client()
user_collection = mongo_connection["galactic_medic"]["user_info"]
chat_collection = mongo_connection["galactic_medic"]["chat_info"]


def save_user_info(user_info: UserInfo):
    try:
        if user_info.email in user_collection.distinct('email'):
            user_collection.update_one({'email': user_info.email}, {'$set': dict(user_info)})
        user_collection.insert_one(dict(user_info))
        logger.info(f"User info saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error in saving user info: {str(e)}")
        return False


def get_user_by_email(email: str):
    try:
        user = user_collection.find_one({'email': email}, {'_id': 0})
        if not user:
            logger.error(f"User not found")
            return None
        logger.info(f"User info fetched successfully")
        return user
    except Exception as e:
        logger.error(f"Error in fetching user info: {str(e)}")
        return None


def save_chat_info(chat_history: dict, email: str):
    try:
        chat_collection.insert_one({'email': email, 'chat_history': chat_history})
        logger.info(f"Chat info saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error in saving chat info: {str(e)}")
        return False


def get_chat_info_by_email(email: str):
    try:
        chat = chat_collection.find({'email': email}, {'_id': 0})
        if not chat:
            logger.error(f"Chat info not found")
            return None
        logger.info(f"Chat info fetched successfully")
        return chat
    except Exception as e:
        logger.error(f"Error in fetching chat info: {str(e)}")
        return None


@router.post("/save_user_info")
async def save_user_info_route(user_info : UserInfo):
    """
    Save user info
    :param user_info:
    :return:
    """
    if save_user_info(user_info):
        raise HTTPException(status_code=status.HTTP_200_OK, detail="User info saved successfully")
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error in saving user info")


@router.get("/get_user_info/{email}")
async def get_user_info(email: str):
    """
    Get user info
    :param email:
    :return
    """
    user = get_user_by_email(email)
    if user:
        return user
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
