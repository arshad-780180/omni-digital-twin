from motor.motor_asyncio import AsyncIOMotorClient
import os
import certifi
import logging
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

MONGODB_URL = os.getenv("MONGODB_URL")
if not MONGODB_URL:
    raise ValueError("MONGODB_URL environment variable is required (e.g., MongoDB Atlas connection string)")

try:
    parsed_uri = urlparse(MONGODB_URL)
    
    if parsed_uri.scheme not in ("mongodb", "mongodb+srv"):
        raise ValueError("URI must start with 'mongodb://' or 'mongodb+srv://'")
        
    if parsed_uri.scheme == "mongodb+srv" and parsed_uri.port is not None:
        raise ValueError("mongodb+srv:// URIs must not include a port number")
        
    _ = parsed_uri.port  # Try accessing port to trigger parsing errors if malformed
    
    host_info = parsed_uri.hostname or "unknown-host"
    if parsed_uri.port:
        host_info = f"{host_info}:{parsed_uri.port}"
        
    # Log safely without credentials
    logger.info(f"Initializing MongoDB connection to: {parsed_uri.scheme}://{host_info}{parsed_uri.path}")
    
except ValueError as e:
    raise ValueError(
        f"Malformed MONGODB_URL provided. "
        f"Expected format: 'mongodb+srv://<username>:<password>@<cluster-url>/<dbname>?options'. "
        f"Error details: {str(e)}"
    )

DATABASE_NAME = os.getenv("DATABASE_NAME", "omnimind_db")

kwargs = {}
if "+srv" in MONGODB_URL or "tls=true" in MONGODB_URL.lower():
    kwargs["tlsCAFile"] = certifi.where()

client = AsyncIOMotorClient(MONGODB_URL, **kwargs)
db = client[DATABASE_NAME]

async def get_db():
    return db
