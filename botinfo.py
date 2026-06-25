import discord
from discord.ext import commands
from flask import Flask, request, render_template_string, redirect
from threading import Thread
import os
import asyncio

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("ANNOUNCE_CHANNEL_ID"))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

app = Flask(__name__)

HTML = """
<h2>Bot運用お知らせ送信</h2>
<form method="POST" action="/send">
  <input type="password" name="password" placeholder="パスワード"><br><br>
  <textarea name="message" rows="10" cols="50" placeholder="送信内容"></textarea><br><br>
  <button type="submit">Discordに送信</button>
</form>
"""

@app.route("/")
def home():
    return HTML

@app.route("/send", methods=["POST"])
def send_message():
    password = request.form.get("password")
    message = request.form.get("message")

    if password != ADMIN_PASSWORD:
        return "パスワードが違います"

    if not message:
        return "メッセージが空です"

    async def send_to_discord():
        channel = bot.get_channel(CHANNEL_ID)
        if channel is None:
            channel = await bot.fetch_channel(CHANNEL_ID)
        await channel.send(message)

    asyncio.run_coroutine_threadsafe(send_to_discord(), bot.loop)

    return redirect("/")

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

@bot.event
async def on_ready():
    print(f"ログイン成功: {bot.user}")

Thread(target=run_web).start()
bot.run(TOKEN)