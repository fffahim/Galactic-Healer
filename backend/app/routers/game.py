import json
import logging

from fastapi import APIRouter, Form, HTTPException
from langchain.prompts import PromptTemplate

from ..disease_datasets.constants import get_species, generate_random_star_wars_character
from ..routers.mongo_crud import save_chat_info
from ..settings.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
config = Config.get_instance()

openai_llm_chat = config.get_openai_chat_connection()
mongo_connection = config.get_mongo_client()
chat_collection = mongo_connection["galactic_medic"]["chat_info"]


def json_cleaner(data) -> str:
    """
    Cleans data to make json compatible, removing extra whitespaces and newlines and ' and " from the data
    :param data:
    :return:
    """
    try:
        data = str(data)
        data = data.replace("\n", " ")
        data = data.replace("\r", " ")
        data = data.replace("  ", " ")
        data = data.replace("\\", "")
        data = data.replace("/", "")
        data = data.replace("[", "{")
        data = data.replace("]", "}")

        return data
    except Exception as e:
        return None

def disease_json_cleaner(data) -> str:
    """
    Cleans data to make json compatible, removing extra whitespaces and newlines and ' and " from the data
    :param data:
    :return:
    """
    try:
        data = data.replace("\n", " ")
        data = data.replace("\r", " ")
        data = data.replace("  ", " ")
        data = data.replace("\\", "")
        data = data.replace("/", "")

        return data
    except Exception as e:
        return None

def get_disease_context():
    (full_name, species, age, traits) = generate_random_star_wars_character()
    disease_dict = get_species(species)
    disease_dict['species'] = species
    disease_dict['age'] = age
    disease_dict['traits'] = traits
    disease_dict['full_name'] = full_name
    return disease_dict


def get_options(bot_response: str, history: list, disease_context: str):
    """
    Generate options for the user to choose from
    :param bot_response:
    :param history:
    :param disease_context:
    :return:
    """

    template = '''CONTEXT : User is playing a Medic Quiz Game in Starwars world, you are given a history of chat {history} 
    and the current Response is {bot_response}.
    YOU PLAY AS MEDIC, ASKING QUESTION TO PATIENT TO DIAGNOSE DISEASE.
    TASK : provide 3 options, comprising of Question based on {disease_context}  (Including Intro, Diagnosis, mental well-being & best practices) to 
    user to choose from,  one of which takes them closer to the right diagnosis/response, and the other 2 are wrong.
     Dont directly give the option to predict disease / ask disease or directly jump to resolving 
    disease. We want to teach right questions for proper diagnosis, care, treatment and mental well being of the 
    patient.
    EXAMPLES: 
    1. So, how are you feeling today? 
    2. Lets see if we can find the reason of this rash, did you eat something new?
    3. I think surgery can be a good option, what do you think?
    OUTPUT_FORMAT is JSON EXAMPLE:
    ["option_1":value1, "option_2":value2, "option_3":value3, "Correct Option":correct_option_key]
    JUST OUTPUT THE OPTIONS as Questions , OR ANY OTHER DETAIL, NO EXTRA SPACES.
    '''
    prompt = PromptTemplate.from_template(template)
    chain = prompt | openai_llm_chat
    response = chain.invoke({"history": history, "bot_response": bot_response, "disease_context": disease_context})
    logger.info(f"Options generated successfully")
    response = json_cleaner(response)
    return response


def get_next_response(history: list, disease_context: str, option: str, correct_option: str):
    """
    Get the next response based on the option selected by the user
    :param history:
    :param disease_context:
    :param option:
    :param correct_option:
    :return:
    """

    if correct_option == "":
        correct_option = "Hi How are you doing"

    if option == "":
        option = correct_option

    template = '''CONTEXT: Welcome to an immersive open-world adventure set in the Star Wars universe, where you embody a character suffering from a rare illness seeking medical assistance. Refer to the provided information on the disease for details {disease_context}. Engage with the medic by responding to their inquiries to unravel your condition.
    
    HISTORY: Review the conversation history {history}. If there's no prior dialogue, introduce yourself and outline your symptoms.
    TASK: Your objective is to assist the user in diagnosing their ailment by guiding them through a series of questions. Avoid revealing the disease name or treatment directly. Encourage correct paths with affirmation and provide additional clues. If the user veers off course, gently redirect them towards the correct diagnostic approach with appropriate responses.
    The medic is asking you : {option} and the correct question should have been {correct_option}. In case of entierly wrong question, guide the doctor in right direction.
    EXAMPLES:
    
    BOT: "Hi Doctor, I've been feeling extremely fatigued and my joints ache constantly."
    BOT: "Your question does resonate with my symptoms. I've been experiencing severe joint pain and fatigue."
    BOT: "No Doctor, I'm afraid that's not quite on track. However, I have been dealing with intense muscle pain and exhaustion."
    Give Response in format, to bring user closer to right diagnosis in JSON FORMAT.
    ["bot_response":value]
    JUST OUTPUT THE Response, DO NOT ASK QUESTIONS TO MEDIC ABOUT THEIR HEALTH, TELL ABOUT YOURS NOT THE HISTORY, OR ANY OTHER DETAIL.
    '''
    prompt = PromptTemplate.from_template(template)
    chain = prompt | openai_llm_chat
    response = chain.invoke(
        {"disease_context": disease_context, "history": history, "option": option, "correct_option": correct_option})
    response = json_cleaner(response)
    return response


