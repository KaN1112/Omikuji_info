from flask import Flask, request, render_template
import requests
import os
import json
import time

TOKEN = os.getenv("DISCORD_TOKEN")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

CHANNELS_FILE = "channels.json"
SYNC_STATUS_FILE = "sync_status.json"
SYNC_COOLDOWN = 30 * 60

app = Flask(__name__)

HEADERS = {
    "Authorization": f"Bot {TOKEN}"
}

def load_channels():
    if not os.path.exists(CHANNELS_FILE):
        return []

    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_channels(channels):
    with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
        json.dump(channels, f, ensure_ascii=False, indent=4)

def load_sync_status():
    if not os.path.exists(SYNC_STATUS_FILE):
        return {"last_sync": 0}

    with open(SYNC_STATUS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_sync_status():
    with open(SYNC_STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_sync": int(time.time())}, f, ensure_ascii=False, indent=4)

def can_sync():
    status = load_sync_status()
    last_sync = status.get("last_sync", 0)
    now = int(time.time())

    remaining = SYNC_COOLDOWN - (now - last_sync)

    if remaining > 0:
        minutes = remaining // 60
        seconds = remaining % 60
        return False, f"同期は30分に1回までです。あと{minutes}分{seconds}秒待ってください。"

    return True, ""

def sync_channels():
    channels_list = []

    guilds_res = requests.get(
        "https://discord.com/api/v10/users/@me/guilds",
        headers=HEADERS
    )

    if guilds_res.status_code != 200:
        return False, f"サーバー取得失敗: {guilds_res.status_code} / {guilds_res.text}"

    guilds = guilds_res.json()

    for guild in guilds:
        guild_id = guild["id"]
        guild_name = guild["name"]

        channels_res = requests.get(
            f"https://discord.com/api/v10/guilds/{guild_id}/channels",
            headers=HEADERS
        )

        if channels_res.status_code != 200:
            continue

        for ch in channels_res.json():
            if ch.get("type") == 0:
                channels_list.append({
                    "guild_name": guild_name,
                    "channel_name": ch["name"],
                    "channel_id": ch["id"]
                })

    save_channels(channels_list)
    save_sync_status()

    return True, f"{len(channels_list)}件のチャンネルを同期しました"

@app.route("/")
def home():
    channels = load_channels()
    return render_template("index.html", channels=channels, message=None)

@app.route("/sync", methods=["POST"])
def sync():
    password = request.form.get("password")

    if password != ADMIN_PASSWORD:
        return render_template(
            "index.html",
            channels=load_channels(),
            message="パスワードが違います"
        )

    allowed, wait_message = can_sync()

    if not allowed:
        return render_template(
            "index.html",
            channels=load_channels(),
            message=wait_message
        )

    success, msg = sync_channels()

    return render_template(
        "index.html",
        channels=load_channels(),
        message=msg
    )

@app.route("/send", methods=["POST"])
def send_message():
    password = request.form.get("password")

    if password != ADMIN_PASSWORD:
        return render_template(
            "index.html",
            channels=load_channels(),
            message="パスワードが違います"
        )

    channel_id = request.form.get("channel_id")
    title = request.form.get("title") or "お知らせ"
    message = request.form.get("message")
    color = int(request.form.get("color"))
    image = request.files.get("image")

    if not channel_id:
        return render_template(
            "index.html",
            channels=load_channels(),
            message="チャンネルが選択されていません"
        )

    if not message:
        return render_template(
            "index.html",
            channels=load_channels(),
            message="本文が空です"
        )

    content = "@everyone" if request.form.get("everyone") else ""

    payload = {
        "content": content,
        "embeds": [
            {
                "title": title,
                "description": message,
                "color": color
            }
        ]
    }

    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"

    if image and image.filename:
        files = {
            "file": (image.filename, image.stream, image.mimetype)
        }

        data = {
            "payload_json": json.dumps(payload, ensure_ascii=False)
        }

        res = requests.post(
            url,
            headers=HEADERS,
            data=data,
            files=files
        )
    else:
        headers = {
            "Authorization": f"Bot {TOKEN}",
            "Content-Type": "application/json"
        }

        res = requests.post(
            url,
            headers=headers,
            json=payload
        )

    if res.status_code in [200, 201]:
        return render_template(
            "index.html",
            channels=load_channels(),
            message="送信しました！"
        )

    return render_template(
        "index.html",
        channels=load_channels(),
        message=f"送信失敗: {res.status_code} / {res.text}"
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
