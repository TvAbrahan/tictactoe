# game.py
# Cliente WebSocket + UI Tkinter para TicTacToe 3D (LAN/WAN)
# Comentarios actualizados, código intacto

import threading
import asyncio
import websockets
import json
from tkinter import *
from tkinter import messagebox, simpledialog

# -------------- CONFIGURACIÓN GENERAL ----------------
# Puerto donde el servidor WebSocket estará escuchando (solo relevante para LAN/ws)
PORT = 8765
# ------------------------------------------------------------

# ---------------- Variables del juego ----------------
jugadas = [[[0,0,0,0] for _ in range(4)] for __ in range(4)]
botones = []
X = Y = Z = jugador = g = 0
reset_in_progress = False

my_player = None
turno_actual = None
client_ws = None
texto = None

# --------- Utilidades ----------
def display_player_num(p):
    if p is None: return "-"
    return p + 1

def ficha_de(p):
    if p is None: return "-"
    return "X" if p == 0 else "O"

# --------- Interfaz Tkinter ----------
tablero = Tk()
tablero.title('Tic Tac Toe 3D - LAN')
try: tablero.iconbitmap('cubo.ico')
except Exception: pass

tablero.geometry("1040x720+100+5")
tablero.resizable(0, 0)

def crearBoton(valor,i):
    return Button(tablero,text=valor,width=5,height=1,font=("Helvetica",15),command=lambda i=i: boton_local_click(i))

def seguir_o_finalizar():
    resp = messagebox.askyesno("FINALIZAR", "¿Quieres continuar?")
    if resp:
        if g: inicio()
    else:
        tablero.destroy()

def boton_local_click(i):
    global X, Y, Z, my_player, turno_actual
    Z = int(i/16)
    y = int(i%16)
    Y = int(y/4)
    X = int(y%4)

    Label(tablero, text='X='+str(X), font='arial, 14', fg='green').place(x=20,y=150)
    Label(tablero, text='Y='+str(Y), font='arial, 14', fg='green').place(x=20,y=180)
    Label(tablero, text='Z='+str(Z), font='arial, 14', fg='green').place(x=20,y=210)

    if g:
        seguir_o_finalizar()
        return

    if my_player is None:
        messagebox.showinfo("Esperando", "Aún no estás asignado por el servidor.")
        return

    if turno_actual is None:
        messagebox.showinfo("Esperando", "Aún no hay turno asignado.")
        return

    if turno_actual != my_player:
        messagebox.showwarning("No es tu turno", "Espera tu turno.")
        return

    if jugadas[Z][Y][X] != 0:
        messagebox.showwarning("Ocupado", "Casilla ocupada")
        return

    if client_ws:
        client_ws.send_move(X, Y, Z, my_player)
    else:
        messagebox.showerror("No conectado", "No hay conexión al servidor.")

def botonClick(i):
    boton_local_click(i)

def ganador():
    global g
    if texto is not None:
        texto.config(text='Jugador '+str(display_player_num(jugador)) + ' GANO')
    else:
        lblg = Label(tablero, text='Jugador '+str(display_player_num(jugador)) + ' GANO', font='arial, 20', fg='blue')
        lblg.place(x=20, y=5)
    g=1

