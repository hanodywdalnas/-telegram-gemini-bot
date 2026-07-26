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
