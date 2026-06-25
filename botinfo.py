from flask import Flask, request, render_template
import requests
import os

TOKEN = os.getenv("DISCORD_TOKEN")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

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
        return "チャンネルIDが空です"

    if not message:
        return "本文が空です"

    content = "@everyone" if request.form.get("everyone") else ""

    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"

    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Content-Type": "application/json"
    }

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

    res = requests.post(url, headers=headers, json=data)

    if res.status_code in [200, 201]:
        return "送信しました！"

    return f"送信失敗: {res.status_code}<br>{res.text}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
