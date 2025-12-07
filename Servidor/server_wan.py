# server_wan.py
# Servidor WebSocket para WAN en Render.com

import os
import asyncio
import websockets
import json

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 10000))

board = [[[0 for _ in range(4)] for _ in range(4)] for _ in range(4)]
clients = set()
player_slots = [None, None]  # slots de jugador 0 y 1
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

# Asignar jugador a slot libre o espectador
async def assign_player(ws):
    for i in range(2):
        if player_slots[i] is None:
            player_slots[i] = ws
            return i
    return None  # espectador

# Manejar desconexión y liberar slot
async def player_disconnect(ws):
    global board, turn
    changed = False
    for i in range(2):
        if player_slots[i] == ws:
            player_slots[i] = None
            changed = True

    if changed:
        # Verificar si queda un jugador conectado
        remaining_player = None
        for i in range(2):
            if player_slots[i] is not None:
                remaining_player = i

        if remaining_player is not None:
            # Solo un jugador se fue, el otro gana automáticamente
            await broadcast({
                "type": "move",
                "player": remaining_player,
                "x": -1,  # Indicamos que es victoria por desconexión
                "y": -1,
                "z": -1,
                "victory": True
            })

        # Si ambos slots están libres, resetear tablero
        if player_slots[0] is None and player_slots[1] is None:
            board = [[[0 for _ in range(4)] for _ in range(4)] for _ in range(4)]
            turn = 0
            await broadcast({"type": "reset"})


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

        # Cambiar turno solo si hay jugadores en ambos slots
        if player_slots[0] is not None and player_slots[1] is not None:
            turn = 1 - turn
            await broadcast({"type": "turn", "turn": turn})

async def handler(ws):
    global clients
    clients.add(ws)

    p = await assign_player(ws)
    await ws.send(json.dumps({"type": "assign", "player": p}))
    await ws.send(json.dumps({"type": "sync", "board": board_copy(), "turn": turn}))

    try:
        async for msg in ws:
            await handle_message(ws, json.loads(msg))
    except:
        pass
    finally:
        clients.remove(ws)
        await player_disconnect(ws)

async def main():
    print("Servidor WAN Render listo")
    print("Render asignará una URL WebSocket")
    await websockets.serve(handler, HOST, PORT)
    await asyncio.Future()

asyncio.run(main())