# -------- Funciones de líneas de victoria --------
def horizontal(): s=0; [s:=s+jugadas[Z][Y][x] for x in range(4)]; return not (s<4 and s>-4)
def vertical(): s=0; [s:=s+jugadas[Z][y][X] for y in range(4)]; return not (s<4 and s>-4)
def profundidad(): s=0; [s:=s+jugadas[z][Y][X] for z in range(4)]; return not (s<4 and s>-4)
def diagonal_frontal1(): s=0; [s:=s+jugadas[Z][x][x] for x in range(4)]; return not (s<4 and s>-4)
def diagonal_frontal2(): s=0; [s:=s+jugadas[Z][y][3-y] for y in range(4)]; return not (s<4 and s>-4)
def diagonal_horizontal1(): s=0; [s:=s+jugadas[z][Y][z] for z in range(4)]; return not (s<4 and s>-4)
def diagonal_horizontal2(): s=0; [s:=s+jugadas[3-z][Y][z] for z in range(4)]; return not (s<4 and s>-4)
def diagonal_vertical1(): s=0; [s:=s+jugadas[z][z][X] for z in range(4)]; return not (s<4 and s>-4)
def diagonal_vertical2(): s=0; [s:=s+jugadas[3-z][z][X] for z in range(4)]; return not (s<4 and s>-4)
def diagonal_cruzada1(): s=0; [s:=s+jugadas[3-x][x][x] for x in range(4)]; return not (s<4 and s>-4)
def diagonal_cruzada2(): s=0; [s:=s+jugadas[x][3-x][x] for x in range(4)]; return not (s<4 and s>-4)
def diagonal_cruzada3(): s=0; [s:=s+jugadas[3-y][3-y][y] for y in range(4)]; return not (s<4 and s>-4)
def diagonal_cruzada4(): s=0; [s:=s+jugadas[z][z][z] for z in range(4)]; return not (s<4 and s>-4)

def inicio():
    global jugadas, X, Y, Z, jugador, g, botones, texto, reset_in_progress
    reset_in_progress = False
    for z in range(4):
        for y in range(4):
            for x in range(4):
                jugadas[z][y][x]=0
                botones[z*16+y*4+x].config(text='', font='arial 15',fg='blue',bg='white')
    X = Y = Z = jugador = g = 0
    if texto is None:
        texto_local = Label(tablero, text='Jugador 1', font='arial, 20', fg='green', width=18, anchor='w')
        texto_local.place(x=500, y=620)
        globals()['texto'] = texto_local
    else:
        texto.config(text='Jugador 1')

# ---------- Creación de tablero ----------
for b in range(64):
    botones.append(crearBoton(' ',b))

contador=0
for z in range(3,-1,-1):
    for y in range(4):
        for x in range(4):
            botones[contador].grid(row=y+z*4,column=x+(3-z)*4)
            contador+=1

# Labels informativos
lbl = Label(tablero, text="Conectando...", font=("Helvetica", 12), fg="green", width=36, anchor="w")
lbl.place(x=10, y=10)
lbl_turno = Label(tablero, text="Turno: -", font=("Helvetica", 12), fg="blue", width=36, anchor="w")
lbl_turno.place(x=10, y=40)

inicio()

# ----------------- WEBSOCKET CLIENT -----------------
class WSClient:
    def __init__(self, server_ip, server_port, on_assign, on_turn, on_move, on_error, on_sync=None):
        self.server_ip = server_ip
        self.server_port = server_port
        self.on_assign = on_assign
        self.on_turn = on_turn
        self.on_move = on_move
        self.on_error = on_error
        self.on_sync = on_sync
        self.loop = None
        self.ws = None
        self._thread = threading.Thread(target=self._start, daemon=True)
        self._thread.start()

    def _start(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._connect())

    async def _connect(self):
        if self.server_port is None or self.server_ip.startswith("ws://") or self.server_ip.startswith("wss://"):
            uri = self.server_ip
        else:
            uri = f"ws://{self.server_ip}:{self.server_port}"

        try:
            async with websockets.connect(uri) as websocket:
                self.ws = websocket
                tablero.after(0, lambda: lbl.config(text=f"Conectado a: {uri}"))
                
                async for mensaje in websocket:
                    try: data = json.loads(mensaje)
                    except: continue
                    t = data.get("type")
                    if t == "assign": self.on_assign(data.get("player"))
                    elif t == "turn": self.on_turn(int(data.get("turn")))
                    elif t == "move": self.on_move(data["x"],data["y"],data["z"],data["player"],data.get("victory", False))
                    elif t == "sync" and self.on_sync: self.on_sync(data)
                    elif t == "reset": tablero.after(0, inicio)
                    elif t == "error": self.on_error(data.get("msg"))
        except Exception as e:
            tablero.after(0, lambda: lbl.config(text=f"Desconectado. Error: {e}"))

    def send_move(self, x, y, z, player, victory=False):
        if self.loop is None: return
        coro = self._send({"type":"move","player":player,"x":x,"y":y,"z":z,"victory":bool(victory)})
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    def send_reset(self):
        if self.loop is None: return
        coro = self._send({"type":"reset"})
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    async def _send(self, obj):
        if self.ws:
            try: await self.ws.send(json.dumps(obj))
            except Exception as e: print("Send failed:", e)

