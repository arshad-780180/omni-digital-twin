from motor.motor_asyncio import AsyncIOMotorClient
import os
import certifi
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
if not MONGODB_URL:
    raise ValueError("MONGODB_URL environment variable is required (e.g., MongoDB Atlas connection string)")
DATABASE_NAME = os.getenv("DATABASE_NAME", "omnimind_db")

kwargs = {}
if "+srv" in MONGODB_URL or "tls=true" in MONGODB_URL.lower():
    kwargs["tlsCAFile"] = certifi.where()

client = AsyncIOMotorClient(MONGODB_URL, **kwargs)
db = client[DATABASE_NAME]

async def get_db():
    return db
