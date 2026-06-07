from telethon import TelegramClient, events
import re
import telebot
import requests
import random
import asyncio
import os
import subprocess
from colorama import Fore
from os import system, path

# ─── Config ────────────────────────────────────────────────────────────────────

api_id = 29009837
api_hash = '1d388952a2f1f03de04a4b94f64eb6ed'

client = TelegramClient('anon', api_id, api_hash)
client.parse_mode = 'html'

TokenAthena = "7426061715:AAGuXLGMGVAVMX2POGVifHfVlBeNjUBE6bo"
id_channel_athena = -1003127906650
OWNER_ID = 5947916142
REPO_URL = "https://github.com/HacheJotaDev/BotTgGo.git"

bot = telebot.TeleBot(TokenAthena, parse_mode="html")
system("clear")

# ─── Imagen ───────────────────────────────────────────────────────────────────
SCRIPT_DIR = path.dirname(path.abspath(__file__))
IMAGE_PATH = path.join(SCRIPT_DIR, "nueva_img.jpg")
IMAGE_FALLBACK = path.join(SCRIPT_DIR, "hj.jpg")
IMAGE_URL = "https://i.ibb.co/9zznM39/IMG-20260607-101547-310.jpg"

SEP = "- - - - - - - - - - - - - - - - - - - - - - - -"


def ensure_image():
    """Descarga la imagen si no existe o está corrupta."""
    for img_path in [IMAGE_PATH, IMAGE_FALLBACK]:
        if path.isfile(img_path) and path.getsize(img_path) > 500:
            print(f"{Fore.GREEN}[✓] Imagen lista: {img_path} ({path.getsize(img_path)} bytes){Fore.RESET}")
            return img_path

    print(f"{Fore.YELLOW}[!] Descargando imagen...{Fore.RESET}")
    try:
        resp = requests.get(IMAGE_URL, timeout=20)
        if resp.status_code == 200 and len(resp.content) > 500:
            with open(IMAGE_PATH, 'wb') as f:
                f.write(resp.content)
            print(f"{Fore.GREEN}[✓] Imagen descargada ({len(resp.content)} bytes){Fore.RESET}")
            return IMAGE_PATH
    except Exception as e:
        print(f"{Fore.RED}[✗] Error descargando: {e}{Fore.RESET}")

    return None


def send_hit(chat_id, caption_text):
    """Envía foto + texto al canal."""
    img_local = ensure_image()

    # Intentar enviar foto con caption
    if img_local and path.isfile(img_local):
        try:
            with open(img_local, 'rb') as photo:
                bot.send_photo(chat_id, photo, caption=caption_text)
            print(f"{Fore.GREEN}[✓] Foto+texto enviada{Fore.RESET}")
            return True
        except Exception as e:
            print(f"{Fore.YELLOW}[!] Error foto+caption: {e}{Fore.RESET}")

    # Fallback: foto por URL con caption
    try:
        bot.send_photo(chat_id, IMAGE_URL, caption=caption_text)
        print(f"{Fore.GREEN}[✓] Foto+texto (URL){Fore.RESET}")
        return True
    except Exception as e:
        print(f"{Fore.YELLOW}[!] Error URL+caption: {e}{Fore.RESET}")

    # Fallback: foto local sin caption + texto separado
    if img_local and path.isfile(img_local):
        try:
            with open(img_local, 'rb') as photo:
                bot.send_photo(chat_id, photo)
            bot.send_message(chat_id, caption_text)
            print(f"{Fore.GREEN}[✓] Foto y texto separados{Fore.RESET}")
            return True
        except Exception as e:
            print(f"{Fore.YELLOW}[!] Error separados: {e}{Fore.RESET}")

    # Último recurso: solo texto
    try:
        bot.send_message(chat_id, caption_text)
        print(f"{Fore.YELLOW}[!] Solo texto{Fore.RESET}")
        return True
    except Exception as e:
        print(f"{Fore.RED}[✗] Error: {e}{Fore.RESET}")

    return False


# ─── Verificar tarjeta duplicada ──────────────────────────────────────────────

def verificar(ccn):
    tarjetas_file = path.join(SCRIPT_DIR, 'tarjetas.txt')
    try:
        with open(tarjetas_file, 'r') as f:
            r = f.read()
        return ccn in r
    except FileNotFoundError:
        return False

# ─── Comando /update ──────────────────────────────────────────────────────────

