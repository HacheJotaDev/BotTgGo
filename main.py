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
OWNER_ID = 5947916142 # Tu user ID de Telegram para comandos admin
REPO_URL = "https://github.com/HacheJotaDev/BotTgGo.git"

bot = telebot.TeleBot(TokenAthena, parse_mode="html")
system("clear")

# ─── Imagen para enviar con los hits ──────────────────────────────────────────
# Usa la imagen nueva descargada. Si no existe, fallback a hj.jpg o URL
SCRIPT_DIR = path.dirname(path.abspath(__file__))
IMAGE_PATH = path.join(SCRIPT_DIR, "nueva_img.jpg")
IMAGE_FALLBACK = path.join(SCRIPT_DIR, "hj.jpg")
IMAGE_URL = "https://i.ibb.co/9zznM39/IMG-20260607-101547-310.jpg"

def get_image():
    """Retorna la ruta de imagen disponible, o URL como último recurso."""
    if path.isfile(IMAGE_PATH):
        return IMAGE_PATH
    if path.isfile(IMAGE_FALLBACK):
        return IMAGE_FALLBACK
    return IMAGE_URL

# ─── Verificar tarjeta duplicada ──────────────────────────────────────────────

def verificar(ccn):
    tarjetas_file = path.join(SCRIPT_DIR, 'tarjetas.txt')
    try:
        with open(tarjetas_file, 'r') as f:
            r = f.read()
        return ccn in r
    except FileNotFoundError:
        return False

# ─── Comando /update — Actualizar bot desde GitHub sin entrar a la VPS ────────

@bot.message_handler(commands=['update'])
def cmd_update(message):
    """Actualiza el bot desde GitHub y lo reinicia automáticamente."""
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        bot.reply_to(message, "⛔ No tenés permiso para usar este comando.")
        return

    bot.reply_to(message, "🔄 <b>Actualizando bot desde GitHub...</b>")

    try:
        # Pull latest changes
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            capture_output=True, text=True,
            cwd=SCRIPT_DIR,
            timeout=30
        )
        output = result.stdout + result.stderr

        if "Already up to date" in output or "Already up-to-date" in output:
            bot.reply_to(message, "✅ <b>El bot ya está actualizado.</b>")
            return

        if result.returncode != 0:
            bot.reply_to(message, f"❌ <b>Error al hacer pull:</b>\n<code>{output[:1000]}</code>")
            return

        # Instalar dependencias nuevas si hay
        req_file = path.join(SCRIPT_DIR, "requirements.txt")
        if path.isfile(req_file):
            pip_result = subprocess.run(
                ["pip", "install", "-r", req_file],
                capture_output=True, text=True,
                timeout=60
            )

        # Descargar imagen si no existe
        if not path.isfile(IMAGE_PATH):
            try:
                subprocess.run(
                    ["curl", "-L", "-o", IMAGE_PATH, IMAGE_URL],
                    capture_output=True, timeout=30
                )
            except:
                pass

        bot.reply_to(message, 
            "✅ <b>Actualización descargada correctamente.</b>\n\n"
            "🔄 Reiniciando bot en 3 segundos...\n\n"
            f"<code>{output[:500]}</code>"
        )

        # Auto-restart
        subprocess.Popen(["bash", "-c", "sleep 3 && cd {} && python3 main.py".format(SCRIPT_DIR)])
        os._exit(0)

    except subprocess.TimeoutExpired:
        bot.reply_to(message, "❌ <b>Timeout: la actualización tardó demasiado.</b>")
    except Exception as e:
        bot.reply_to(message, f"❌ <b>Error:</b> <code>{str(e)[:500]}</code>")

# ─── Comando /status — Ver estado del bot ─────────────────────────────────────

@bot.message_handler(commands=['status'])
def cmd_status(message):
    """Muestra el estado actual del bot."""
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return

    # Verificar último commit
    try:
        commit = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            capture_output=True, text=True,
            cwd=SCRIPT_DIR
        )
        commit_msg = commit.stdout.strip() or "Desconocido"
    except:
        commit_msg = "No disponible"

    img_status = "✅ nueva_img.jpg" if path.isfile(IMAGE_PATH) else "⚠️ Fallback"

    bot.reply_to(message,
        f"📊 <b>Estado del Bot</b>\n\n"
        f"🔑 Commit: <code>{commit_msg}</code>\n"
        f"🖼 Imagen: {img_status}\n"
        f"📂 Directorio: <code>{SCRIPT_DIR}</code>\n"
        f"👤 Owner ID: <code>{OWNER_ID}</code>"
    )

# ─── Comando /restart — Reiniciar el bot ──────────────────────────────────────

