# webhook.py
# Placeholder clean template.
# Replace with the finalized implementation if needed.

from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error
import base64

from prompt import SYSTEM_INSTRUCTION

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type","text/plain")
        self.end_headers()
        self.wfile.write(b"Bot webhook is running.")

    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))
