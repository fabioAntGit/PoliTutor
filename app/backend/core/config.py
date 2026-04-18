from rag.src.config import QUERY_MAX_LENGTH, SOCRATIC_REDIRECT
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI", "")
MONGO_DB = os.getenv("MONGODB_DB", "poli_tutor")