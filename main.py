"""
HJ SCAM BOT v8.8 - Pyrogram + Telethon + Raw API
Fix: usar HTTP API directa de Telegram para enviar custom_emoji al canal.
Pyrogram funciona para privado pero no para canales con custom emoji.
La API cruda de Telegram (/sendMessage con entities JSON) SI funciona en canales.
"""
import re
import requests as http_requests
import json
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
    print("[OK] Telethon importado")
except ImportError:
    print("[WARN] Telethon no disponible")
    TelegramClient = None

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
TG_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

SCRIPT_DIR = path.dirname(path.abspath(__file__))
IMG_PATH   = path.join(SCRIPT_DIR, "nueva_img.jpg")
IMG_FALL   = path.join(SCRIPT_DIR, "hj.jpg")
IMG_URL    = "https://i.ibb.co/9zznM39/IMG-20260607-101547-310.jpg"
TARJ_FILE  = path.join(SCRIPT_DIR, "tarjetas.txt")
TEL_SESSION = path.join(SCRIPT_DIR, "anon")

# ─── Custom Emoji IDs ─────────────────────────────────────────────────────────
CHAT_EMOJI  = 5427181942934088912   # 💬 premium
CARD_EMOJI  = 5927169041595634481   # 💳 premium
ARROW_EMOJI = 5197375087786874047   # ⏩ premium
GLOBE_EMOJI = 5879585266426973039   # 🌐 premium
HOUSE_EMOJI = 5967822972931542886   # 🏠 premium
NOTE_EMOJI  = 5877597667231534929   # 🗒 premium

# Unicode chars
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
        r = http_requests.get(IMG_URL, timeout=20)
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
            self.e.append({
                "type": "custom_emoji",
                "offset": off,
                "length": ln,
                "custom_emoji_id": str(emoji)
            })
        if bold:
            self.e.append({"type": "bold", "offset": off, "length": ln})
        if italic:
            self.e.append({"type": "italic", "offset": off, "length": ln})
        if code:
            self.e.append({"type": "code", "offset": off, "length": ln})
        if hashtag:
            self.e.append({"type": "hashtag", "offset": off, "length": ln})
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


# ─── Raw Telegram API Send ────────────────────────────────────────────────────
def _convert_entities_for_pyrogram(entities):
    """Convert raw dict entities to Pyrogram MessageEntity objects for private chat"""
    result = []
    for e in entities:
        if e["type"] == "custom_emoji":
            result.append(MessageEntity(
                type=MessageEntityType.CUSTOM_EMOJI,
                offset=e["offset"],
                length=e["length"],
                custom_emoji_id=int(e["custom_emoji_id"])
            ))
        elif e["type"] == "bold":
            result.append(MessageEntity(type=MessageEntityType.BOLD, offset=e["offset"], length=e["length"]))
        elif e["type"] == "italic":
            result.append(MessageEntity(type=MessageEntityType.ITALIC, offset=e["offset"], length=e["length"]))
        elif e["type"] == "code":
            result.append(MessageEntity(type=MessageEntityType.CODE, offset=e["offset"], length=e["length"]))
        elif e["type"] == "hashtag":
            result.append(MessageEntity(type=MessageEntityType.HASHTAG, offset=e["offset"], length=e["length"]))
    return result


def api_send_message(chat_id, text, entities):
    """Enviar mensaje con custom_emoji usando HTTP API directa de Telegram"""
    url = f"{TG_API_URL}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "entities": json.dumps(entities),
        "parse_mode": ""
    }
    try:
        r = http_requests.post(url, data=data, timeout=10)
        result = r.json()
        if result.get("ok"):
            print(f"[OK] API directa: mensaje enviado ok")
            return True
        else:
            print(f"[ERR] API directa: {result.get('description', 'unknown error')}")
            return False
    except Exception as e:
        print(f"[ERR] API directa exception: {e}")
        return False


def api_send_photo(chat_id, photo_path, caption, caption_entities):
    """Enviar foto con caption+custom_emoji usando HTTP API directa"""
    url = f"{TG_API_URL}/sendPhoto"
    try:
        with open(photo_path, "rb") as f:
            data = {
                "chat_id": chat_id,
                "caption": caption,
                "caption_entities": json.dumps(caption_entities),
                "parse_mode": ""
            }
            files = {"photo": f}
            r = http_requests.post(url, data=data, files=files, timeout=15)
            result = r.json()
            if result.get("ok"):
                print(f"[OK] API directa: foto+caption enviado ok")
                return True
            else:
                print(f"[ERR] API directa foto: {result.get('description', 'unknown error')}")
                return False
    except Exception as e:
        print(f"[ERR] API directa foto exception: {e}")
        return False


async def send_hit_to_channel(txt, ent, img_path=None):
    """
    Enviar hit al canal con emojis premium usando API directa de Telegram.
    Primero intenta foto+caption, luego texto solo.
    """
    # Intentar foto + caption con premium
    if img_path and path.isfile(img_path):
        ok = api_send_photo(CHAN_ID, img_path, txt, ent)
        if ok:
            return True
        print("[WARN] Foto fallo, intentando texto solo...")

    # Texto solo con premium
    ok = api_send_message(CHAN_ID, txt, ent)
    if ok:
        return True

    # Fallback sin entities
    print("[WARN] Premium fallo, enviando sin entities...")
    try:
        ok = api_send_message(CHAN_ID, txt, [])
        return ok
    except:
        return False

