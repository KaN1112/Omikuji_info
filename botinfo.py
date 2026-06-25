import discord
from discord.ext import commands
from flask import Flask, request, redirect
from threading import Thread
import os
import asyncio

TOKEN = os.getenv("DISCORD_TOKEN")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

intents = discord.Intents.default()
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

app = Flask(__name__)

def make_html():
    options = ""
    for guild in bot.guilds:
        for channel in guild.text_channels:
            options += f'<option value="{channel.id}">{guild.name} / #{channel.name}</option>'

    return f"""
    <h2>📢 Bot運用お知らせ</h2>
    <form method="POST" action="/send">
        <input type="password" name="password" placeholder="パスワード"><br><br>

        <label>送信先チャンネル</label><br>
        <select name="channel_id">
            {options}
        </select><br><br>

        <label>タイトル</label><br>
        <input type="text" name="title" placeholder="例：メンテナンスのお知らせ"><br><br>

        <label>本文</label><br>
        <textarea name="message" rows="8" cols="50"></textarea><br><br>

        <label>色</label><br>
        <select name="color">
            <option value="blue">青</option>
            <option value="red">赤</option>
            <option value="green">緑</option>
            <option value="yellow">黄</option>
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
    if not bot.is_ready():
        return "Bot起動中です。少し待ってから更新してください。"
    return make_html()

@app.route("/send", methods=["POST"])
def send_message():
    password = request.form.get("password")
    if password != ADMIN_PASSWORD:
        return "パスワードが違います"

    channel_id = int(request.form.get("channel_id"))
    title = request.form.get("title") or "お知らせ"
    message = request.form.get("message")
    color_name = request.form.get("color")
    everyone = request.form.get("everyone")

    colors = {
        "blue": 0x3498db,
        "red": 0xe74c3c,
        "green": 0x2ecc71,
        "yellow": 0xf1c40f
    }

    async def send_to_discord():
        channel = bot.get_channel(channel_id)
        embed = discord.Embed(
            title=title,
            description=message,
            color=colors.get(color_name, 0x3498db)
        )

        content = "@everyone" if everyone else None
        await channel.send(content=content, embed=embed)

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
