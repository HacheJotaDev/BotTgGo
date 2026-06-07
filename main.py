from telethon import TelegramClient, events
from telethon.tl.types import (
    MessageEntityBold,
    MessageEntityItalic,
    MessageEntityCode,
    MessageEntityHashtag,
    MessageEntityCustomEmoji
)
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

# ─── Custom Emoji IDs (premium) ───────────────────────────────────────────────
EMOJI_CHAT_ID = 5427181942934088912   # 💬 premium (document_id)
EMOJI_CARD_ID = 5927169041595634481   # 💳 premium (document_id)

# Emojis Unicode (fallback visual)
CHAT_EMOJI = "\U0001f4ac"     # 💬
CARD_EMOJI = "\U0001f4b3"     # 💳
ARROW_EMOJI = "\u23e9\ufe0f"  # ⏩️


# ─── UTF-16 offset helper ─────────────────────────────────────────────────────

def utf16_len(s):
    """Longitud en UTF-16 code units (Telegram usa UTF-16 para offsets)."""
    return len(s.encode('utf-16-le')) // 2


# ─── Message Builder con Telethon entities ────────────────────────────────────

class MsgBuilder:
    """Construye texto + entidades Telethon para mensajes con emojis premium."""

    def __init__(self):
        self.text = ""
        self.entities = []

    def add(self, text, bold=False, italic=False, code=False, hashtag=False, custom_emoji_id=None):
        offset = utf16_len(self.text)
        self.text += text
        length = utf16_len(text)
        if length == 0:
            return self

        if custom_emoji_id:
            self.entities.append(MessageEntityCustomEmoji(
                offset=offset, length=length, document_id=custom_emoji_id
            ))
        if bold:
            self.entities.append(MessageEntityBold(offset=offset, length=length))
        if italic:
            self.entities.append(MessageEntityItalic(offset=offset, length=length))
        if code:
            self.entities.append(MessageEntityCode(offset=offset, length=length))
        if hashtag:
            self.entities.append(MessageEntityHashtag(offset=offset, length=length))

        return self

    def nl(self):
        self.text += "\n"
        return self

    def separator(self, count=11):
        """Línea separadora de 💬 premium."""
        for _ in range(count):
            self.add(CHAT_EMOJI, custom_emoji_id=EMOJI_CHAT_ID)
        return self.nl()

    def build(self):
        return self.text, self.entities


def build_hit_message(bin_num, cc, mm, yy, cvv, extra2, brand, level, type_, bank, country, flag):
    """Construye el mensaje hit con emojis premium via Telethon entities."""
    b = MsgBuilder()

    # HJ SCAM #BIN402348
    b.add("HJ SCAM", bold=True, italic=True)
    b.add(" ")
    b.add(f"#BIN{bin_num}", hashtag=True)
    b.nl()

    # 💬x11 separador
    b.separator()

    # 💳 Cc ⏩️ cc|mm|yy|cvv
    b.add(CARD_EMOJI, custom_emoji_id=EMOJI_CARD_ID)
    b.add(" ")
    b.add("Cc", bold=True)
    b.add(" ")
    b.add(ARROW_EMOJI)
    b.add(" ")
    b.add(f"{cc}|{mm}|{yy}|{cvv}", code=True)
    b.nl()

    # 💬 Response ⏩️ Approved! ✅
    b.add(CHAT_EMOJI, custom_emoji_id=EMOJI_CHAT_ID)
    b.add(" ")
    b.add("Response", bold=True)
    b.add(" ")
    b.add(ARROW_EMOJI)
    b.add(" Approved! ✅")
    b.nl()

    # ⚙ Extra ⏩️ ...
    b.add("⚙ ")
    b.add("Extra", bold=True)
    b.add(" ")
    b.add(ARROW_EMOJI)
    b.add(f" {extra2}xxxx|{mm}|{yy}|rnd", code=True)
    b.nl()

    # 💬x11 separador
    b.separator()

    # 🗒 Info ⏩️ ...
    b.add("🗒 ")
    b.add("Info", bold=True)
    b.add(" ")
    b.add(ARROW_EMOJI)
    b.add(f" {brand} - {level} - {type_}")
    b.nl()

    # 🏠 Bank ⏩️ ...
    b.add("🏠 ")
    b.add("Bank", bold=True)
    b.add(" ")
    b.add(ARROW_EMOJI)
    b.add(f" {bank}")
    b.nl()

    # 🌐 Country ⏩️ ...
    b.add("🌐 ")
    b.add("Country", bold=True)
    b.add(" ")
    b.add(ARROW_EMOJI)
    b.add(f" {country} {flag}")
    b.nl()

    # 💬x11 separador
    b.separator()

    # 👑 Owner  @hjofc20
    b.add("👑 ")
    b.add("Owner", bold=True)
    b.add("  @hjofc20")

    return b.build()


