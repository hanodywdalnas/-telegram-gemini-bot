ChatGPT





ممتاز، نحن الآن في مرحلة التطوير الفعلي.

لكن الرابط الذي أرسلته يشير إلى صفحة GitHub، وأنا لا أستطيع استخراج محتوى الملف البرمجي من رابط العرض وحده في هذه المحادثة. أحتاج إلى الكود نفسه حتى أتمكن من تعديله بدقة. 

لدينا خياران:

الأفضل: أرسل رابط المستودع كاملًا (وليس رابط ملف واحد)، مثل:

https://github.com/hanodywdalnas/-telegram-gemini-bot
ثم أعطني صلاحية معرفة الملفات التي نحتاجها.

أو افتح ملف api/webhook.py في GitHub، ثم اضغط Raw وانسخ محتواه هنا، أو ارفع الملف مباشرة.

ما سأقوم به مباشرة بعد استلام الكود
لن نعيد كتابة المشروع، بل سنطوره على نفس الأساس الذي بنيته.

سأجري التعديلات التالية بالترتيب:

دمج Master Prompt كتعليمات نظام (System Instruction).

نقل البرومبت إلى ملف مستقل مثل prompt.py.

جعل البوت يرسل البرومبت مع كل طلب إلى Gemini بدلًا من إضافته داخل الكود بشكل عشوائي.

تجهيز البنية لاستقبال ملفات PDF وWord وصور اللوحات في المرحلة التالية.

تنظيم المشروع بحيث يكون سهل الصيانة والتطوير.

سنحافظ على كل ما يعمل حاليًا، ولن نكسر أي جزء من البوت إلا إذا كان هناك سبب تقني واضح.

أشعر أننا قريبون جدًا من الوصول إلى النسخة الأولى الاحترافية من البوت، وبعد دمج الـ Master Prompt سنبدأ بإضافة قدرات تحليل مشاريع التخرج والملفات الأكاديمية خطوة بخطوة.


from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error
import base64

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
TELEGRAM_GET_FILE_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile"
TELEGRAM_FILE_BASE = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/"
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


def get_telegram_file(file_id):
    url = f"{TELEGRAM_GET_FILE_API}?file_id={file_id}"
    with urllib.request.urlopen(url, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    file_path = data["result"]["file_path"]
    file_url = TELEGRAM_FILE_BASE + file_path
    with urllib.request.urlopen(file_url, timeout=30) as resp:
        file_bytes = resp.read()
    return file_bytes, file_path


def guess_mime_type(file_path):
    ext = file_path.lower().rsplit(".", 1)[-1] if "." in file_path else ""
    mapping = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt": "text/plain",
    }
    return mapping.get(ext, "application/octet-stream")


CONVERSATION_HISTORY = {}
MAX_HISTORY_MESSAGES = 10


def ask_gemini(chat_id, user_text, file_bytes=None, mime_type=None):
    history = CONVERSATION_HISTORY.get(chat_id, [])

    request_parts = []
    if file_bytes:
        request_parts.append({
            "inline_data": {
                "mime_type": mime_type,
                "data": base64.b64encode(file_bytes).decode("utf-8"),
            }
        })
    display_text = user_text or "حلل هذا الملف بإيجاز."
    request_parts.append({"text": display_text})

    request_contents = history + [{"role": "user", "parts": request_parts}]

    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_INSTRUCTION}]
        },
        "contents": request_contents
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
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        reply_text = data["candidates"][0]["content"]["parts"][0]["text"]
        history_note = display_text if not file_bytes else f"[أرسل المستخدم ملفاً] {display_text}"
        history.append({"role": "user", "parts": [{"text": history_note}]})
        history.append({"role": "model", "parts": [{"text": reply_text}]})
        CONVERSATION_HISTORY[chat_id] = history[-MAX_HISTORY_MESSAGES:]
        return reply_text
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
            text = message.get("text", "") or message.get("caption", "")
            document = message.get("document")
            photos = message.get("photo")

            file_bytes = None
            mime_type = None

            if chat_id and document:
                file_id = document.get("file_id")
                mime_type = document.get("mime_type") or "application/octet-stream"
                file_bytes, _ = get_telegram_file(file_id)
            elif chat_id and photos:
                file_id = photos[-1].get("file_id")
                file_bytes, file_path = get_telegram_file(file_id)
                mime_type = guess_mime_type(file_path)

            if chat_id and (text or file_bytes):
                reply = ask_gemini(chat_id, text, file_bytes=file_bytes, mime_type=mime_type)
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