@bot.message_handler(commands=['restart'])
def cmd_restart(message):
    """Reinicia el bot."""
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return

    bot.reply_to(message, "🔄 <b>Reiniciando bot...</b>")
    subprocess.Popen(["bash", "-c", "sleep 2 && cd {} && python3 main.py".format(SCRIPT_DIR)])
    os._exit(0)

# ─── Worker: Escuchar mensajes y capturar hits ────────────────────────────────

@client.on(events.NewMessage)
@client.on(events.MessageEdited)
async def my_event_handler(event):
    global resp
    text = event.raw_text

    res = text.split()
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

    # Validaciones
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

    # Verificar duplicado
    if verificar(cc):
        return

    # Guardar tarjeta
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

    # Generar extra
    extra2 = cc[0:12]

    # Generar nombre aleatorio basado en país
    try:
        api = requests.get(f"https://randomuser.me/api/?nat={country}&inc=name,location").json()
        name = api["results"][0]["name"]["first"]
        lastname = api["results"][0]["name"]["last"]
        street = api["results"][0]["location"]["street"]["name"]
        complement = api["results"][0]["location"]["street"]["number"]
    except:
        name, lastname, street, complement = "Name", "Last", "Street", "123"

    # ── Construir mensaje con imagen + texto ──
    img = get_image()

    new2 = f"""<b><i>HJ SCAM</i> #BIN{bin_num}</b>
<b>- - - - - - - - - - - - - - - - - - - - - - - -</b>
<b>Cc</b> ➸ <code>{cc}|{mm}|{yy}|{cvv}</code>
<b>Response</b> ➸ Approved! ✅ 
<b>Extra</> ➸ <code>{extra2}xxxx|{mm}|{yy}|rnd</code>
<b>- - - - - - - - - - - - - - - - - - - - - - - -</b>
<b>Info</b> ➸ {brand} - {level} - {type_}
<b>Bank</b> ➸ {bank}
<b>Country</b> ➸ {country} {flag}
<b>- - - - - - - - - - - - - - - - - - - - - - - -</b>
<b>Owner</b> ➸ @hjofc123
"""

    print(f"\n ✅ {Fore.LIGHTWHITE_EX}#Card Tested: {Fore.LIGHTBLUE_EX}{cc}|{mm}|{yy}|{cvv} {Fore.LIGHTWHITE_EX}/ {country}|{flag}\n"
          f"  {Fore.LIGHTWHITE_EX}#Successfully Sended - ID Channel: {Fore.LIGHTBLUE_EX}{id_channel_athena}")

    try:
        bot.send_photo(id_channel_athena, img, new2)
    except Exception as e:
        print(f"{Fore.RED}Error al enviar foto: {e}{Fore.RESET}")
        try:
            bot.send_message(id_channel_athena, new2)
        except Exception as e2:
            print(f"{Fore.RED}Error al enviar mensaje: {e2}{Fore.RESET}")


# ─── Iniciar ──────────────────────────────────────────────────────────────────

print(f"""
{Fore.RED}╔══════════════════════════════════════════╗
{Fore.RED}║         {Fore.WHITE}HJ SCAM BOT - v2.0{Fore.RED}            ║
{Fore.RED}╠══════════════════════════════════════════╣
{Fore.RED}║  {Fore.WHITE}📸 Imagen + Texto automático{Fore.RED}        ║
{Fore.RED}║  {Fore.WHITE}🔄 /update - Actualizar desde TG{Fore.RED}     ║
{Fore.RED}║  {Fore.WHITE}📊 /status - Ver estado del bot{Fore.RED}     ║
{Fore.RED}║  {Fore.WHITE}🔁 /restart - Reiniciar bot{Fore.RED}         ║
{Fore.RED}╚══════════════════════════════════════════╝{Fore.RESET}
""")

# Descargar imagen si no existe
if not path.isfile(IMAGE_PATH):
    print(f"{Fore.YELLOW}[!] Descargando imagen nueva...{Fore.RESET}")
    try:
        subprocess.run(["curl", "-L", "-o", IMAGE_PATH, IMAGE_URL], timeout=30)
        print(f"{Fore.GREEN}[✓] Imagen descargada{Fore.RESET}")
    except:
        print(f"{Fore.YELLOW}[!] No se pudo descargar, usando fallback{Fore.RESET}")

# Iniciar bot de comandos en thread separado
import threading
def run_telebot():
    bot.infinity_polling()

telebot_thread = threading.Thread(target=run_telebot, daemon=True)
telebot_thread.start()

# Iniciar cliente Telethon
client.start()
client.run_until_disconnected()