def build_test_message():
    """Mensaje de prueba con emojis premium."""
    b = MsgBuilder()
    b.add("TEST IMAGE", bold=True, italic=True)
    b.nl()
    b.separator()
    b.add(CARD_EMOJI, custom_emoji_id=EMOJI_CARD_ID)
    b.add(" ")
    b.add("Test", bold=True)
    b.add(" ")
    b.add(ARROW_EMOJI)
    b.add(" ")
    b.add("4111111111111111|12|2026|123", code=True)
    b.nl()
    b.add(CHAT_EMOJI, custom_emoji_id=EMOJI_CHAT_ID)
    b.add(" ")
    b.add("Response", bold=True)
    b.add(" ")
    b.add(ARROW_EMOJI)
    b.add(" Approved! ✅")
    b.nl()
    b.add("⚙ ")
    b.add("Extra", bold=True)
    b.add(" ")
    b.add(ARROW_EMOJI)
    b.add(" ")
    b.add("411111111111xxxx|12|2026|rnd", code=True)
    b.nl()
    b.separator()
    b.add("🗒 ")
    b.add("Info", bold=True)
    b.add(" ")
    b.add(ARROW_EMOJI)
    b.add(" VISA - CLASSIC - CREDIT")
    b.nl()
    b.add("🏠 ")
    b.add("Bank", bold=True)
    b.add(" ")
    b.add(ARROW_EMOJI)
    b.add(" TEST BANK")
    b.nl()
    b.add("🌐 ")
    b.add("Country", bold=True)
    b.add(" ")
    b.add(ARROW_EMOJI)
    b.add(" US 🇺🇸")
    b.nl()
    b.separator()
    b.add("👑 ")
    b.add("Owner", bold=True)
    b.add("  @hjofc20")
    return b.build()


def build_emoji_test_message():
    """Mensaje de test detallado para verificar emojis premium."""
    b = MsgBuilder()

    b.add("EMOJI TEST", bold=True, italic=True)
    b.nl()
    b.nl()

    # Sección: emojis normales vs premium
    b.add("Normal (Unicode):", bold=True)
    b.nl()
    b.add(CHAT_EMOJI)
    b.add(CARD_EMOJI)
    b.nl()
    b.nl()

    b.add("Premium (custom_emoji):", bold=True)
    b.nl()
    b.add(CHAT_EMOJI, custom_emoji_id=EMOJI_CHAT_ID)
    b.add(" ")
    b.add(CARD_EMOJI, custom_emoji_id=EMOJI_CARD_ID)
    b.nl()
    b.nl()

    b.add("Separador 11x:", bold=True)
    b.nl()
    b.separator()
    b.nl()

    b.add("Formato completo:", bold=True)
    b.nl()
    b.add(CARD_EMOJI, custom_emoji_id=EMOJI_CARD_ID)
    b.add(" ")
    b.add("Cc", bold=True)
    b.add(" ")
    b.add(ARROW_EMOJI)
    b.add(" ")
    b.add("4532015112830366|09|2028|930", code=True)
    b.nl()
    b.add(CHAT_EMOJI, custom_emoji_id=EMOJI_CHAT_ID)
    b.add(" ")
    b.add("Response", bold=True)
    b.add(" ")
    b.add(ARROW_EMOJI)
    b.add(" Approved! ✅")

    return b.build()


