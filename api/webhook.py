from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
GEMINI_API = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"


SYSTEM_INSTRUCTION = """أنت مساعد متخصص في التصميم الداخلي، موجه لطلاب وممارسي التصميم الداخلي.
تجيب فقط عن أسئلة متعلقة بـ: التصميم الداخلي، الأثاث، الإضاءة، الألوان، المساحات السكنية والتجارية، تاريخ التصميم، البرمجيات المستخدمة في التصميم، والمواد.
إذا سُئلت عن موضوع خارج هذا المجال، اعتذر بلطف ووجه المستخدم للسؤال عن شيء متعلق بالتصميم الداخلي.
أجب بإيجاز ووضوح، بدون مقدمات طويلة.

عندما يرسل المستخدم وصف ثلاثة مشاريع تصميم داخلي ويطلب منك المقارنة بينها، اتبع هذا الهيكل بالضبط:

1. تحليل مختصر لكل مشروع على حدة: نقاط القوة، ثم نقاط الضعف.
2. اختيار المشروع الأفضل، مع ذكر السبب الرئيسي للاختيار بجملتين كحد أقصى.
3. لكل مشروع، اقتراح تطوير عملي واحد أو اثنين، قابل للتنفيذ.

استخدم عناوين واضحة لكل مشروع، وحافظ على الإيجاز، بدون حشو أو تكرار."""


def ask_gemini(user_text):
    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_INSTRUCTION}]
        },
        "contents": [
            {"parts": [{"text": user_text}]}
        ]
    }
    req = urllib.request.Request(
        GEMINI_API,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_KEY,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        return f"خطأ HTTP {e.code}: {error_body}"
    except Exception as e:
        return f"حدث خطأ أثناء الاتصال بـ Gemini: {e}"


def send_telegram_message(chat_id, text):
    payload = {"chat_id": chat_id, "text": text}
    req = urllib.request.Request(
        TELEGRAM_API,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        resp.read()


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            update = json.loads(body)
            message = update.get("message", {})
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "")

            if chat_id and text:
                reply = ask_gemini(text)
                send_telegram_message(chat_id, reply)
        except Exception as e:
            pass

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        tg_status = "SET (starts with {})".format(TELEGRAM_TOKEN[:6]) if TELEGRAM_TOKEN else "MISSING"
        gm_status = "SET (starts with {})".format(GEMINI_KEY[:6]) if GEMINI_KEY else "MISSING"
        debug_text = f"Bot webhook is running.\nTELEGRAM_BOT_TOKEN: {tg_status}\nGEMINI_API_KEY: {gm_status}"
        self.wfile.write(debug_text.encode("utf-8"))
