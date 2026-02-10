import asyncio
import asyncpg
import sys

connection_url = 'postgresql://sentinel_user:sentinel_password@127.0.0.1:5432/sentinel_db'

async def test_conn():
    print(f"DEBUG: Attempting to connect to '{connection_url}'")
    try:
        conn = await asyncpg.connect(connection_url)
        print("SUCCESS: Connection established!")
        await conn.close()
    except Exception as e:
        print(f"FAILURE: Could not connect to DB.\nError: {e}")
        # Print extra context
        import socket
        try:
            print(f"DEBUG: Resolver test for 127.0.0.1: {socket.gethostbyname('127.0.0.1')}")
        except Exception as se:
            print(f"DEBUG: Resolver failed: {se}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_conn())