def keep_question_count(history: list):
    """
    Keep track of the number of questions asked
    :param history:
    :return:
    """
    return len(history)


@router.post("/game_chat")
def game_chat(email: str, message: str = Form(...), correct_option: str = Form(...), history: list = Form(...),
              question_count: int = Form(...), disease_context: str = Form(...)):
    """
    Chat with the AI
    :param correct_option:
    :param email:
    :param score:
    :param question_count:
    :param message:
    :param history:
    :param disease_context:
    :return:
    """
    if disease_context.strip() == "None":
        disease_context = get_disease_context()
        disease_context = disease_json_cleaner(json.dumps(disease_context))

    else:
        disease_context = json.loads(json.loads(disease_context))
        print(disease_context)
        print(type(disease_context))
        if disease_context["disease"]["name"] in message.lower():
            return {
                "bot_response": "You have successfully diagnosed the disease",
                "option_1": "",
                "option_2": "",
                "option_3": "",
                "Correct Option": "",
                "question_count": question_count,
                "history": history,
                "stop": True,
                "disease_context": disease_context
            }
        disease_context = json.dumps(disease_context)

    response_template = {
        "bot_response": "",
        "option_1": "",
        "option_2": "",
        "option_3": "",
        "Correct Option": "",
        "question_count": 0,
        "history": [],
        "stop": False,
        "disease_context": ""
    }

    try:
        if history is None or history == ['string'] or history == [''] or history == ['None']:
            history = []

        if "STOP" in message or "Stop" in message or "stop" in message:
            save_chat_info(email=email, chat_history={"history": history})
            return {
                "bot_response": "STOPPING CHAT ",
                "option_1": "",
                "option_2": "",
                "option_3": "",
                "Correct Option": "",
                "question_count": question_count,
                "history": history,
                "stop": True,
                "disease_context": disease_context
            }

        if len(history) == 0:
            question_count = 1
            bresponse = get_next_response(history=[], disease_context=disease_context, option="How are you?",
                                          correct_option="How are you?")
            bot_response = json.loads(bresponse)["bot_response"]
            option = get_options(bot_response, history, disease_context)
            history.append(
                {"user_question": "How are you?", "bot_response": bot_response})
            option = json.loads(option)
            response_template["bot_response"] = bot_response
            response_template["option_1"] = option["option_1"]
            response_template["option_2"] = option["option_2"]
            response_template["option_3"] = option["option_3"]
            response_template["Correct Option"] = option["Correct Option"]
            response_template["question_count"] = question_count
            response_template["disease_context"] = disease_context
            response_template["history"] = history

            return response_template



        else:
            print("REACHED HERE1")
            selected_option = message
            bot_response = get_next_response(history, disease_context, selected_option, correct_option)
            print("REACHED HERE2")
            print(bot_response)
            bot_response = json.loads(bot_response)["bot_response"]
            history.append(
                {"user_question": selected_option, "bot_response": bot_response})
            print("REACHED HERE3")
            print(history)
            option = get_options(bot_response, history, disease_context)
            option = json.loads(option)
            response_template["bot_response"] = bot_response
            response_template["option_1"] = option["option_1"]
            response_template["option_2"] = option["option_2"]
            response_template["option_3"] = option["option_3"]
            response_template["Correct Option"] = option["Correct Option"]
            response_template["question_count"] = question_count
            response_template["disease_context"] = disease_context
            response_template["history"] = history

            return response_template

    except Exception as e:
        logger.error(f"Error in chatting with AI: {str(e)}")
        raise HTTPException(status_code=500, detail="Error in chatting with AI")