# --------- Callbacks UI ----------
def on_move_recv(x,y,z,player,victory):
    def _do():
        aplicar_jugada_recibida(x,y,z,player)
        if victory:
            messagebox.showinfo("Resultado", f"Jugador {display_player_num(player)} GANÓ")
    tablero.after(0, _do)

def on_assign_recv(player):
    global my_player
    my_player = player
    def _label():
        if player is None:
            lbl.config(text="Eres espectador")
        else:
            lbl.config(text=f"Eres el Jugador {display_player_num(player)} - Usas '{ficha_de(player)}'")
    tablero.after(0, _label)

def on_turn_recv(turn):
    global turno_actual
    turno_actual = int(turn)
    def _t():
        lbl_turno.config(text=f"Turno del Jugador {display_player_num(turno_actual)} ({ficha_de(turno_actual)})")
        if texto: texto.config(text="Jugador " + str(display_player_num(turno_actual)))
    tablero.after(0, _t)

def on_error_recv(msg):
    def _t(): messagebox.showerror("Error servidor", msg)
    tablero.after(0, _t)

def on_sync_recv(data):
    board = data.get("board")
    turn = data.get("turn")
    def _s():
        global jugadas, turno_actual
        try:
            for z in range(4):
                for y in range(4):
                    for x in range(4):
                        val = board[z][y][x]
                        jugadas[z][y][x] = val
                        i = z*16 + y*4 + x
                        if val == 0:
                            botones[i].config(text='', fg='blue', bg='white')
                        elif val == -1:
                            botones[i].config(text='X', fg='blue', bg='white')
                        else:
                            botones[i].config(text='O', fg='red', bg='white')
        except: pass

        try:
            turno_actual = int(turn)
            lbl_turno.config(text=f"Turno del Jugador {display_player_num(turno_actual)} ({ficha_de(turno_actual)})")
            if texto: texto.config(text="Jugador " + str(display_player_num(turno_actual)))
        except: pass
        
    tablero.after(0, _s)

