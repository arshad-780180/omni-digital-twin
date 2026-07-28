import os
import asyncio
from urllib.parse import urlparse, unquote

def investigate():
    MONGODB_URL = os.environ.get("MONGODB_URL")
    if not MONGODB_URL:
        print("ERROR: MONGODB_URL environment variable is missing.")
        print("Please ensure you are running this in an environment where MONGODB_URL is set.")
        return

    try:
        parsed = urlparse(MONGODB_URL)
    except Exception as e:
        print(f"Failed to parse URL: {e}")
        return

    # 1. Print sanitized URL
    safe_url = f"{parsed.scheme}://{parsed.username}:********@{parsed.hostname}{parsed.path}"
    print(f"\n1. Sanitized MONGODB_URL: {safe_url}")

    # 2. Extract and decode username and password
    raw_username = parsed.username
    raw_password = parsed.password

    decoded_username = unquote(raw_username) if raw_username else None
    decoded_password = unquote(raw_password) if raw_password else None

    print(f"2. Username extracted: {decoded_username}")
    print("   -> Verify this exactly matches your Atlas DB User.")

    # 4. Check for URL encoding issues
    print(f"3. Password length: {len(decoded_password) if decoded_password else 0} characters.")
    print("   -> Verify this is the latest password you set in Atlas.")
    
    needs_encoding = False
    special_chars = "@:/?#[]@!$&'()*+,;="
    if decoded_password and any(c in special_chars for c in decoded_password):
        if raw_password == decoded_password:
            needs_encoding = True
            print("\n4. WARNING: Your password contains special characters but is NOT URL-encoded!")
            print("   This is highly likely the cause of the `bad auth` error.")
        else:
            print("\n4. URL Encoding: Your password contains special characters and IS URL-encoded. Good.")
    else:
        print("\n4. URL Encoding: Your password contains no special characters. No encoding needed.")

    # 5. Run ping
    print("\n5. Testing connection using AsyncIOMotorClient...")
    try:
        # Import the secure client we just built
        from database.connection import client
        async def ping():
            res = await client.admin.command("ping")
            print("   -> Ping SUCCESSFUL! Connection established.", res)
        asyncio.run(ping())
    except Exception as e:
        print(f"   -> Ping FAILED! Error: {e}")

if __name__ == "__main__":
    investigate()
