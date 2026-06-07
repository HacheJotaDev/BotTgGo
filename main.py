"""
HJ SCAM BOT v7.0 - Simple & Clean
Diseño con guiones y ➸, sin emojis premium
Imagen + texto como caption juntos
"""
import re
import requests as http_requests
import asyncio
import os
import subprocess
import sys
from os import system, path

# ─── Imports ───────────────────────────────────────────────────────────────────
try:
    from pyrogram import Client, filters
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

SCRIPT_DIR = path.dirname(path.abspath(__file__))
IMG_PATH   = path.join(SCRIPT_DIR, "nueva_img.jpg")
IMG_FALL   = path.join(SCRIPT_DIR, "hj.jpg")
IMG_URL    = "https://i.ibb.co/9zznM39/IMG-20260607-101547-310.jpg"
TARJ_FILE  = path.join(SCRIPT_DIR, "tarjetas.txt")
TEL_SESSION = path.join(SCRIPT_DIR, "anon")

system("clear")

# ─── Imagen ────────────────────────────────────────────────────────────────────
def ensure_image():
    for p in [IMG_PATH, IMG_FALL]:
        if path.isfile(p) and path.getsize(p) > 500:
            print(f"[OK] Imagen: {p}")
            return p
    print("[!] Descargando imagen...")
    try:
        r = http_requests.get(IMG_URL, timeout=20)
        if r.status_code == 200 and len(r.content) > 500:
            with open(IMG_PATH, "wb") as f:
                f.write(r.content)
            print("[OK] Imagen descargada")
            return IMG_PATH
    except Exception as e:
        print(f"[ERR] Imagen: {e}")
    return None

# ─── Build message ─────────────────────────────────────────────────────────────
def build_hit(bin_n, cc, mm, yy, cvv, extra, brand, level, tipo, bank, country, flag):
    sep1 = "- - - - - - - - - - - - - - - - - - - - - - - -"
    sep2 = "- - - - - - - - - - - - - - - - - - - - - - - -"
    sep3 = "- - - - - - - - - - - - - - - - - - - - - - - -"
    msg = (
        f"HJ SCAM #BIN{bin_n}\n"
        f"{sep1}\n"
        f"Cc ➸ {cc}|{mm}|{yy}|{cvv}\n"
        f"Response ➸ Approved! ✅\n"
        f"Extra ➸ {extra}xxxx|{mm}|{yy}|rnd\n"
        f"{sep2}\n"
        f"Info ➸ {brand} - {level} - {tipo}\n"
        f"Bank ➸ {bank}\n"
        f"Country ➸ {country} {flag}\n"
        f"{sep3}\n"
        f"Owner ➸ @hjofc20"
    )
    return msg

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

# ─── Send to channel ───────────────────────────────────────────────────────────
async def send_hit_to_channel(text, img_path=None):
    """Enviar imagen+caption al canal como un solo mensaje"""
    try:
        if img_path and path.isfile(img_path):
            await bot.send_photo(CHAN_ID, img_path, caption=text)
            print("[OK] Foto+caption enviado al canal")
        else:
            await bot.send_message(CHAN_ID, text)
            print("[OK] Texto enviado al canal")
        return True
    except Exception as e:
        print(f"[ERR] Envio al canal: {e}")
        # Fallback sin imagen
        try:
            await bot.send_message(CHAN_ID, text)
            print("[WARN] Enviado sin imagen (fallback)")
            return True
        except Exception as e2:
            print(f"[ERR] Fallback: {e2}")
            return False

# ─── Comandos Pyrogram ────────────────────────────────────────────────────────

@bot.on_message(filters.command("start") & filters.private)
async def cmd_start(c, m):
    tel_status = "Conectado" if tel_ok else "Desconectado"
    await m.reply(f"Bot activo! v7.0\nTelethon: {tel_status}\nComandos: /status /testimg /connect /update /restart")

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
    await m.reply(f"Bot v7.0\nCommit: {commit}\nImagen: {img}\nTelethon: {tel}\nDir: {SCRIPT_DIR}")

@bot.on_message(filters.command("testimg") & filters.private)
async def cmd_testimg(c, m):
    if m.from_user.id != OWNER_ID:
        return
    await m.reply("Enviando prueba al canal...")
    msg = build_hit("411111", "4111111111111111", "12", "2026", "123",
                    "411111111111", "VISA", "CLASSIC", "CREDIT", "TEST BANK", "US", "\U0001F1FA\U0001F1F8")
    img = ensure_image()
    ok = await send_hit_to_channel(msg, img)
    if ok:
        await m.reply("Enviado al canal!")
    else:
        await m.reply("Error al enviar.")

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
        await m.reply(f"Actualizacion correcta.\nReiniciando en 3s...\n{out[:500]}")
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
        print(f"[WARN] Sesion vacia")
        return

    try:
        print("[..] Conectando Telethon...")
        tel_client = TelegramClient(TEL_SESSION, API_ID, API_HASH)
        await tel_client.start()
        me = await tel_client.get_me()
        print(f"[OK] Telethon: {me.first_name} (id={me.id})")

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

            msg = build_hit(bin_n, cc, mm, yy, cvv, cc[:12], brand, level, tipo, bank, country, flag)
            print(f"[HIT] {cc}|{mm}|{yy}|{cvv} {country}")

            img = ensure_image()
            await send_hit_to_channel(msg, img)

        tel_ok = True
        print("[OK] Escuchando hits...")

    except Exception as e:
        print(f"[ERR] Telethon: {e}")
        tel_client = None


# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ensure_image()
    print("=" * 40)
    print("HJ SCAM BOT v7.0")
    print("Simple & Clean")
    print("=" * 40)
    bot.run()