# ─── Imagen ────────────────────────────────────────────────────────────────────

def ensure_image():
    """Descarga la imagen si no existe o está corrupta."""
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


# ─── Envío Telethon (premium) ─────────────────────────────────────────────────

async def send_hit_to_channel(msg_text, msg_entities):
    """Envía foto + texto premium al canal usando Telethon (cuenta premium)."""
    # Enviar foto
    img_local = ensure_image()
    photo_sent = False

    if img_local and path.isfile(img_local):
        try:
            await client.send_file(id_channel_athena, img_local)
            photo_sent = True
            print(f"{Fore.GREEN}[✓] Foto enviada (Telethon){Fore.RESET}")
        except Exception as e:
            print(f"{Fore.YELLOW}[!] Error foto Telethon: {e}{Fore.RESET}")

    if not photo_sent:
        try:
            # Enviar foto por URL via bot API
            bot.send_photo(id_channel_athena, IMAGE_URL)
            print(f"{Fore.GREEN}[✓] Foto enviada (bot URL){Fore.RESET}")
        except Exception as e:
            print(f"{Fore.YELLOW}[!] Error foto URL: {e}{Fore.RESET}")

    # Enviar texto con emojis premium via Telethon
    try:
        await client.send_message(
            id_channel_athena,
            msg_text,
            formatting_entities=msg_entities
        )
        print(f"{Fore.GREEN}[✓] Texto premium enviado (Telethon){Fore.RESET}")
        return True
    except Exception as e:
        print(f"{Fore.RED}[✗] Error texto premium: {e}{Fore.RESET}")

        # Fallback: enviar sin entidades premium
        try:
            await client.send_message(id_channel_athena, msg_text)
            print(f"{Fore.YELLOW}[!] Texto enviado sin premium (fallback){Fore.RESET}")
            return True
        except Exception as e2:
            print(f"{Fore.RED}[✗] Error fallback: {e2}{Fore.RESET}")

    return False


def send_telethon_sync(chat_id, msg_text, msg_entities):
    """Envía mensaje premium via Telethon desde contexto síncrono (bot handlers)."""
    future = asyncio.run_coroutine_threadsafe(
        client.send_message(chat_id, msg_text, formatting_entities=msg_entities),
        client.loop
    )
    try:
        future.result(timeout=15)
        return True
    except Exception as e:
        print(f"{Fore.RED}[✗] Error send_telethon_sync: {e}{Fore.RESET}")
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
        bot.reply_to(message, "⛔ No tenés permiso para usar este comando.")
        return

    bot.reply_to(message, "🔄 <b>Actualizando bot desde GitHub...</b>")

    try:
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

        req_file = path.join(SCRIPT_DIR, "requirements.txt")
        if path.isfile(req_file):
            subprocess.run(["pip", "install", "-r", req_file], capture_output=True, text=True, timeout=60)

        ensure_image()

        bot.reply_to(message,
            "✅ <b>Actualización descargada correctamente.</b>\n\n"
            "🔄 Reiniciando bot en 3 segundos...\n\n"
            f"<code>{output[:500]}</code>"
        )

        subprocess.Popen(["bash", "-c", "sleep 3 && cd {} && python3 main.py".format(SCRIPT_DIR)])
        os._exit(0)

    except subprocess.TimeoutExpired:
        bot.reply_to(message, "❌ <b>Timeout: la actualización tardó demasiado.</b>")
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
        f"📂 Directorio: <code>{SCRIPT_DIR}</code>\n"
        f"👤 Owner ID: <code>{OWNER_ID}</code>"
    )

# ─── Comando /restart ─────────────────────────────────────────────────────────

