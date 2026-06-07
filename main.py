from telethon import TelegramClient, events
from pyrogram import Client, filters
from pyrogram.types import MessageEntity
from pyrogram.enums import MessageEntityType
import re
import requests
import asyncio
import os
import subprocess
from colorama import Fore
from os import system, path

# ─── Config ────────────────────────────────────────────────────────────────────
api_id = 29009837
api_hash = '1d388952a2f1f03de04a4b94f64eb6ed'
BOT_TOKEN = "8594813440:AAFFKfWwup01Si1C-exXIN2InTABuKgRv7g"
id_channel_athena = -1003127906650
OWNER_ID = 5947916142
REPO_URL = "https://github.com/HacheJotaDev/BotTgGo.git"

system("clear")

# ─── Clients ───────────────────────────────────────────────────────────────────
# Telethon: userbot para escuchar canales
client = TelegramClient('anon', api_id, api_hash)

# Pyrogram: bot para enviar mensajes con emojis premium + comandos
bot = Client("premium_bot", api_id=api_id, api_hash=api_hash, bot_token=BOT_TOKEN)

# ─── Custom Emoji IDs (premium) ───────────────────────────────────────────────
CHAT_ID  = 5427181942934088912   # 💬
CARD_ID  = 5927169041595634481   # 💳
ARROW_ID = 5197375087786874047   # ⏩️
GLOBE_ID = 5879585266426973039   # 🌐
HOUSE_ID = 5967822972931542886   # 🏠
NOTEPAD_ID = 5877597667231534929 # 🗒

# Normal emojis (sin premium)
CROWN = "\U0001f451"    # 👑
GEAR  = "\u2699\ufe0f"  # ⚙

# Unicode fallbacks
CHAT_U  = "\U0001f4ac"     # 💬
CARD_U  = "\U0001f4b3"     # 💳
ARROW_U = "\u23e9\ufe0f"  # ⏩️
GLOBE_U = "\U0001f310"    # 🌐
HOUSE_U = "\U0001f3e0"    # 🏠
NOTEPAD_U = "\U0001f5d2"  # 🗒

# ─── Imagen ───────────────────────────────────────────────────────────────────
SCRIPT_DIR = path.dirname(path.abspath(__file__))
IMAGE_PATH = path.join(SCRIPT_DIR, "nueva_img.jpg")
IMAGE_FALLBACK = path.join(SCRIPT_DIR, "hj.jpg")
IMAGE_URL = "https://i.ibb.co/9zznM39/IMG-20260607-101547-310.jpg"


def ensure_image():
    for img_path in [IMAGE_PATH, IMAGE_FALLBACK]:
        if path.isfile(img_path) and path.getsize(img_path) > 500:
            print(f"{Fore.GREEN}[✓] Imagen: {img_path}{Fore.RESET}")
            return img_path
    print(f"{Fore.YELLOW}[!] Descargando imagen...{Fore.RESET}")
    try:
        resp = requests.get(IMAGE_URL, timeout=20)
        if resp.status_code == 200 and len(resp.content) > 500:
            with open(IMAGE_PATH, 'wb') as f:
                f.write(resp.content)
            print(f"{Fore.GREEN}[✓] Descargada{Fore.RESET}")
            return IMAGE_PATH
    except Exception as e:
        print(f"{Fore.RED}[✗] Error: {e}{Fore.RESET}")
    return None


# ─── UTF-16 offset helper ─────────────────────────────────────────────────────
def utf16_len(s):
    return len(s.encode('utf-16-le')) // 2


# ─── Message Builder ──────────────────────────────────────────────────────────
class MsgBuilder:
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
            self.entities.append(MessageEntity(
                type=MessageEntityType.CUSTOM_EMOJI,
                offset=offset,
                length=length,
                custom_emoji_id=custom_emoji_id
            ))
        if bold:
            self.entities.append(MessageEntity(
                type=MessageEntityType.BOLD, offset=offset, length=length
            ))
        if italic:
            self.entities.append(MessageEntity(
                type=MessageEntityType.ITALIC, offset=offset, length=length
            ))
        if code:
            self.entities.append(MessageEntity(
                type=MessageEntityType.CODE, offset=offset, length=length
            ))
        if hashtag:
            self.entities.append(MessageEntity(
                type=MessageEntityType.HASHTAG, offset=offset, length=length
            ))
        return self

    def nl(self):
        self.text += "\n"
        return self

    def sep(self, count=11):
        for _ in range(count):
            self.add(CHAT_U, custom_emoji_id=CHAT_ID)
        return self.nl()

    def build(self):
        return self.text, self.entities


