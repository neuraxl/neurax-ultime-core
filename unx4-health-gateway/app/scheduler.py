import asyncio
import os
import time
from .main import sync

INTERVAL=int(os.getenv("UNX4_SYNC_INTERVAL_SECONDS","21600"))

async def run():
    while True:
        try:
            await sync()
        except Exception as exc:
            print(f"UNX4 scheduled sync error: {exc}", flush=True)
        await asyncio.sleep(INTERVAL)

if __name__ == "__main__":
    asyncio.run(run())