@bot.message_handler(commands=['update'])
def cmd_update(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        bot.reply_to(message, "⛔ No tenés permiso.")
        return

    bot.reply_to(message, "🔄 <b>Actualizando bot desde GitHub...</b>")

    try:
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            capture_output=True, text=True,
            cwd=SCRIPT_DIR, timeout=30
        )
        output = result.stdout + result.stderr

        if "Already up to date" in output or "Already up-to-date" in output:
            bot.reply_to(message, "✅ <b>El bot ya está actualizado.</b>")
            return

        if result.returncode != 0:
            bot.reply_to(message, f"❌ <b>Error:</b>\n<code>{output[:1000]}</code>")
            return

        req_file = path.join(SCRIPT_DIR, "requirements.txt")
        if path.isfile(req_file):
            subprocess.run(["pip", "install", "-r", req_file], capture_output=True, text=True, timeout=60)

        ensure_image()

        bot.reply_to(message,
            "✅ <b>Actualización correcta.</b>\n\n"
            "🔄 Reiniciando en 3s...\n\n"
            f"<code>{output[:500]}</code>"
        )

        subprocess.Popen(["bash", "-c", f"sleep 3 && cd {SCRIPT_DIR} && python3 main.py"])
        os._exit(0)

    except subprocess.TimeoutExpired:
        bot.reply_to(message, "❌ <b>Timeout.</b>")
    except Exception as e:
        bot.reply_to(message, f"❌ <b>Error:</b> <code>{str(e)[:500]}</code>")

# ─── Comando /status ──────────────────────────────────────────────────────────