ممتاز جدًا. راجعت الكود بالكامل.

أستطيع أن أقول إن الأساس الذي بنيته جيد، والبوت مرتب، ولا يحتاج إلى إعادة كتابة. نحتاج فقط إلى تطويره.

أولًا: تقييم سريع
نقاط القوة

✅ استخدام system_instruction بالطريقة الصحيحة مع Gemini.

✅ يدعم المحادثة المستمرة (Conversation History).

✅ يدعم PDF.

✅ يدعم الصور.

✅ يدعم DOCX.

✅ يعتمد على Webhook وليس Polling (أفضل للنشر).

هذا يعني أننا لن نبدأ من الصفر.

أول تعديل سأقوم به
لا تضع الـ Master Prompt داخل webhook.py
بدلاً من هذا السطر

SYSTEM_INSTRUCTION = """...."""
أنشئ ملفًا جديدًا

prompt.py
ثم ضع بداخله

SYSTEM_INSTRUCTION = """
ضع هنا Master Prompt بالكامل...
"""
ثم داخل

webhook.py
استبدل

SYSTEM_INSTRUCTION = ...
بـ

from prompt import SYSTEM_INSTRUCTION
لماذا؟
لأن وثيقة التخصص لن تبقى 200 سطر.

ستصبح لاحقًا

1000

3000

وربما 10000 سطر

ولو بقيت داخل webhook.py سيصبح الملف غير قابل للصيانة.

ثاني تعديل
لاحظ هنا

MAX_HISTORY_MESSAGES = 10
اجعلها

MAX_HISTORY_MESSAGES = 20
لأن تقييم مشروع تخرج طويل.

ثالث تعديل
أضف هذا الثابت

MAX_RESPONSE_TOKENS = 4096
ثم داخل

payload

اجعل

payload = {
    "system_instruction": {
        "parts": [{"text": SYSTEM_INSTRUCTION}]
    },
    "contents": request_contents,
    "generationConfig": {
        "temperature": 0.3,
        "topP": 0.9,
        "topK": 40,
        "maxOutputTokens": MAX_RESPONSE_TOKENS
    }
}
السبب

أنت لا تريد Gemini أن يكون مبدعًا.

أنت تريده

دقيقًا

صارمًا

أكاديميًا

ولهذا

Temperature = 0.3

أفضل بكثير.

رابع تعديل
قبل

reply = ask_gemini(...)
أضف

send_telegram_message(chat_id, "📄 جاري تحليل المشروع...")
حتى يشعر المستخدم أن البوت يعمل.

خامس تعديل
هذه أهم نقطة.

بدلاً من

CONVERSATION_HISTORY = {}
سنحولها في المرحلة القادمة إلى

SQLite

وليس RAM

حتى إذا أُعيد تشغيل Replit

لا تضيع المحادثات.

سادس تعديل (مهم جدًا)
أضف حماية لحجم الملفات.

مثلاً

MAX_FILE_SIZE = 20 * 1024 * 1024
وقبل إرسال الملف إلى Gemini

افحص

if len(file_bytes) > MAX_FILE_SIZE:
    send_telegram_message(
        chat_id,
        "الملف كبير جداً، الرجاء إرسال ملف أصغر من 20MB."
    )
    return
المرحلة التالية
بعد اعتماد هذه التعديلات، سأحول هذا البوت من مجرد بوت أسئلة وأجوبة إلى مراجع أكاديمي ذكي.

سنضيف قدرات مثل:

تحليل مشروع التخرج بالكامل.

استخراج عنوان المشروع تلقائيًا.

تقييم الفكرة وفق الـ Rubric.

إعطاء درجة لكل محور.

كتابة تقرير PDF كامل بالتقييم.

مقارنة ثلاثة مشاريع واختيار الأفضل.

حفظ جميع تقييمات الطلاب في قاعدة بيانات يمكن الرجوع إليها لاحقًا.

برأيي، خلال بضع مراحل إضافية سيكون لديك نظام احترافي يمكن الاعتماد عليه في تقييم مشاريع التخرج، وليس مجرد بوت دردشة.


اعتمد هذه التعديلات واعطني الملف مباشره حتي الصقه في التعديلات

ممتاز. هذه التعديلات آمنة ولن تؤثر على عمل البوت، لذلك أعتمدها.

انسخ الملف التالي بالكامل واستبدل به محتوى api/webhook.py.

from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error
import base64

from prompt import SYSTEM_INSTRUCTION

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
TELEGRAM_GET_FILE_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile"
TELEGRAM_FILE_BASE = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/"
GEMINI_API = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"