def build_hit_message(bin_num, cc, mm, yy, cvv, extra2, brand, level, type_, bank, country, flag):
    b = MsgBuilder()

    # HJ SCAM #BIN402348
    b.add("HJ SCAM", bold=True, italic=True)
    b.add(" ")
    b.add(f"#BIN{bin_num}", hashtag=True)
    b.nl()

    # 💬x11
    b.sep()

    # 💳 Cc ⏩️ data
    b.add(CARD_U, custom_emoji_id=CARD_ID)
    b.add(" ")
    b.add("Cc", bold=True)
    b.add(" ")
    b.add(ARROW_U, custom_emoji_id=ARROW_ID)
    b.add(" ")
    b.add(f"{cc}|{mm}|{yy}|{cvv}", code=True)
    b.nl()

    # 💬 Response ⏩️ Approved! ✅
    b.add(CHAT_U, custom_emoji_id=CHAT_ID)
    b.add(" ")
    b.add("Response", bold=True)
    b.add(" ")
    b.add(ARROW_U, custom_emoji_id=ARROW_ID)
    b.add(" Approved! ✅")
    b.nl()

    # ⚙ Extra ⏩️data
    b.add(GEAR)
    b.add(" ")
    b.add("Extra", bold=True)
    b.add(" ")
    b.add(ARROW_U, custom_emoji_id=ARROW_ID)
    b.add(f"{extra2}xxxx|{mm}|{yy}|rnd", code=True)
    b.nl()

    # 💬x11
    b.sep()

    # 🗒 Info ⏩️ ...
    b.add(NOTEPAD_U, custom_emoji_id=NOTEPAD_ID)
    b.add(" ")
    b.add("Info", bold=True)
    b.add(" ")
    b.add(ARROW_U, custom_emoji_id=ARROW_ID)
    b.add(f" {brand} - {level} - {type_}")
    b.nl()

    # 🏠 Bank ⏩️ ...
    b.add(HOUSE_U, custom_emoji_id=HOUSE_ID)
    b.add(" ")
    b.add("Bank", bold=True)
    b.add(" ")
    b.add(ARROW_U, custom_emoji_id=ARROW_ID)
    b.add(f" {bank}")
    b.nl()

    # 🌐 Country ⏩️ ...
    b.add(GLOBE_U, custom_emoji_id=GLOBE_ID)
    b.add(" ")
    b.add("Country", bold=True)
    b.add(" ")
    b.add(ARROW_U, custom_emoji_id=ARROW_ID)
    b.add(f" {country} {flag}")
    b.nl()

    # 💬x10
    b.sep(10)

    # 👑Owner  @hjofc20
    b.add(CROWN)
    b.add("Owner", bold=True)
    b.add("  @hjofc20")

    return b.build()


