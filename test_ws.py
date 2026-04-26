import asyncio
import websockets

async def test():
    try:
        async with websockets.connect('ws://127.0.0.1:5000/api/ws-voice') as ws:
            await ws.send("DONE")
            print(await ws.recv())
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