# ─── Verificar duplicado ──────────────────────────────────────────────────────
def verificar(ccn):
    try:
        with open(TARJ_FILE, "r") as f:
            return ccn in f.read()
    except FileNotFoundError:
        return False

# ─── Clients ───────────────────────────────────────────────────────────────────
bot = Client("premium_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

tel_client = None
tel_ok = False

# ─── Comandos Pyrogram ────────────────────────────────────────────────────────

@bot.on_message(filters.command("start") & filters.private)
async def cmd_start(c, m):
    tel_status = "Conectado" if tel_ok else "Desconectado"
    await m.reply(f"Bot activo! v8.8\nTelethon: {tel_status}\nComandos: /status /emojis /emojischan /testimg /connect /update /restart")

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
    ses = "Si" if path.isfile(TEL_SESSION + ".session") else "NO"
    await m.reply(f"Bot v8.8\nCommit: {commit}\nImagen: {img}\nTelethon: {tel}\nSession: {ses}\nDir: {SCRIPT_DIR}")

@bot.on_message(filters.command("emojis") & filters.private)
async def cmd_emojis(c, m):
    """Test emojis premium en chat privado (usa Pyrogram)"""
    if m.from_user.id != OWNER_ID:
        return
    txt, ent = build_emoji_test()
    pyro_ent = _convert_entities_for_pyrogram(ent)
    try:
        await c.send_message(m.chat.id, txt, entities=pyro_ent)
    except Exception as e:
        await m.reply(f"Error: {e}")

@bot.on_message(filters.command("emojischan") & filters.private)
async def cmd_emojischan(c, m):
    """Test emojis premium en el canal (usa API directa)"""
    if m.from_user.id != OWNER_ID:
        return
    await m.reply("Enviando test de emojis al canal (API directa)...")
    txt, ent = build_emoji_test()
    ok = await send_hit_to_channel(txt, ent)
    if ok:
        await m.reply("Enviado! Verifica si se ven premium en el canal.")
    else:
        await m.reply("Error al enviar al canal.")

@bot.on_message(filters.command("testimg") & filters.private)
async def cmd_testimg(c, m):
    if m.from_user.id != OWNER_ID:
        return
    await m.reply("Enviando prueba completa al canal...")
    txt, ent = build_hit("411111", "4111111111111111", "12", "2026", "123",
                         "411111111111", "VISA", "CLASSIC", "CREDIT", "TEST BANK", "US", "\U0001F1FA\U0001F1F8")
    img = ensure_image()
    ok = await send_hit_to_channel(txt, ent, img)
    if ok:
        await m.reply("Enviado al canal! Verifica premium emojis.")
    else:
        await m.reply("Error al enviar al canal.")

@bot.on_message(filters.command("connect") & filters.private)
async def cmd_connect(c, m):
    if m.from_user.id != OWNER_ID:
        return
    if tel_ok:
        await m.reply("Telethon ya esta conectado!")
        return
    await m.reply("Conectando Telethon...")
    await _start_telethon()
    if tel_ok:
        await m.reply("Telethon conectado! Escuchando hits...")
    else:
        await m.reply("Telethon fallo. Ver logs.")

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


# ─── Telethon ─────────────────────────────────────────────────────────────────
async def _start_telethon():
    """Iniciar Telethon y registrar handlers"""
    global tel_client, tel_ok

    if TelegramClient is None:
        print("[WARN] Telethon no importado")
        return

    if tel_ok:
        return

    session_file = TEL_SESSION + ".session"
    if not path.isfile(session_file):
        print(f"[WARN] No hay sesion: {session_file}")
        return

    if path.getsize(session_file) < 50:
        print(f"[WARN] Sesion vacia: {session_file}")
        return

    try:
        print("[..] Conectando Telethon...")
        tel_client = TelegramClient(TEL_SESSION, API_ID, API_HASH)
        await tel_client.start()
        me = await tel_client.get_me()
        print(f"[OK] Telethon conectado como: {me.first_name} (id={me.id})")

        # Registrar handlers DESPUES de conectar
        @tel_client.on(events.NewMessage)
        @tel_client.on(events.MessageEdited)
        async def hit_handler(event):
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
                rs = http_requests.get(f"https://bins.antipublic.cc/bins/{bin_n}").json()
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

            # Enviar al canal usando API directa
            img = ensure_image()
            await send_hit_to_channel(txt, ent, img)

        tel_ok = True
        print("[OK] Telethon handlers registrados. Escuchando hits...")

    except Exception as e:
        print(f"[ERR] Telethon fallo: {e}")
        tel_client = None


# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ensure_image()
    print("=" * 40)
    print("HJ SCAM BOT v8.8")
    print("API directa para canales")
    print("=" * 40)
    print("[..] Iniciando bot.run()...")
    bot.run()
