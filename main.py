"""
HJ SCAM BOT v8.5 - Pyrogram + Telethon
Telethon arranca automaticamente si existe sesion
Handlers se registran DESPUES de conectar
"""
import re
import requests
import asyncio
import os
import subprocess
import sys
from os import path

# ─── Imports ───────────────────────────────────────────────────────────────────
try:
    from pyrogram import Client, filters
    from pyrogram.types import MessageEntity
    from pyrogram.enums import MessageEntityType
    print("[OK] Pyrogram importado")
except ImportError:
    print("[FATAL] pip install pyrogram tgcrypto")
    sys.exit(1)

try:
    from telethon import TelegramClient, events
    HAS_TELETHON = True
    print("[OK] Telethon importado")
except ImportError:
    HAS_TELETHON = False
    print("[WARN] Telethon no disponible")

try:
    from colorama import Fore, init
    init(autoreset=True)
except ImportError:
    class Fore:
        RED = GREEN = YELLOW = RESET = ""

# ─── Config ────────────────────────────────────────────────────────────────────
API_ID     = 29009837
API_HASH   = "1d388952a2f1f03de04a4b94f64eb6ed"
BOT_TOKEN  = "8594813440:AAFFKfWwup01Si1C-exXIN2InTABuKgRv7g"
CHAN_ID    = -1003127906650
OWNER_ID   = 5947916142

SCRIPT_DIR = path.dirname(path.abspath(__file__))
IMG_PATH   = path.join(SCRIPT_DIR, "nueva_img.jpg")
IMG_FALL   = path.join(SCRIPT_DIR, "hj.jpg")
IMG_URL    = "https://i.ibb.co/9zznM39/IMG-20260607-101547-310.jpg"
TARJ_FILE  = path.join(SCRIPT_DIR, "tarjetas.txt")

# Buscar sesion Telethon en multiples ubicaciones
TEL_SESSION_PATHS = [
    path.join(SCRIPT_DIR, "anon"),
    path.join(SCRIPT_DIR, "sessions", "anon"),
]

# ─── Custom Emoji IDs ─────────────────────────────────────────────────────────
CHAT_EMOJI  = 5427181942934088912   # 💬 premium
CARD_EMOJI  = 5927169041595634481   # 💳 premium
ARROW_EMOJI = 5197375087786874047   # ⏩ premium
GLOBE_EMOJI = 5879585266426973039   # 🌐 premium
HOUSE_EMOJI = 5967822972931542886   # 🏠 premium
NOTE_EMOJI  = 5877597667231534929   # 🗒 premium

U_CHAT  = "\U0001f4ac"
U_CARD  = "\U0001f4b3"
U_ARROW = "\u23e9\ufe0f"
U_GLOBE = "\U0001f310"
U_HOUSE = "\U0001f3e0"
U_NOTE  = "\U0001f5d2"
U_CROWN = "\U0001f451"
U_GEAR  = "\u2699\ufe0f"

# ─── Imagen ────────────────────────────────────────────────────────────────────
def ensure_image():
    for p in [IMG_PATH, IMG_FALL]:
        if path.isfile(p) and path.getsize(p) > 500:
            return p
    try:
        r = requests.get(IMG_URL, timeout=20)
        if r.status_code == 200 and len(r.content) > 500:
            with open(IMG_PATH, "wb") as f:
                f.write(r.content)
            return IMG_PATH
    except Exception as e:
        print(f"[ERR] Imagen: {e}")
    return None

# ─── UTF-16 helpers ────────────────────────────────────────────────────────────
def u16len(s):
    return len(s.encode("utf-16-le")) // 2

# ─── Message Builder ──────────────────────────────────────────────────────────
class MB:
    def __init__(self):
        self.t = ""
        self.e = []

    def a(self, text, bold=False, italic=False, code=False, hashtag=False, emoji=None):
        off = u16len(self.t)
        self.t += text
        ln = u16len(text)
        if ln == 0:
            return self
        if emoji:
            self.e.append(MessageEntity(type=MessageEntityType.CUSTOM_EMOJI, offset=off, length=ln, custom_emoji_id=emoji))
        if bold:
            self.e.append(MessageEntity(type=MessageEntityType.BOLD, offset=off, length=ln))
        if italic:
            self.e.append(MessageEntity(type=MessageEntityType.ITALIC, offset=off, length=ln))
        if code:
            self.e.append(MessageEntity(type=MessageEntityType.CODE, offset=off, length=ln))
        if hashtag:
            self.e.append(MessageEntity(type=MessageEntityType.HASHTAG, offset=off, length=ln))
        return self

    def n(self):
        self.t += "\n"
        return self

    def sep(self, n=11):
        for _ in range(n):
            self.a(U_CHAT, emoji=CHAT_EMOJI)
        return self.n()

    def build(self):
        return self.t, self.e


