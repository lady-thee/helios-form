from pymongo import AsyncMongoClient
from beanie import init_beanie
from app.models import Forms, FormVersion, Submission
from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")

async def init_db():
    client = AsyncMongoClient(MONGODB_URL)
    app_documents = [Forms, FormVersion, Submission]
    await init_beanie(database=client[DATABASE_NAME], document_models=app_documents)