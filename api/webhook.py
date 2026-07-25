from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
GEMINI_API = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"


def ask_gemini(user_text):
    payload = {
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