@bot.message_handler(commands=['restart'])
def cmd_restart(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return

    bot.reply_to(message, "🔄 <b>Reiniciando bot...</b>")
    subprocess.Popen(["bash", "-c", "sleep 2 && cd {} && python3 main.py".format(SCRIPT_DIR)])
    os._exit(0)

# ─── Comando /testimg ─────────────────────────────────────────────────────────

@bot.message_handler(commands=['testimg'])
def cmd_testimg(message):
    """Envía imagen de prueba + texto premium al canal."""
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return

    bot.reply_to(message, "📸 <b>Enviando imagen de prueba al canal...</b>")
    msg_text, msg_entities = build_test_message()
    ok = send_telethon_sync(id_channel_athena, msg_text, msg_entities)
    if ok:
        bot.reply_to(message, "✅ <b>Mensaje enviado al canal.</b> Verificá el canal.")
    else:
        bot.reply_to(message, "❌ <b>Error.</b> Revisá los logs.")

# ─── Comando /emojis ─────────────────────────────────────────────────────────

@bot.message_handler(commands=['emojis'])
def cmd_emojis(message):
    """Testea emojis premium - envía al chat actual."""
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return

    chat_id = message.chat.id
    msg_text, msg_entities = build_emoji_test_message()
    ok = send_telethon_sync(chat_id, msg_text, msg_entities)

    if ok:
        bot.reply_to(message, "✅ <b>Emojis premium enviados via Telethon (cuenta premium).</b>")
    else:
        bot.reply_to(message, "❌ <b>Error enviando emojis.</b> Revisá los logs en la VPS.")

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

    extra2 = cc[0:12]

    try:
        api = requests.get(f"https://randomuser.me/api/?nat={country}&inc=name,location").json()
        name = api["results"][0]["name"]["first"]
        lastname = api["results"][0]["name"]["last"]
        street = api["results"][0]["location"]["street"]["name"]
        complement = api["results"][0]["location"]["street"]["number"]
    except:
        name, lastname, street, complement = "Name", "Last", "Street", "123"

    # Construir mensaje con emojis premium
    msg_text, msg_entities = build_hit_message(
        bin_num, cc, mm, yy, cvv, extra2,
        brand, level, type_, bank, country, flag
    )

    print(f"\n ✅ {Fore.LIGHTWHITE_EX}#Card Tested: {Fore.LIGHTBLUE_EX}{cc}|{mm}|{yy}|{cvv} {Fore.LIGHTWHITE_EX}/ {country}|{flag}\n"
          f"  {Fore.LIGHTWHITE_EX}#Successfully Sended - ID Channel: {Fore.LIGHTBLUE_EX}{id_channel_athena}")

    # Enviar foto + texto premium via Telethon (cuenta premium)
    await send_hit_to_channel(msg_text, msg_entities)


# ─── Iniciar ──────────────────────────────────────────────────────────────────

print(f"""
{Fore.RED}╔══════════════════════════════════════════╗
{Fore.RED}║         {Fore.WHITE}HJ SCAM BOT - v6.0{Fore.RED}            ║
{Fore.RED}╠══════════════════════════════════════════╣
{Fore.RED}║  {Fore.WHITE}💬 Premium via Telethon userbot{Fore.RED}     ║
{Fore.RED}║  {Fore.WHITE}📸 Imagen + Texto automático{Fore.RED}        ║
{Fore.RED}║  {Fore.WHITE}🔄 /update - Actualizar desde TG{Fore.RED}     ║
{Fore.RED}║  {Fore.WHITE}📊 /status - Ver estado del bot{Fore.RED}     ║
{Fore.RED}║  {Fore.WHITE}🔁 /restart - Reiniciar bot{Fore.RED}         ║
{Fore.RED}║  {Fore.WHITE}🖼 /testimg - Probar imagen+texto{Fore.RED}   ║
{Fore.RED}║  {Fore.WHITE}😀 /emojis - Testear emojis premium{Fore.RED}  ║
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