@bot.message_handler(commands=['status'])
def cmd_status(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return

    try:
        commit = subprocess.run(["git", "log", "--oneline", "-1"], capture_output=True, text=True, cwd=SCRIPT_DIR)
        commit_msg = commit.stdout.strip() or "Desconocido"
    except:
        commit_msg = "No disponible"

    img_status = "✅ nueva_img.jpg" if path.isfile(IMAGE_PATH) and path.getsize(IMAGE_PATH) > 500 else "⚠️ Fallback"

    bot.reply_to(message,
        f"📊 <b>Estado del Bot</b>\n\n"
        f"🔑 Commit: <code>{commit_msg}</code>\n"
        f"🖼 Imagen: {img_status}\n"
        f"📂 Dir: <code>{SCRIPT_DIR}</code>"
    )

# ─── Comando /restart ─────────────────────────────────────────────────────────

@bot.message_handler(commands=['restart'])
def cmd_restart(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return

    bot.reply_to(message, "🔄 <b>Reiniciando...</b>")
    subprocess.Popen(["bash", "-c", f"sleep 2 && cd {SCRIPT_DIR} && python3 main.py"])
    os._exit(0)

# ─── Comando /testimg ─────────────────────────────────────────────────────────

@bot.message_handler(commands=['testimg'])
def cmd_testimg(message):
    """Envía mensaje de prueba al canal con imagen."""
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return

    bot.reply_to(message, "📸 <b>Enviando prueba al canal...</b>")

    test_msg = f"""<b><i>HJ SCAM</i> #BIN411111</b>
{SEP}
<b>Cc</b> ➸ <code>4111111111111111|12|2026|123</code>
<b>Response</b> ➸ Approved! ✅
<b>Extra</b> ➸ <code>411111111111xxxx|12|2026|rnd</code>
{SEP}
<b>Info</b> ➸ VISA - CLASSIC - CREDIT
<b>Bank</b> ➸ TEST BANK
<b>Country</b> ➸ US 🇺🇸
{SEP}
<b>Owner</b> ➸ @hjofc20
"""

    ok = send_hit(id_channel_athena, test_msg)
    if ok:
        bot.reply_to(message, "✅ <b>Enviado al canal.</b> Verificá.")
    else:
        bot.reply_to(message, "❌ <b>Error.</b> Revisá logs.")

# ─── Worker: Escuchar mensajes y capturar hits ────────────────────────────────

@client.on(events.NewMessage)
@client.on(events.MessageEdited)
async def my_event_handler(event):
    text = event.raw_text

    responses = [
        'Approved', 'Non VBV', 'Gateway Rejected: avs',
        '✅✅✅ Approved ✅✅✅', 'Succeeded! 🤑', 'APPROVED',
        'APPROVED ✅', 'Approved CCN', 'Approved #AUTH! ✅',
        'Approved ❇️', 'APPROVED ✓', '✅Appr0ved',
        'Security code incorrect✅', 'CVV2 FAILURE POSSIBLE CVV ⌯ N - AVS: G',
        'Succeeded!', '𝑨𝒑𝒑𝒓𝒐𝒗𝒆𝒅 𝑪𝒂𝒓𝒅 ✅', '𝑨𝒑𝒑𝒓𝒐𝒗𝒆𝒅',
        '𝑪𝒉𝒂𝒓𝒈𝒆𝒅 𝟎.𝟐𝟓$', '𝑪𝒉𝒂𝒓𝒈𝒆𝒅 $3 ✅', 'Subscription complete',
        'CVV LIVE ✅', 'Card Approved CCN/CCV Live', 'incorrect_cvc',
        'Approved! ✅', 'VIVA ✅'
    ]

    if not any(response in text for response in responses):
        return

    x = re.findall(r'\d+', text)

    if len(x) < 4:
        return

    cc = x[0]
    mm = x[1]
    yy = x[2]
    cvv = x[3]

    if len(cc) > 16 or len(cc) < 15:
        return
    if len(mm) > 2:
        return
    if len(yy) > 4:
        return
    if len(cvv) > 4:
        return

    # Ajustar formato de fecha
    if mm.startswith('2'):
        mm, yy = yy, mm
    if len(mm) >= 3:
        mm, yy, cvv = yy, cvv, mm
    if len(yy) == 2:
        yy = '20' + yy

    tarj = f'{cc}|{mm}|{yy}|{cvv}'

    if verificar(cc):
        return

    tarjetas_file = path.join(SCRIPT_DIR, 'tarjetas.txt')
    with open(tarjetas_file, 'a') as d:
        d.write(tarj + "\n")

    # Consultar BIN
    bin_num = cc[0:6]
    try:
        rs = requests.get(f"https://bins.antipublic.cc/bins/{bin_num}").json()
        country = rs.get("country", "??")
        flag = rs.get("country_flag", "🏳️")
        bank = rs.get("bank", "Unknown")
        brand = rs.get("brand", "Unknown")
        type_ = rs.get("type", "Unknown")
        level = rs.get("level", "Unknown")
    except:
        country, flag, bank, brand, type_, level = "??", "🏳️", "Unknown", "Unknown", "Unknown", "Unknown"

    extra2 = cc[0:12]

    # Construir mensaje
    new2 = f"""<b><i>HJ SCAM</i> #BIN{bin_num}</b>
{SEP}
<b>Cc</b> ➸ <code>{cc}|{mm}|{yy}|{cvv}</code>
<b>Response</b> ➸ Approved! ✅
<b>Extra</b> ➸ <code>{extra2}xxxx|{mm}|{yy}|rnd</code>
{SEP}
<b>Info</b> ➸ {brand} - {level} - {type_}
<b>Bank</b> ➸ {bank}
<b>Country</b> ➸ {country} {flag}
{SEP}
<b>Owner</b> ➸ @hjofc20
"""

    print(f"\n ✅ {Fore.LIGHTWHITE_EX}#Card Tested: {Fore.LIGHTBLUE_EX}{cc}|{mm}|{yy}|{cvv} {Fore.LIGHTWHITE_EX}/ {country}|{flag}\n"
          f"  {Fore.LIGHTWHITE_EX}#Successfully Sended - ID Channel: {Fore.LIGHTBLUE_EX}{id_channel_athena}")

    send_hit(id_channel_athena, new2)


# ─── Iniciar ──────────────────────────────────────────────────────────────────

print(f"""
{Fore.RED}╔══════════════════════════════════════════╗
{Fore.RED}║         {Fore.WHITE}HJ SCAM BOT - v7.0{Fore.RED}            ║
{Fore.RED}╠══════════════════════════════════════════╣
{Fore.RED}║  {Fore.WHITE}📸 Imagen + Texto automático{Fore.RED}        ║
{Fore.RED}║  {Fore.WHITE}🔄 /update - Actualizar desde TG{Fore.RED}     ║
{Fore.RED}║  {Fore.WHITE}📊 /status - Ver estado del bot{Fore.RED}     ║
{Fore.RED}║  {Fore.WHITE}🔁 /restart - Reiniciar bot{Fore.RED}         ║
{Fore.RED}║  {Fore.WHITE}🖼 /testimg - Probar envío{Fore.RED}          ║
{Fore.RED}╚══════════════════════════════════════════╝{Fore.RESET}
""")

ensure_image()

import threading
def run_telebot():
    bot.infinity_polling()

telebot_thread = threading.Thread(target=run_telebot, daemon=True)
telebot_thread.start()

client.start()
client.run_until_disconnected()
