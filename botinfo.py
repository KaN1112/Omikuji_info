from flask import Flask, request, render_template
import requests
import os
import json

TOKEN = os.getenv("DISCORD_TOKEN")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

app = Flask(__name__)

HEADERS = {
    "Authorization": f"Bot {TOKEN}"
}

def get_channels():
    channels_list = []

    guilds_res = requests.get(
        "https://discord.com/api/v10/users/@me/guilds",
        headers=HEADERS
    )

    if guilds_res.status_code != 200:
        return [{
            "guild_name": "ERROR",
            "channel_name": f"guilds取得失敗 {guilds_res.status_code}",
            "channel_id": ""
        }]

    guilds = guilds_res.json()

    if not guilds:
        return [{
            "guild_name": "ERROR",
            "channel_name": "Botがサーバーに参加していません",
            "channel_id": ""
        }]

    for guild in guilds:
        guild_id = guild["id"]
        guild_name = guild["name"]

        channels_res = requests.get(
            f"https://discord.com/api/v10/guilds/{guild_id}/channels",
            headers=HEADERS
        )

        if channels_res.status_code != 200:
            channels_list.append({
                "guild_name": guild_name,
                "channel_name": f"channels取得失敗 {channels_res.status_code}",
                "channel_id": ""
            })
            continue

        channels = channels_res.json()

        for ch in channels:
            if ch.get("type") == 0:
                channels_list.append({
                    "guild_name": guild_name,
                    "channel_name": ch["name"],
                    "channel_id": ch["id"]
                })

    if not channels_list:
        channels_list.append({
            "guild_name": "ERROR",
            "channel_name": "表示できるテキストチャンネルがありません",
            "channel_id": ""
        })

    return channels_list

@app.route("/")
def home():
    channels = get_channels()
    return render_template("index.html", channels=channels)

@app.route("/send", methods=["POST"])
def send_message():
    password = request.form.get("password")

    if password != ADMIN_PASSWORD:
        return "パスワードが違います"

    channel_id = request.form.get("channel_id")
    title = request.form.get("title") or "お知らせ"
    message = request.form.get("message")
    color = int(request.form.get("color"))
    image = request.files.get("image")

    if not channel_id:
        return "チャンネルが選択されていません"

    if not message:
        return "本文が空です"

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
        return "送信しました！"

    return f"送信失敗: {res.status_code}<br>{res.text}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
