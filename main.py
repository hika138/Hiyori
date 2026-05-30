import os
from os.path import join, dirname
from dotenv import load_dotenv
import discord
from discord.ext import commands

# .envファイルを読み込む
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# 環境変数を取得
token = os.getenv('TOKEN')
if token is None:
    raise ValueError("TOKEN environment variable is not set.")

# DiscordのBotを作成
intent = discord.Intents.default()
intent.message_content = True
bot = commands.Bot(command_prefix="!", intents=intent)

@bot.event
async def setup_hook():
    await bot.load_extension("cogs.weather")


@bot.event
async def on_ready():
    print("Get on Ready!")


bot.run(token)