import os
import requests
from dotenv import load_dotenv
from utils.openRouter import OpenRouterChat
from langchain_openai import ChatOpenAI

load_dotenv()

"""
Utility functions for interacting with various LLMs.
"""


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_BASE = os.getenv(
    "OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
OPENROUTER_DEFAULT_MODEL = "google/gemini-2.5-flash"

openrouter_gemini25 = None
if OPENROUTER_API_KEY:
    try:
        openrouter_gemini25 = ChatOpenAI(
            model=OPENROUTER_DEFAULT_MODEL,
            temperature=0,
            openai_api_base=OPENROUTER_API_BASE,
            openai_api_key=OPENROUTER_API_KEY,
        )
    except Exception:
        openrouter_gemini25 = None



def getllmByName(name: str):
    """Returns an LLM instance based on the provided name."""
    llm_dict = {

        "openrouter_gemini25": openrouter_gemini25
    }
    return llm_dict.get(name)