def build_emoji_test():
    b = MsgBuilder()
    b.add("EMOJI TEST", bold=True, italic=True)
    b.nl()
    b.nl()
    b.add("💬 premium → ", bold=True)
    b.add(CHAT_U, custom_emoji_id=CHAT_ID)
    b.nl()
    b.add("💳 premium → ", bold=True)
    b.add(CARD_U, custom_emoji_id=CARD_ID)
    b.nl()
    b.add("⏩️ premium → ", bold=True)
    b.add(ARROW_U, custom_emoji_id=ARROW_ID)
    b.nl()
    b.add("🗒 premium → ", bold=True)
    b.add(NOTEPAD_U, custom_emoji_id=NOTEPAD_ID)
    b.nl()
    b.add("🏠 premium → ", bold=True)
    b.add(HOUSE_U, custom_emoji_id=HOUSE_ID)
    b.nl()
    b.add("🌐 premium → ", bold=True)
    b.add(GLOBE_U, custom_emoji_id=GLOBE_ID)
    b.nl()
    b.add("👑 normal → ", bold=True)
    b.add(CROWN)
    b.nl()
    b.add("⚙ normal → ", bold=True)
    b.add(GEAR)
    b.nl()
    b.nl()
    b.add("Separador 11x 💬:", bold=True)
    b.nl()
    b.sep()
    b.nl()
    b.add("Formato completo:", bold=True)
    b.nl()
    b.add(CARD_U, custom_emoji_id=CARD_ID)
    b.add(" ")
    b.add("Cc", bold=True)
    b.add(" ")
    b.add(ARROW_U, custom_emoji_id=ARROW_ID)
    b.add(" ")
    b.add("4532015112830366|09|2028|930", code=True)
    b.nl()
    b.add(CHAT_U, custom_emoji_id=CHAT_ID)
    b.add(" ")
    b.add("Response", bold=True)
    b.add(" ")
    b.add(ARROW_U, custom_emoji_id=ARROW_ID)
    b.add(" Approved! ✅")
    return b.build()


# ─── Verificar duplicado ──────────────────────────────────────────────────────
def verificar(ccn):
    tarjetas_file = path.join(SCRIPT_DIR, 'tarjetas.txt')
    try:
        with open(tarjetas_file, 'r') as f:
            return ccn in f.read()
    except FileNotFoundError:
        return False


# ─── Pyrogram Command Handlers ────────────────────────────────────────────────

@bot.on_message(filters.command("update") & filters.private)
async def cmd_update(client_pyro, message):
    if message.from_user.id != OWNER_ID:
        await message.reply("⛔ No tenés permiso.")
        return

    await message.reply("🔄 Actualizando bot desde GitHub...")

    try:
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            capture_output=True, text=True,
            cwd=SCRIPT_DIR, timeout=30
        )
        output = result.stdout + result.stderr

        if "Already up to date" in output or "Already up-to-date" in output:
            await message.reply("✅ El bot ya está actualizado.")
            return

        if result.returncode != 0:
            await message.reply(f"❌ Error:\n{output[:1000]}")
            return

        req_file = path.join(SCRIPT_DIR, "requirements.txt")
        if path.isfile(req_file):
            subprocess.run(["pip", "install", "-r", req_file], capture_output=True, text=True, timeout=60)

        ensure_image()

        await message.reply(f"✅ Actualización correcta.\n🔄 Reiniciando en 3s...\n{output[:500]}")
        subprocess.Popen(["bash", "-c", f"sleep 3 && cd {SCRIPT_DIR} && python3 main.py"])
        os._exit(0)

    except subprocess.TimeoutExpired:
        await message.reply("❌ Timeout.")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)[:500]}")


@bot.on_message(filters.command("status") & filters.private)
async def cmd_status(client_pyro, message):
    if message.from_user.id != OWNER_ID:
        return
    try:
        commit = subprocess.run(["git", "log", "--oneline", "-1"], capture_output=True, text=True, cwd=SCRIPT_DIR)
        commit_msg = commit.stdout.strip() or "Desconocido"
    except:
        commit_msg = "No disponible"
    img = "✅ nueva_img.jpg" if path.isfile(IMAGE_PATH) and path.getsize(IMAGE_PATH) > 500 else "⚠️ Fallback"
    await message.reply(f"📊 Estado del Bot\n\n🔑 Commit: {commit_msg}\n🖼 Imagen: {img}\n📂 Dir: {SCRIPT_DIR}")


@bot.on_message(filters.command("restart") & filters.private)
async def cmd_restart(client_pyro, message):
    if message.from_user.id != OWNER_ID:
        return
    await message.reply("🔄 Reiniciando...")
    subprocess.Popen(["bash", "-c", f"sleep 2 && cd {SCRIPT_DIR} && python3 main.py"])
    os._exit(0)