def build_hit(bin_n, cc, mm, yy, cvv, extra, brand, level, tipo, bank, country, flag):
    b = MB()
    b.a("HJ SCAM", bold=True, italic=True).a(" ").a(f"#BIN{bin_n}", hashtag=True).n()
    b.sep()
    b.a(U_CARD, emoji=CARD_EMOJI).a(" ").a("Cc", bold=True).a(" ").a(U_ARROW, emoji=ARROW_EMOJI).a(" ").a(f"{cc}|{mm}|{yy}|{cvv}", code=True).n()
    b.a(U_CHAT, emoji=CHAT_EMOJI).a(" ").a("Response", bold=True).a(" ").a(U_ARROW, emoji=ARROW_EMOJI).a(" Approved! \u2705").n()
    b.a(U_GEAR).a(" ").a("Extra", bold=True).a(" ").a(U_ARROW, emoji=ARROW_EMOJI).a(" ").a(f"{extra}xxxx|{mm}|{yy}|rnd", code=True).n()
    b.sep()
    b.a(U_NOTE, emoji=NOTE_EMOJI).a(" ").a("Info", bold=True).a(" ").a(U_ARROW, emoji=ARROW_EMOJI).a(f" {brand} - {level} - {tipo}").n()
    b.a(U_HOUSE, emoji=HOUSE_EMOJI).a(" ").a("Bank", bold=True).a(" ").a(U_ARROW, emoji=ARROW_EMOJI).a(f" {bank}").n()
    b.a(U_GLOBE, emoji=GLOBE_EMOJI).a(" ").a("Country", bold=True).a(" ").a(U_ARROW, emoji=ARROW_EMOJI).a(f" {country} {flag}").n()
    b.sep(10)
    b.a(U_CROWN).a("Owner", bold=True).a("  @hjofc20")
    return b.build()


def build_emoji_test():
    b = MB()
    b.a("EMOJI TEST", bold=True, italic=True).n().n()
    b.a("Chat: ", bold=True).a(U_CHAT, emoji=CHAT_EMOJI).n()
    b.a("Card: ", bold=True).a(U_CARD, emoji=CARD_EMOJI).n()
    b.a("Arrow: ", bold=True).a(U_ARROW, emoji=ARROW_EMOJI).n()
    b.a("Note: ", bold=True).a(U_NOTE, emoji=NOTE_EMOJI).n()
    b.a("House: ", bold=True).a(U_HOUSE, emoji=HOUSE_EMOJI).n()
    b.a("Globe: ", bold=True).a(U_GLOBE, emoji=GLOBE_EMOJI).n()
    b.a("Crown: ", bold=True).a(U_CROWN).n()
    b.a("Gear: ", bold=True).a(U_GEAR).n().n()
    b.a("Separador:", bold=True).n()
    b.sep()
    return b.build()

# ─── Verificar duplicado ──────────────────────────────────────────────────────
def verificar(ccn):
    try:
        with open(TARJ_FILE, "r") as f:
            return ccn in f.read()
    except FileNotFoundError:
        return False

