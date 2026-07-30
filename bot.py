import requests
import time
import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("PORT", 10000))

class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *a):
        pass

def run_http():
    s = HTTPServer(("0.0.0.0", PORT), HealthCheck)
    s.serve_forever()

threading.Thread(target=run_http, daemon=True).start()

TOKEN = os.environ.get("BOT_TOKEN", "8493905380:AAFI-9I1_SfXCWWEJmfcP_CmKazkVmNbsrI")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8651166378"))
PROXY = os.environ.get("BOT_PROXY", "")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "-1004429697205")

API = f"https://api.telegram.org/bot{TOKEN}"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "settings_db.json")

proxies = None
if PROXY:
    proxies = {"http": PROXY, "https": PROXY}

if os.path.exists(DB_FILE):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        settings = json.load(f)
else:
    settings = {"photo_id": None}

def save_settings():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def api(method, data=None, files=None, retries=5):
    for attempt in range(retries):
        try:
            r = requests.post(f"{API}/{method}", data=data, files=files, proxies=proxies, timeout=120)
            return r.json()
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3)
            else:
                print(f"Error {method}: {e}", flush=True)
                return None

keyboard = {
    "inline_keyboard": [
        [
            {"text": "Solara", "callback_data": "solara"},
            {"text": "Xeno", "callback_data": "xeno"}
        ]
    ]
}

print("Бот запущен!", flush=True)
last_offset = 0

while True:
    try:
        r = requests.get(f"{API}/getUpdates", params={"offset": last_offset + 1, "timeout": 30}, proxies=proxies, timeout=35)
        data = r.json()
        if not data.get("ok"):
            time.sleep(1)
            continue

        for update in data["result"]:
            last_offset = update["update_id"]

            if "message" in update:
                m = update["message"]
                chat_id = m["chat"]["id"]
                text = m.get("text", "")

                if text == "/start":
                    photo_id = settings.get("photo_id")
                    if photo_id:
                        api("sendPhoto", {"chat_id": chat_id, "photo": photo_id, "caption": "Выбери чит:", "reply_markup": json.dumps(keyboard)})
                    else:
                        api("sendMessage", {"chat_id": chat_id, "text": "Выбери чит:", "reply_markup": json.dumps(keyboard)})

                if chat_id == ADMIN_ID and "photo" in m:
                    settings["photo_id"] = m["photo"][-1]["file_id"]
                    save_settings()
                    api("sendMessage", {"chat_id": chat_id, "text": "Фото сохранено."})

            elif "callback_query" in update:
                cb = update["callback_query"]
                chat_id = cb["message"]["chat"]["id"]
                api("answerCallbackQuery", {"callback_query_id": cb["id"]})

                msg_id = 2 if cb["data"] == "solara" else 3
                result = api("copyMessage", {
                    "chat_id": chat_id,
                    "from_chat_id": CHANNEL_ID,
                    "message_id": msg_id
                })
                if not result or not result.get("ok"):
                    api("sendMessage", {"chat_id": chat_id, "text": "Ошибка доступа к файлу."})

    except Exception as e:
        print(f"Polling error: {e}", flush=True)
        time.sleep(5)
