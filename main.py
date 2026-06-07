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
SCRIPT_DIR = path.dirname(path.abspath(__file__))
IMAGE_PATH = path.join(SCRIPT_DIR, "nueva_img.jpg")
IMAGE_FALLBACK = path.join(SCRIPT_DIR, "hj.jpg")
IMAGE_URL = "https://i.ibb.co/9zznM39/IMG-20260607-101547-310.jpg"

# ─── Custom Emoji IDs (premium) ───────────────────────────────────────────────
EMOJI_CHAT_ID = "5427181942934088912"     # 💬 premium
EMOJI_CARD_ID = "5927169041595634481"     # 💳 premium

# ⏩️ es emoji normal, NO premium — se usa directo sin tg-emoji
ARROW = "\u23e9\ufe0f"  # ⏩️

def ce(emoji_id, fallback):
    """Genera tag tg-emoji para emojis premium personalizados."""
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

# Atajos de emojis premium
CHAT = ce(EMOJI_CHAT_ID, "\U0001f4ac")  # 💬 premium
CARD = ce(EMOJI_CARD_ID, "\U0001f4b3")  # 💳 premium
SEPARATOR = CHAT * 11  # Línea separadora de 11 💬


def ensure_image():
    """Descarga la imagen con requests si no existe o está corrupta. Retorna la ruta local o None."""
    for img_path in [IMAGE_PATH, IMAGE_FALLBACK]:
        if path.isfile(img_path) and path.getsize(img_path) > 500:
            print(f"{Fore.GREEN}[✓] Imagen lista: {img_path} ({path.getsize(img_path)} bytes){Fore.RESET}")
            return img_path

    print(f"{Fore.YELLOW}[!] Descargando imagen desde URL...{Fore.RESET}")
    try:
        resp = requests.get(IMAGE_URL, timeout=20)
        if resp.status_code == 200 and len(resp.content) > 500:
            with open(IMAGE_PATH, 'wb') as f:
                f.write(resp.content)
            print(f"{Fore.GREEN}[✓] Imagen descargada ({len(resp.content)} bytes){Fore.RESET}")
            return IMAGE_PATH
        else:
            print(f"{Fore.RED}[✗] Respuesta inválida: status={resp.status_code}, size={len(resp.content)}{Fore.RESET}")
    except Exception as e:
        print(f"{Fore.RED}[✗] Error descargando imagen: {e}{Fore.RESET}")

    return None


def send_hit_photo(chat_id, caption_text):
    """Envía foto + texto al canal. Foto primero, texto con emojis premium después."""
    img_local = ensure_image()

    # ── Enviar foto ──
    photo_sent = False
    if img_local and path.isfile(img_local):
        try:
            with open(img_local, 'rb') as photo_file:
                bot.send_photo(chat_id, photo_file)
            photo_sent = True
            print(f"{Fore.GREEN}[✓] Foto enviada{Fore.RESET}")
        except Exception as e:
            print(f"{Fore.YELLOW}[!] Error enviando foto: {e}{Fore.RESET}")

    if not photo_sent:
        try:
            bot.send_photo(chat_id, IMAGE_URL)
            photo_sent = True
            print(f"{Fore.GREEN}[✓] Foto enviada (URL){Fore.RESET}")
        except Exception as e:
            print(f"{Fore.YELLOW}[!] Error con URL de foto: {e}{Fore.RESET}")

    # ── Enviar texto con emojis premium (mensaje separado, sin límite de 1024) ──
    try:
        bot.send_message(chat_id, caption_text)
        print(f"{Fore.GREEN}[✓] Texto premium enviado{Fore.RESET}")
        return True
    except Exception as e:
        print(f"{Fore.RED}[✗] Error enviando texto: {e}{Fore.RESET}")

    # ── Último recurso: texto sin tg-emoji ──
    try:
        clean = caption_text
        for eid in [EMOJI_CHAT_ID, EMOJI_CARD_ID]:
            clean = clean.replace(f'<tg-emoji emoji-id="{eid}">', '').replace('</tg-emoji>', '')
        bot.send_message(chat_id, clean)
        print(f"{Fore.YELLOW}[!] Texto enviado sin emojis premium{Fore.RESET}")
        return True
    except Exception as e:
        print(f"{Fore.RED}[✗] Error enviando mensaje: {e}{Fore.RESET}")

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

        # Descargar imagen si no existe o está corrupta
        ensure_image()

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

    img_status = "✅ nueva_img.jpg" if path.isfile(IMAGE_PATH) and path.getsize(IMAGE_PATH) > 500 else "⚠️ Fallback"

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

