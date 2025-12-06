# server_render.py
# Servidor WebSocket para WAN en Render.com

import os
import asyncio
import websockets
import json

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 10000))

board = [[[0 for _ in range(4)] for _ in range(4)] for _ in range(4)]
clients = set()
player_slots = [None, None]
turn = 0

def board_copy():
    return [[[board[z][y][x] for x in range(4)] for y in range(4)] for z in range(4)]

async def broadcast(obj):
    msg = json.dumps(obj)
    for c in clients:
        try:
            await c.send(msg)
        except:
            pass

async def assign_player(ws):
    if player_slots[0] is None:
        player_slots[0] = ws
        return 0
    if player_slots[1] is None:
        player_slots[1] = ws
        return 1
    return None

async def handle_message(ws, data):
    global turn, board

    if data["type"] == "reset":
        board = [[[0]*4 for _ in range(4)] for _ in range(4)]
        turn = 0
        await broadcast({"type": "reset"})
        return

    if data["type"] == "move":
        p = data["player"]
        x, y, z = data["x"], data["y"], data["z"]

        if p != turn:
            return
        if board[z][y][x] != 0:
            return

        board[z][y][x] = -1 if p == 0 else 1
        await broadcast({"type": "move", "player": p, "x": x, "y": y, "z": z})

        turn = 1 - turn
        await broadcast({"type": "turn", "turn": turn})

async def handler(ws):
    global clients
    clients.add(ws)

    p = await assign_player(ws)
    await ws.send(json.dumps({"type": "assign", "player": p}))
    await ws.send(json.dumps({"type": "sync", "board": board_copy(), "turn": turn}))

    async for msg in ws:
        await handle_message(ws, json.loads(msg))

    clients.remove(ws)

async def main():
    print("Servidor WAN Render listo")
    print("Render asignará una URL WebSocket en /ws")
    await websockets.serve(handler, HOST, PORT, path="/ws")
    await asyncio.Future()

asyncio.run(main())