# ─── Pyrogram Bot ─────────────────────────────────────────────────────────────
bot = Client("premium_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Estado global
tel_client = None
tel_ok = False


# ─── Telethon Hit Handler ─────────────────────────────────────────────────────
async def _hit_handler(event):
    """Se ejecuta cuando Telethon detecta un hit en un canal"""
    text = event.raw_text
    responses = [
        'Approved', 'Non VBV', 'Gateway Rejected: avs',
        'Succeeded!', 'APPROVED', 'Approved CCN',
        'Approved #AUTH!', 'Appr0ved',
        'Security code incorrect', 'CVV2 FAILURE POSSIBLE CVV',
        'Subscription complete', 'CVV LIVE',
        'Card Approved CCN/CCV Live', 'incorrect_cvc',
        'Approved!', 'VIVA'
    ]
    if not any(r in text for r in responses):
        return

    x = re.findall(r'\d+', text)
    if len(x) < 4:
        return

    cc, mm, yy, cvv = x[0], x[1], x[2], x[3]
    if len(cc) > 16 or len(cc) < 15:
        return
    if len(mm) > 2:
        return
    if len(yy) > 4:
        return
    if len(cvv) > 4:
        return

    if mm.startswith('2'):
        mm, yy = yy, mm
    if len(mm) >= 3:
        mm, yy, cvv = yy, cvv, mm
    if len(yy) == 2:
        yy = '20' + yy

    if verificar(cc):
        return

    with open(TARJ_FILE, 'a') as d:
        d.write(f"{cc}|{mm}|{yy}|{cvv}\n")

    bin_n = cc[:6]
    try:
        rs = requests.get(f"https://bins.antipublic.cc/bins/{bin_n}").json()
        country = rs.get("country", "??")
        flag = rs.get("country_flag", "\U0001F3F3")
        bank = rs.get("bank", "Unknown")
        brand = rs.get("brand", "Unknown")
        tipo = rs.get("type", "Unknown")
        level = rs.get("level", "Unknown")
    except:
        country, flag, bank, brand, tipo, level = "??", "\U0001F3F3", "Unknown", "Unknown", "Unknown", "Unknown"

    txt, ent = build_hit(bin_n, cc, mm, yy, cvv, cc[:12], brand, level, tipo, bank, country, flag)
    print(f"[HIT] {cc}|{mm}|{yy}|{cvv} {country}")

    try:
        img = ensure_image()
        if img and path.isfile(img):
            await bot.send_photo(CHAN_ID, img)
        await bot.send_message(CHAN_ID, txt, entities=ent)
        print("[OK] Enviado con premium al canal")
    except Exception as e:
        print(f"[ERR] Pyrogram send: {e}")
        try:
            await bot.send_message(CHAN_ID, txt)
            print("[WARN] Enviado sin premium")
        except Exception as e2:
            print(f"[ERR] Fallback: {e2}")


# ─── Iniciar Telethon ─────────────────────────────────────────────────────────
def _find_telethon_session():
    """Buscar sesion de Telethon en todas las ubicaciones posibles"""
    for sess in TEL_SESSION_PATHS:
        if path.isfile(sess + ".session"):
            sz = path.getsize(sess + ".session")
            if sz > 100:
                print(f"[OK] Sesion Telethon encontrada: {sess}.session ({sz} bytes)")
                return sess
            else:
                print(f"[WARN] Sesion vacia: {sess}.session ({sz} bytes)")
    # Buscar cualquier .session en el dir
    for f in os.listdir(SCRIPT_DIR):
        if f.endswith(".session") and f != "premium_bot.session":
            sz = path.getsize(path.join(SCRIPT_DIR, f))
            if sz > 100:
                sess = path.join(SCRIPT_DIR, f[:-8])  # quitar .session
                print(f"[OK] Sesion alternativa: {f} ({sz} bytes)")
                return sess
    return None


async def _start_telethon():
    """Iniciar Telethon y registrar handlers"""
    global tel_client, tel_ok

    if not HAS_TELETHON:
        print("[WARN] Telethon no instalado")
        return

    session_path = _find_telethon_session()
    if not session_path:
        print("[WARN] No hay sesion de Telethon. Hits desactivados.")
        print("[TIP] Para activar: ejecuta manualmente una vez para crear sesion:")
        print(f"[TIP]   cd {SCRIPT_DIR} && python3 -c \"from telethon.sync import TelegramClient; TelegramClient('anon',{API_ID},'{API_HASH}').start()\"")
        return

    try:
        tel_client = TelegramClient(session_path, API_ID, API_HASH)
        await tel_client.start()
        tel_ok = True

        # Registrar handlers DESPUES de conectar
        tel_client.add_event_handler(_hit_handler, events.NewMessage())
        tel_client.add_event_handler(_hit_handler, events.MessageEdited())

        print("[OK] Telethon conectado + handlers registrados - escuchando hits")
    except Exception as e:
        print(f"[WARN] Telethon fallo: {e}")
        tel_client = None


# ─── Comandos Pyrogram ────────────────────────────────────────────────────────

@bot.on_message(filters.command("start") & filters.private)
async def cmd_start(c, m):
    await m.reply("Bot activo! v8.5\nComandos: /status /emojis /testimg /update /restart")

@bot.on_message(filters.command("status") & filters.private)
async def cmd_status(c, m):
    if m.from_user.id != OWNER_ID:
        return
    try:
        r = subprocess.run(["git", "log", "--oneline", "-1"], capture_output=True, text=True, cwd=SCRIPT_DIR)
        commit = r.stdout.strip() or "?"
    except:
        commit = "?"
    img = "OK" if path.isfile(IMG_PATH) and path.getsize(IMG_PATH) > 500 else "Fallback"
    tel = "Conectado" if tel_ok else "Desconectado"
    await m.reply(f"Bot v8.5\nCommit: {commit}\nImagen: {img}\nTelethon: {tel}\nDir: {SCRIPT_DIR}")

@bot.on_message(filters.command("emojis") & filters.private)
async def cmd_emojis(c, m):
    if m.from_user.id != OWNER_ID:
        return
    txt, ent = build_emoji_test()
    try:
        await c.send_message(m.chat.id, txt, entities=ent)
    except Exception as e:
        await m.reply(f"Error: {e}")

@bot.on_message(filters.command("testimg") & filters.private)
async def cmd_testimg(c, m):
    if m.from_user.id != OWNER_ID:
        return
    await m.reply("Enviando prueba al canal...")
    txt, ent = build_hit("411111", "4111111111111111", "12", "2026", "123",
                         "411111111111", "VISA", "CLASSIC", "CREDIT", "TEST BANK", "US", "\U0001F1FA\U0001F1F8")
    try:
        img = ensure_image()
        if img and path.isfile(img):
            await c.send_photo(CHAN_ID, img)
        await c.send_message(CHAN_ID, txt, entities=ent)
        await m.reply("Enviado al canal!")
    except Exception as e:
        await m.reply(f"Error: {e}")

@bot.on_message(filters.command("update") & filters.private)
async def cmd_update(c, m):
    if m.from_user.id != OWNER_ID:
        return
    await m.reply("Actualizando...")
    try:
        r = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True, cwd=SCRIPT_DIR, timeout=30)
        out = r.stdout + r.stderr
        if "Already up" in out:
            await m.reply("Ya actualizado.")
            return
        if r.returncode != 0:
            await m.reply(f"Error:\n{out[:500]}")
            return
        req = path.join(SCRIPT_DIR, "requirements.txt")
        if path.isfile(req):
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", req], capture_output=True, text=True, timeout=120)
        ensure_image()
        await m.reply(f"OK! Reiniciando...\n{out[:300]}")
        subprocess.Popen(["sudo", "systemctl", "restart", "bot-tg"])
    except Exception as e:
        await m.reply(f"Error: {e}")

