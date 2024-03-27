import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import mongo_crud, game, chatbot

# logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



app = FastAPI(
    title="RQMO - GALACTIC HEALER",
    description="API for GALACTIC HEALER",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# routers
app.include_router(mongo_crud.router, prefix="/mongo_crud", tags=["mongo_crud"])
app.include_router(game.router, prefix="/game", tags=["game"])
app.include_router(chatbot.router, prefix="/chatbot", tags=["chatbot"])

