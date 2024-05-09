import discord
from discord.ext import tasks

import sys
import os
from os.path import join, dirname
from dotenv import load_dotenv

import requests
import json

from datetime import datetime

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

intent = discord.Intents.default()
intent.message_content = True
client = discord.Client(intents=intent)

server_id = int(os.getenv('GUILD_ID'))
channel_id = int(os.getenv('CHANNEL_ID'))
token = os.getenv('TOKEN')

tokushima_code = 360000
hyogo_code = 280000
tokushima_north_code = 360010
hyogo_south_code = 280010

@client.event
async def on_ready():
    loop.start()
    await weather_notify()
    print("Get on ready!")

# 天気予報を取得する関数
def get_weather(pref_code: int, area_code: int):
    weather_url=f'http://www.jma.go.jp/bosai/forecast/data/forecast/{str(pref_code)}.json'
    weather_json = requests.get(weather_url).json()
    for weather_area in weather_json[0]["timeSeries"][0]["areas"]:
        if int(weather_area["area"]["code"]) == area_code:
                weather = str(weather_area["weathers"][0]).replace("\u3000", "")
    return weather

# 天気予報を通知する関数
async def weather_notify():
    channel = client.get_channel(channel_id)
    tokushima_weather = get_weather(tokushima_code, tokushima_north_code)
    hyogo_weather = get_weather(hyogo_code, hyogo_south_code)
    send_message = f"# {datetime.now().strftime('%Y/%m/%d')}\n## 徳島北部の天気\n> ## {tokushima_weather}\n## 兵庫南部の天気\n> ## {hyogo_weather}"
    await channel.send(send_message)


# 毎日6時に天気予報を通知する
@tasks.loop(seconds=60)
async def loop():
    now = datetime.now().strftime('%H:%M')
    if now == '06:00':
        await weather_notify()

client.run(token)