# ─── Comando /testimg — Probar envío de imagen ────────────────────────────────

@bot.message_handler(commands=['testimg'])
def cmd_testimg(message):
    """Envía una imagen de prueba al canal para verificar que funciona."""
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return

    bot.reply_to(message, "📸 <b>Enviando imagen de prueba al canal...</b>")
    test_caption = f"""<b><i>TEST IMAGE</i></b>
{SEPARATOR}
{CARD} <b>Test</b> {ARROW} <code>4111111111111111|12|2026|123</code>
{CHAT} <b>Response</b> {ARROW} Approved! ✅
⚙ <b>Extra</b> {ARROW} <code>411111111111xxxx|12|2026|rnd</code>
{SEPARATOR}
🗒 <b>Info</b> {ARROW} VISA - CLASSIC - CREDIT
🏠 <b>Bank</b> {ARROW} TEST BANK
🌐 <b>Country</b> {ARROW} US 🇺🇸
{SEPARATOR}
👑 <b>Owner</b>  @hjofc20
"""

    ok = send_hit_photo(id_channel_athena, test_caption)
    if ok:
        bot.reply_to(message, "✅ <b>Imagen enviada al canal.</b> Verificá el canal.")
    else:
        bot.reply_to(message, "❌ <b>No se pudo enviar la imagen.</b> Revisá los logs en la VPS.")

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

    # ── Construir mensaje con emojis premium ──
    new2 = f"""<b><i>HJ SCAM</i> #BIN{bin_num}</b>
{SEPARATOR}
{CARD} <b>Cc</b> {ARROW} <code>{cc}|{mm}|{yy}|{cvv}</code>
{CHAT} <b>Response</b> {ARROW} Approved! ✅
⚙ <b>Extra</b> {ARROW} <code>{extra2}xxxx|{mm}|{yy}|rnd</code>
{SEPARATOR}
🗒 <b>Info</b> {ARROW} {brand} - {level} - {type_}
🏠 <b>Bank</b> {ARROW} {bank}
🌐 <b>Country</b> {ARROW} {country} {flag}
{SEPARATOR}
👑 <b>Owner</b>  @hjofc20
"""

    print(f"\n ✅ {Fore.LIGHTWHITE_EX}#Card Tested: {Fore.LIGHTBLUE_EX}{cc}|{mm}|{yy}|{cvv} {Fore.LIGHTWHITE_EX}/ {country}|{flag}\n"
          f"  {Fore.LIGHTWHITE_EX}#Successfully Sended - ID Channel: {Fore.LIGHTBLUE_EX}{id_channel_athena}")

    # Enviar foto + caption
    send_hit_photo(id_channel_athena, new2)


# ─── Iniciar ──────────────────────────────────────────────────────────────────

print(f"""
{Fore.RED}╔══════════════════════════════════════════╗
{Fore.RED}║         {Fore.WHITE}HJ SCAM BOT - v4.0{Fore.RED}            ║
{Fore.RED}╠══════════════════════════════════════════╣
{Fore.RED}║  {Fore.WHITE}💬 Emojis Premium activados{Fore.RED}          ║
{Fore.RED}║  {Fore.WHITE}📸 Imagen + Texto automático{Fore.RED}        ║
{Fore.RED}║  {Fore.WHITE}🔄 /update - Actualizar desde TG{Fore.RED}     ║
{Fore.RED}║  {Fore.WHITE}📊 /status - Ver estado del bot{Fore.RED}     ║
{Fore.RED}║  {Fore.WHITE}🔁 /restart - Reiniciar bot{Fore.RED}         ║
{Fore.RED}║  {Fore.WHITE}🖼 /testimg - Probar imagen{Fore.RED}         ║
{Fore.RED}╚══════════════════════════════════════════╝{Fore.RESET}
""")

# Asegurar que la imagen existe al iniciar
ensure_image()

# Iniciar bot de comandos en thread separado
import threading
def run_telebot():
    bot.infinity_polling()

telebot_thread = threading.Thread(target=run_telebot, daemon=True)
telebot_thread.start()

# Iniciar cliente Telethon
client.start()
client.run_until_disconnected()