@bot.on_message(filters.command("emojis") & filters.private)
async def cmd_emojis(client_pyro, message):
    if message.from_user.id != OWNER_ID:
        return
    msg_text, msg_entities = build_emoji_test()
    try:
        await client_pyro.send_message(
            message.chat.id,
            msg_text,
            entities=msg_entities
        )
        await message.reply("✅ Emojis premium enviados. Si ves animación/color especial, funcionan.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@bot.on_message(filters.command("testimg") & filters.private)
async def cmd_testimg(client_pyro, message):
    if message.from_user.id != OWNER_ID:
        return
    await message.reply("📸 Enviando prueba al canal...")
    msg_text, msg_entities = build_hit_message(
        "411111", "4111111111111111", "12", "2026", "123",
        "411111111111", "VISA", "CLASSIC", "CREDIT",
        "TEST BANK", "US", "🇺🇸"
    )
    try:
        # Enviar foto
        img = ensure_image()
        if img and path.isfile(img):
            await client_pyro.send_photo(id_channel_athena, img)
        # Enviar texto premium
        await client_pyro.send_message(id_channel_athena, msg_text, entities=msg_entities)
        await message.reply("✅ Enviado al canal.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


# ─── Telethon Worker: escuchar hits ───────────────────────────────────────────

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

    tarj = f'{cc}|{mm}|{yy}|{cvv}'

    if verificar(cc):
        return

    with open(path.join(SCRIPT_DIR, 'tarjetas.txt'), 'a') as d:
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

    # Construir mensaje con emojis premium
    msg_text, msg_entities = build_hit_message(
        bin_num, cc, mm, yy, cvv, extra2,
        brand, level, type_, bank, country, flag
    )

    print(f"\n ✅ {Fore.LIGHTWHITE_EX}#Card: {Fore.LIGHTBLUE_EX}{cc}|{mm}|{yy}|{cvv} {Fore.LIGHTWHITE_EX}/ {country}|{flag}")

    # Enviar foto + texto premium via Pyrogram
    try:
        img = ensure_image()
        if img and path.isfile(img):
            await bot.send_photo(id_channel_athena, img)
        await bot.send_message(id_channel_athena, msg_text, entities=msg_entities)
        print(f"{Fore.GREEN}[✓] Foto+premium enviado{Fore.RESET}")
    except Exception as e:
        print(f"{Fore.RED}[✗] Error Pyrogram: {e}{Fore.RESET}")
        # Fallback sin premium
        try:
            await bot.send_message(id_channel_athena, msg_text)
            print(f"{Fore.YELLOW}[!] Enviado sin premium{Fore.RESET}")
        except Exception as e2:
            print(f"{Fore.RED}[✗] Error fallback: {e2}{Fore.RESET}")


# ─── Iniciar ──────────────────────────────────────────────────────────────────

print(f"""
{Fore.RED}╔══════════════════════════════════════════╗
{Fore.RED}║         {Fore.WHITE}HJ SCAM BOT - v8.0{Fore.RED}            ║
{Fore.RED}╠══════════════════════════════════════════╣
{Fore.RED}║  {Fore.WHITE}💬 Emojis Premium (Pyrogram){Fore.RED}        ║
{Fore.RED}║  {Fore.WHITE}📸 Imagen + Texto automático{Fore.RED}        ║
{Fore.RED}║  {Fore.WHITE}🔄 /update - Actualizar desde TG{Fore.RED}     ║
{Fore.RED}║  {Fore.WHITE}📊 /status - Ver estado{Fore.RED}              ║
{Fore.RED}║  {Fore.WHITE}🔁 /restart - Reiniciar bot{Fore.RED}         ║
{Fore.RED}║  {Fore.WHITE}🖼 /testimg - Probar envío{Fore.RED}          ║
{Fore.RED}║  {Fore.WHITE}😀 /emojis - Testear emojis premium{Fore.RED}  ║
{Fore.RED}╚══════════════════════════════════════════╝{Fore.RESET}
""")

ensure_image()


async def main():
    await bot.start()
    print(f"{Fore.GREEN}[✓] Pyrogram bot iniciado{Fore.RESET}")
    await client.start()
    print(f"{Fore.GREEN}[✓] Telethon userbot iniciado{Fore.RESET}")
    print(f"{Fore.GREEN}[✓] Todo listo. Escuchando hits...{Fore.RESET}")
    await client.run_until_disconnected()


asyncio.run(main())
