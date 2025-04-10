import asyncio
import websockets

async def test():
    uri = "ws://localhost:6000/ws-test"
    try:
        async with websockets.connect(uri) as websocket:
            print("연결 성공")
            await websocket.send("안녕하세요")
            response = await websocket.recv()
            print(f"받은 응답: {response}")
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(test())