def aplicar_jugada_recibida(x, y, z, player):
    global X, Y, Z, jugador, reset_in_progress
    valor = -1 if player == 0 else 1
    if jugadas[z][y][x] != 0: return
    jugadas[z][y][x] = valor

    i = z*16 + y*4 + x
    texto_char = "X" if valor == -1 else "O"
    color = "blue" if valor == -1 else "red"
    botones[i].config(text=texto_char, font='arial 15', fg=color)

    X, Y, Z = x, y, z
    jugador = player

    def resaltar_y_reset(indices):
        global reset_in_progress
        for idx in indices:
            botones[idx].config(fg='yellow', bg='red')
        if client_ws and not reset_in_progress:
            reset_in_progress = True
            tablero.after(5000, lambda: client_ws.send_reset())

    if horizontal(): resaltar_y_reset([Z*16+Y*4+xx for xx in range(4)]); ganador(); return
    if vertical(): resaltar_y_reset([Z*16+yy*4+X for yy in range(4)]); ganador(); return
    if profundidad(): resaltar_y_reset([zz*16+Y*4+X for zz in range(4)]); ganador(); return
    if X==Y and diagonal_frontal1(): resaltar_y_reset([Z*16+xx*4+xx for xx in range(4)]); ganador(); return
    if X+Y==3 and diagonal_frontal2(): resaltar_y_reset([Z*16+(3-xx)*4+xx for xx in range(4)]); ganador(); return
    if X==Z and diagonal_horizontal1(): resaltar_y_reset([zz*16+Y*4+zz for zz in range(4)]); ganador(); return
    if X+Z==3 and diagonal_horizontal2(): resaltar_y_reset([(3-zz)*16+Y*4+zz for zz in range(4)]); ganador(); return
    if Y==Z and diagonal_vertical1(): resaltar_y_reset([zz*16+zz*4+X for zz in range(4)]); ganador(); return
    if Y+Z==3 and diagonal_vertical2(): resaltar_y_reset([(3-zz)*16+zz*4+X for zz in range(4)]); ganador(); return
    if Y==X and diagonal_cruzada1(): resaltar_y_reset([xx*16+(3-xx)*4+(3-xx) for xx in range(4)]); ganador(); return
    if Z==X and diagonal_cruzada2(): resaltar_y_reset([xx*16+(3-xx)*4+xx for xx in range(4)]); ganador(); return
    if Z==Y and diagonal_cruzada3(): resaltar_y_reset([xx*16+xx*4+(3-xx) for xx in range(4)]); ganador(); return
    if Z==Y and Y==X and diagonal_cruzada4(): resaltar_y_reset([xx*16+xx*4+xx for xx in range(4)]); ganador(); return

# ------------- CONEXIÓN LAN / WAN ----------------

def conectar_lan():
    global client_ws
    server_ip = simpledialog.askstring(
        "Conectar por LAN",
        f"Ingresa la IP local del servidor (192.168.x.x). Puerto: {PORT}"
    )

    if not server_ip:
        lbl.config(text="No conectado")
        return

    if client_ws:
        client_ws = None

    lbl.config(text=f"Conectando a {server_ip}:{PORT} ... (LAN - ws)")

    client_ws = WSClient(
        server_ip,
        PORT,
        on_assign_recv,
        on_turn_recv,
        on_move_recv,
        on_error_recv,
        on_sync_recv
    )

def conectar_wan_render():
    global client_ws

    # !!! REEMPLAZA ESTE DOMINIO CON TU APP DE RENDER !!!
    RENDER_URL = "tu-app.onrender.com"

    full_url = f"wss://{RENDER_URL}/ws"

    if client_ws:
        client_ws = None

    lbl.config(text=f"Conectando a {full_url} ... (WAN - wss)")

    client_ws = WSClient(
        full_url,
        None,
        on_assign_recv,
        on_turn_recv,
        on_move_recv,
        on_error_recv,
        on_sync_recv
    )

def seleccionar_modo_conexion():
    modo = simpledialog.askstring(
        "Modo de conexión",
        "Seleccione:\nA = Servidor Render (WAN)\nB = LAN local"
    )

    if not modo:
        lbl.config(text="No conectado. Elige un modo.")
        return

    modo = modo.strip().upper()

    if modo == "A":
        conectar_wan_render()
    elif modo == "B":
        conectar_lan()
    else:
        messagebox.showerror("Error", "Opción inválida. Escriba A o B.")

def iniciar_conexion():
    seleccionar_modo_conexion()

# ----------- BOTONES (YA ORDENADOS) --------------
btn_lan = Button(tablero, text="Conectar LAN", width=12, height=1, font=("Helvetica", 12), command=conectar_lan)
btn_lan.place(x=850, y=20)

btn_wan = Button(tablero, text="Conectar WAN (Render)", width=18, height=1, font=("Helvetica", 12), command=conectar_wan_render)
btn_wan.place(x=820, y=60)

tablero.after(100, iniciar_conexion)
tablero.mainloop()
