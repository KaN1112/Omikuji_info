from flask import Flask, request, render_template, redirect
import requests
import os
import json

TOKEN = os.getenv("DISCORD_TOKEN")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

CHANNELS_FILE = "channels.json"

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
    return True, f"{len(channels_list)}件のチャンネルを同期しました"

@app.route("/")
def home():
    channels = load_channels()
    return render_template("index.html", channels=channels, message=None)

@app.route("/sync", methods=["POST"])
def sync():
    password = request.form.get("password")

    if password != ADMIN_PASSWORD:
        channels = load_channels()
        return render_template("index.html", channels=channels, message="パスワードが違います")

    success, msg = sync_channels()
    channels = load_channels()

    return render_template("index.html", channels=channels, message=msg)

@app.route("/send", methods=["POST"])
def send_message():
    password = request.form.get("password")

    if password != ADMIN_PASSWORD:
        channels = load_channels()
        return render_template("index.html", channels=channels, message="パスワードが違います")

    channel_id = request.form.get("channel_id")
    title = request.form.get("title") or "お知らせ"
    message = request.form.get("message")
    color = int(request.form.get("color"))
    image = request.files.get("image")

    if not channel_id:
        channels = load_channels()
        return render_template("index.html", channels=channels, message="チャンネルが選択されていません")

    if not message:
        channels = load_channels()
        return render_template("index.html", channels=channels, message="本文が空です")

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

    channels = load_channels()

    if res.status_code in [200, 201]:
        return render_template("index.html", channels=channels, message="送信しました！")

    return render_template(
        "index.html",
        channels=channels,
        message=f"送信失敗: {res.status_code} / {res.text}"
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