@bot.on_message(filters.command("restart") & filters.private)
async def cmd_restart(c, m):
    if m.from_user.id != OWNER_ID:
        return
    await m.reply("Reiniciando...")
    subprocess.Popen(["sudo", "systemctl", "restart", "bot-tg"])

@bot.on_message(filters.command("telethon") & filters.private)
async def cmd_telethon(c, m):
    """Forzar inicio de Telethon"""
    if m.from_user.id != OWNER_ID:
        return
    global tel_ok
    if tel_ok:
        await m.reply("Telethon ya esta conectado.")
        return
    await m.reply("Iniciando Telethon...")
    await _start_telethon()
    if tel_ok:
        await m.reply("Telethon conectado! Escuchando hits.")
    else:
        await m.reply("Telethon fallo. Revisa los logs.")


# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    img = ensure_image()
    if img:
        print(f"[OK] Imagen lista")
    print("=" * 40)
    print("HJ SCAM BOT v8.5")
    print("Pyrogram + Emojis Premium")
    print("Comandos: /start /status /emojis")
    print("  /testimg /update /restart /telethon")
    print("=" * 40)

    # Iniciar Telethon automaticamente si hay sesion
    # Se hace como tarea de fondo despues de que bot.run() arranque Pyrogram
    async def _auto_start():
        await asyncio.sleep(3)  # Esperar a que Pyrogram estabilice
        print("[..] Auto-iniciando Telethon...")
        await _start_telethon()

    # Registrar la tarea de auto-start como callback de Pyrogram
    @bot.on_disconnect()
    async def on_disconnect(c):
        print("[WARN] Pyrogram desconectado")

    # Usar on_startup para iniciar Telethon cuando Pyrogram este listo
    # Pyrogram 2.0 no tiene on_startup, usamos el primer comando
    # Pero intentamos iniciar Telethon como tarea de fondo
    original_start = bot.start

    async def patched_start():
        result = await original_start()
        print("[OK] Pyrogram bot conectado")
        # Iniciar Telethon como tarea de fondo
        asyncio.ensure_future(_auto_start())
        return result

    bot.start = patched_start

    print("[..] Iniciando bot.run()...")
    bot.run()
