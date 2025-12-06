# server_lan.py
# Servidor WebSocket para TicTacToe 3D (SOLO LAN)

import asyncio
import websockets
import json

PORT = 8765
HOST = "0.0.0.0"   # Permite que otras PCs en tu LAN se conecten

# Representación del tablero 4×4×4
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

def check_victory(x, y, z):
    v = board[z][y][x]

    dirs = [
        [(1,0,0),(-1,0,0)],[(0,1,0),(0,-1,0)],[(0,0,1),(0,0,-1)],
        [(1,1,0),(-1,-1,0)],[(1,-1,0),(-1,1,0)],
        [(1,0,1),(-1,0,-1)],[(1,0,-1),(-1,0,1)],
        [(0,1,1),(0,-1,-1)],[(0,1,-1),(0,-1,1)],
        [(1,1,1),(-1,-1,-1)],[(1,1,-1),(-1,-1,1)],
        [(1,-1,1),(-1,1,-1)],[(1,-1,-1),(-1,1,1)],
    ]

    for direction in dirs:
        count = 1
        for dx, dy, dz in direction:
            cx, cy, cz = x, y, z
            for _ in range(3):
                cx += dx; cy += dy; cz += dz
                if 0 <= cx < 4 and 0 <= cy < 4 and 0 <= cz < 4:
                    if board[cz][cy][cx] == v:
                        count += 1
                        if count == 4:
                            return True
                    else:
                        break
                else:
                    break
    return False

async def assign_player(ws):
    global player_slots
    if player_slots[0] is None:
        player_slots[0] = ws
        return 0
    elif player_slots[1] is None:
        player_slots[1] = ws
        return 1
    return None

async def handle_message(ws, data):
    global turn, board

    t = data.get("type")

    if t == "reset":
        board = [[[0 for _ in range(4)] for _ in range(4)] for _ in range(4)]
        turn = 0
        await broadcast({"type": "reset"})
        await broadcast({"type": "turn", "turn": turn})
        return

    if t == "move":
        player = data.get("player")
        x = data.get("x"); y = data.get("y"); z = data.get("z")

        if player != turn:
            await ws.send(json.dumps({"type": "error","msg":"No es tu turno"}))
            return

        if board[z][y][x] != 0:
            await ws.send(json.dumps({"type": "error","msg":"Casilla ocupada"}))
            return

        value = -1 if player == 0 else 1
        board[z][y][x] = value

        victory = check_victory(x, y, z)

        await broadcast({
            "type":"move","player":player,
            "x":x,"y":y,"z":z,
            "victory":victory
        })

        if victory:
            return

        turn = 1 - turn
        await broadcast({"type":"turn","turn":turn})

async def handler(ws):
    global clients
    clients.add(ws)

    p = await assign_player(ws)

    await ws.send(json.dumps({"type": "assign", "player": p}))
    await ws.send(json.dumps({
        "type": "sync",
        "board": board_copy(),
        "turn": turn
    }))

    async for msg in ws:
        try:
            data = json.loads(msg)
        except:
            continue
        await handle_message(ws, data)

    clients.remove(ws)
    if p == 0: player_slots[0] = None
    if p == 1: player_slots[1] = None


async def main():
    print("=====================================")
    print(" SERVIDOR TIC TAC TOE 3D (LAN)")
    print(f" Conéctate con: ws://TU_IP_LOCAL:{PORT}")
    print("=====================================")

    async with websockets.serve(handler, HOST, PORT):
        await asyncio.Future()

asyncio.run(main())
