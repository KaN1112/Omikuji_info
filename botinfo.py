from flask import Flask, request, render_template
import requests
import os

TOKEN = os.getenv("DISCORD_TOKEN")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

app = Flask(__name__)

HEADERS = {
    "Authorization": f"Bot {TOKEN}",
    "Content-Type": "application/json"
}

def get_channels():
    channels_list = []

    guilds_res = requests.get(
        "https://discord.com/api/v10/users/@me/guilds",
        headers=HEADERS
    )

    if guilds_res.status_code != 200:
        return []

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

        channels = channels_res.json()

        for ch in channels:
            if ch.get("type") == 0:
                channels_list.append({
                    "guild_name": guild_name,
                    "channel_name": ch["name"],
                    "channel_id": ch["id"]
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

    if not channel_id:
        return "チャンネルが選択されていません"

    if not message:
        return "本文が空です"

    content = "@everyone" if request.form.get("everyone") else ""

    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"

    data = {
        "content": content,
        "embeds": [
            {
                "title": title,
                "description": message,
                "color": color
            }
        ]
    }

    res = requests.post(url, headers=HEADERS, json=data)

    if res.status_code in [200, 201]:
        return "送信しました！"

    return f"送信失敗: {res.status_code}<br>{res.text}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
