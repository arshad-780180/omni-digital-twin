from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
import certifi
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.environ.get("MONGODB_URL")
if not MONGODB_URL:
    print("Error: MONGODB_URL environment variable is missing.")
    exit(1)

kwargs = {}
if "+srv" in MONGODB_URL or "tls=true" in MONGODB_URL.lower():
    kwargs["tlsCAFile"] = certifi.where()

client = AsyncIOMotorClient(MONGODB_URL, **kwargs)

async def main():
    try:
        print("Pinging MongoDB...")
        response = await client.admin.command("ping")
        print("Ping successful! Response:", response)
    except Exception as e:
        print("Ping failed! Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
