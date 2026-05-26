import os
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone
from fastapi import FastAPI # Your existing FastAPI import will be around here

# 1. Load the .env file securely from disk
load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")
pinecone_key = os.getenv("PINECONE_API_KEY")

if not openai_key or not pinecone_key:
    raise ValueError("CRITICAL: Production API keys are missing from the local .env file!")

# 2. Initialize your production AI microservices
ai_client = OpenAI(api_key=openai_key)
pc_client = Pinecone(api_key=pinecone_key)

# ... The rest of your existing FastAPI app code, routes, and logic continue below ...