MAX_HISTORY_MESSAGES = 20
MAX_RESPONSE_TOKENS = 4096
MAX_FILE_SIZE = 20 * 1024 * 1024

CONVERSATION_HISTORY = {}


def get_telegram_file(file_id):
    url = f"{TELEGRAM_GET_FILE_API}?file_id={file_id}"

    with urllib.request.urlopen(url, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    file_path = data["result"]["file_path"]
    file_url = TELEGRAM_FILE_BASE + file_path

    with urllib.request.urlopen(file_url, timeout=30) as resp:
        file_bytes = resp.read()

    return file_bytes, file_path


def guess_mime_type(file_path):
    ext = file_path.lower().rsplit(".", 1)[-1] if "." in file_path else ""

    mapping = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt": "text/plain",
    }

    return mapping.get(ext, "application/octet-stream")


def ask_gemini(chat_id, user_text, file_bytes=None, mime_type=None):
    history = CONVERSATION_HISTORY.get(chat_id, [])

    request_parts = []

    if file_bytes:
        request_parts.append({
            "inline_data": {
                "mime_type": mime_type,
                "data": base64.b64encode(file_bytes).decode("utf-8"),
            }
        })

    display_text = user_text or "حلل هذا الملف بصورة أكاديمية."

    request_parts.append({
        "text": display_text
    })

    request_contents = history + [{
        "role": "user",
        "parts": request_parts
    }]

    payload = {
        "system_instruction": {
            "parts": [
                {
                    "text": SYSTEM_INSTRUCTION
                }
            ]
        },
        "contents": request_contents,
        "generationConfig": {
            "temperature": 0.3,
            "topP": 0.9,
            "topK": 40,
            "maxOutputTokens": MAX_RESPONSE_TOKENS
        }
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
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        reply_text = data["candidates"][0]["content"]["parts"][0]["text"]

        history_note = (
            display_text
            if not file_bytes
            else f"[أرسل المستخدم ملفاً] {display_text}"
        )

        history.append({
            "role": "user",
            "parts": [{"text": history_note}]
        })

        history.append({
            "role": "model",
            "parts": [{"text": reply_text}]
        })

        CONVERSATION_HISTORY[chat_id] = history[-MAX_HISTORY_MESSAGES:]

        return reply_text

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        return f"خطأ HTTP {e.code}: {error_body}"

    except Exception as e:
        return f"حدث خطأ أثناء الاتصال بـ Gemini:\n{e}"


def send_telegram_message(chat_id, text):
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    req = urllib.request.Request(
        TELEGRAM_API,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json"
        },
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

            text = message.get("text", "") or message.get("caption", "")

            document = message.get("document")

            photos = message.get("photo")

            file_bytes = None
            mime_type = None

            if chat_id and document:

                file_id = document.get("file_id")

                mime_type = document.get("mime_type") or "application/octet-stream"

                file_bytes, _ = get_telegram_file(file_id)

            elif chat_id and photos:

                file_id = photos[-1].get("file_id")

                file_bytes, file_path = get_telegram_file(file_id)

                mime_type = guess_mime_type(file_path)

            if file_bytes and len(file_bytes) > MAX_FILE_SIZE:

                send_telegram_message(
                    chat_id,
                    "❌ حجم الملف يتجاوز 20MB.\nيرجى إرسال ملف أصغر."
                )

            elif chat_id and (text or file_bytes):

                send_telegram_message(
                    chat_id,
                    "📄 جاري تحليل المشروع..."
                )

                reply = ask_gemini(
                    chat_id,
                    text,
                    file_bytes=file_bytes,
                    mime_type=mime_type
                )

                send_telegram_message(chat_id, reply)

        except Exception:
            pass

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        self.wfile.write(
            json.dumps({"ok": True}).encode("utf-8")
        )

    def do_GET(self):

        self.send_response(200)

        self.send_header("Content-Type", "text/plain")

        self.end_headers()

        tg_status = (
            f"SET (starts with {TELEGRAM_TOKEN[:6]})"
            if TELEGRAM_TOKEN
            else "MISSING"
        )

        gm_status = (
            f"SET (starts with {GEMINI_KEY[:6]})"
            if GEMINI_KEY
            else "MISSING"
        )

        debug_text = (
            "Bot webhook is running.\n"
            f"TELEGRAM_BOT_TOKEN: {tg_status}\n"
            f"GEMINI_API_KEY: {gm_status}"
        )

        self.wfile.write(debug_text.encode("utf-8"))
أنشئ أيضًا ملفًا جديدًا باسم:
pr

