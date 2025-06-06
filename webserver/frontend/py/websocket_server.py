import asyncio
import websockets
import socket
import struct

UDP_PORT = 50003
WS_PORT = 8080

clients = set()

async def udp_listener():
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(("", UDP_PORT))
    udp_sock.setblocking(False)

    loop = asyncio.get_event_loop()

    while True:
        try:
            data, _ = await loop.run_in_executor(None, udp_sock.recvfrom, 1024)
            floats = struct.unpack("f" * (len(data) // 4), data)
            msg = ",".join(map(str, floats))
            print("[UDP → WS] Forwarding:", msg[:60], "...")

            await asyncio.gather(*(ws.send(msg) for ws in clients))
        except Exception as e:
            print("[UDP error]", e)

async def ws_handler(websocket, _):
    print("[WebSocket] Connected")
    clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        clients.remove(websocket)
        print("[WebSocket] Disconnected")

async def main():
    print(f"Listening UDP:{UDP_PORT} → Forwarding to WS:{WS_PORT}")
    await asyncio.gather(
        websockets.serve(ws_handler, "0.0.0.0", WS_PORT),
        udp_listener()
    )

if __name__ == "__main__":
    asyncio.run(main())
