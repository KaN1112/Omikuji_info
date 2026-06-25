from flask import Flask, request, redirect
import requests
import os

TOKEN = os.getenv("DISCORD_TOKEN")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

app = Flask(__name__)

HTML = """
<h2>📢 Bot運用お知らせ</h2>

<form method="POST" action="/send">
    <input type="password" name="password" placeholder="パスワード"><br><br>

    <label>送信先チャンネルID</label><br>
    <input type="text" name="channel_id" placeholder="例：123456789012345678"><br><br>

    <label>タイトル</label><br>
    <input type="text" name="title" placeholder="例：メンテナンスのお知らせ"><br><br>

    <label>本文</label><br>
    <textarea name="message" rows="8" cols="50"></textarea><br><br>

    <label>色</label><br>
    <select name="color">
        <option value="3447003">青</option>
        <option value="15158332">赤</option>
        <option value="3066993">緑</option>
        <option value="16776960">黄</option>
    </select><br><br>

    <label>
        <input type="checkbox" name="everyone">
        @everyone を付ける
    </label><br><br>

    <button type="submit">送信</button>
</form>
"""

@app.route("/")
def home():
    return HTML

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
