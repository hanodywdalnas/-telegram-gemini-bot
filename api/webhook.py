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


GEMINI_API = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-flash-latest:generateContent"
)


CONVERSATION_HISTORY = {}

MAX_HISTORY_MESSAGES = 10



def get_telegram_file(file_id):

    url = f"{TELEGRAM_GET_FILE_API}?file_id={file_id}"

    with urllib.request.urlopen(url, timeout=20) as resp:
        data = json.loads(
            resp.read().decode("utf-8")
        )


    file_path = data["result"]["file_path"]


    file_url = TELEGRAM_FILE_BASE + file_path


    with urllib.request.urlopen(file_url, timeout=30) as resp:
        file_bytes = resp.read()


    return file_bytes, file_path



def guess_mime_type(file_path):

    ext = (
        file_path.lower().rsplit(".", 1)[-1]
        if "." in file_path
        else ""
    )


    mapping = {

        "pdf": "application/pdf",

        "jpg": "image/jpeg",

        "jpeg": "image/jpeg",

        "png": "image/png",

        "webp": "image/webp",

        "docx":
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",

        "txt": "text/plain",

    }


    return mapping.get(
        ext,
        "application/octet-stream"
    )



def ask_gemini(chat_id, user_text, file_bytes=None, mime_type=None):

    history = CONVERSATION_HISTORY.get(
        chat_id,
        []
    )


    request_parts = []


    if file_bytes:

        request_parts.append(
            {
                "inline_data": {

                    "mime_type": mime_type,

                    "data": base64.b64encode(
                        file_bytes
                    ).decode("utf-8")

                }
            }
        )


    request_parts.append(
        {
            "text":
            user_text or "حلل هذا الملف أكاديمياً."
        }
    )


    request_contents = history + [

        {

            "role": "user",

            "parts": request_parts

        }

    ]    payload = {

        "system_instruction": {

            "parts": [

                {

                    "text": SYSTEM_INSTRUCTION

                }

            ]

        },


        "contents": request_contents

    }



    req = urllib.request.Request(

        GEMINI_API,

        data=json.dumps(payload).encode("utf-8"),

        headers={

            "Content-Type": "application/json",

            "x-goog-api-key": GEMINI_KEY

        },

        method="POST"

    )



    try:

        with urllib.request.urlopen(req, timeout=90) as resp:

            data = json.loads(
                resp.read().decode("utf-8")
            )


        reply_text = (

            data["candidates"][0]
            ["content"]["parts"][0]["text"]

        )


        history.append(

            {

                "role": "user",

                "parts": [

                    {

                        "text": user_text

                    }

                ]

            }

        )


        history.append(

            {

                "role": "model",

                "parts": [

                    {

                        "text": reply_text

                    }

                ]

            }

        )


        CONVERSATION_HISTORY[chat_id] = (
            history[-MAX_HISTORY_MESSAGES:]
        )


        return reply_text



    except urllib.error.HTTPError as e:


        error_body = e.read().decode("utf-8")


        return f"خطأ HTTP {e.code}: {error_body}"



    except Exception as e:


        return f"حدث خطأ أثناء الاتصال بـ Gemini: {e}"




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

        method="POST"

    )



    with urllib.request.urlopen(req, timeout=20) as resp:

        resp.read()class handler(BaseHTTPRequestHandler):


    def do_POST(self):

        content_length = int(
            self.headers.get(
                "Content-Length",
                0
            )
        )


        body = self.rfile.read(
            content_length
        )


        try:

            update = json.loads(body)


            message = update.get(
                "message",
                {}
            )


            chat_id = (
                message
                .get("chat", {})
                .get("id")
            )


            text = (
                message.get("text", "")
                or message.get("caption", "")
            )


            document = message.get(
                "document"
            )


            photos = message.get(
                "photo"
            )


            file_bytes = None

            mime_type = None



            if chat_id and document:


                file_id = document.get(
                    "file_id"
                )


                file_bytes, file_path = get_telegram_file(
                    file_id
                )


                mime_type = (
                    document.get(
                        "mime_type"
                    )
                    or guess_mime_type(
                        file_path
                    )
                )



            elif chat_id and photos:


                file_id = photos[-1].get(
                    "file_id"
                )


                file_bytes, file_path = get_telegram_file(
                    file_id
                )


                mime_type = guess_mime_type(
                    file_path
                )



            if chat_id and (
                text or file_bytes
            ):


                send_telegram_message(

                    chat_id,

                    "📄 جاري تحليل الطلب..."

                )


                reply = ask_gemini(

                    chat_id,

                    text,

                    file_bytes=file_bytes,

                    mime_type=mime_type

                )


                send_telegram_message(

                    chat_id,

                    reply

                )



        except Exception:

            pass



        self.send_response(
            200
        )


        self.send_header(
            "Content-Type",
            "application/json"
        )


        self.end_headers()


        self.wfile.write(

            json.dumps(
                {
                    "ok": True
                }
            ).encode("utf-8")

        )




    def do_GET(self):

        self.send_response(
            200
        )


        self.send_header(
            "Content-Type",
            "text/plain"
        )


        self.end_headers()


        tg_status = (

            "SET"

            if TELEGRAM_TOKEN

            else "MISSING"

        )


        gm_status = (

            "SET"

            if GEMINI_KEY

            else "MISSING"

        )


        response = (

            "Bot webhook is running.\n"

            f"TELEGRAM_BOT_TOKEN: {tg_status}\n"

            f"GEMINI_API_KEY: {gm_status}"

        )


        self.wfile.write(
            response.encode("utf-8")
        )
