import discord
from discord.ext import tasks

import sys
import os
from os.path import join, dirname
from dotenv import load_dotenv

import requests
import json

from datetime import datetime

# .envファイルを読み込む
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

intent = discord.Intents.default()
intent.message_content = True
client = discord.Client(intents=intent)

# 環境変数を取得
server_id = int(os.getenv('GUILD_ID'))
channel_id = int(os.getenv('CHANNEL_ID'))
token = os.getenv('TOKEN')

# 天気予報の地域コード
tokushima_code = 360000
hyogo_code = 280000
tokushima_north_code = 360010
hyogo_south_code = 280010
tokushima_city_code = 71106
kobe_city_code = 63518


@client.event
async def on_ready():
    loop.start()
    await weather_notify()
    print("Get on ready!")

# 天気予報を取得する関数
def get_weather(pref_code: int, area_code: int, local_code: int = 0):
    weather_url=f'http://www.jma.go.jp/bosai/forecast/data/forecast/{str(pref_code)}.json'
    weather_json = requests.get(weather_url).json()
    weather = ""
    temp={0, 0}
    # 該当地域の天気予報を取得
    for weather_area in weather_json[0]["timeSeries"][0]["areas"]:
        if int(weather_area["area"]["code"]) == area_code:
                weather = str(weather_area["weathers"][0]).replace("\u3000", "")
    # 該当地域の予想最高気温を取得
    for temp_area in weather_json[0]["timeSeries"][2]["areas"]:
        if int(temp_area["area"]["code"]) == local_code:
                temp = temp_area["temps"][0]
    # 該当地域の日中予想降水確率を取得
    for pops_area in weather_json[0]["timeSeries"][1]["areas"]:
        if int(pops_area["area"]["code"]) == area_code:
            pops = {pops_area["pops"][0], pops_area["pops"][1], pops_area["pops"][2]}
            pop_sum = 0
            for pop in pops:
                 pop_sum += int(pop)
        pop_avg = pop_sum / 3   # 30時間分の降水確率の平均値を取得

    return weather, temp, int(pop_avg)

# 天気予報を通知する関数
async def weather_notify():
    channel = client.get_channel(channel_id)
    tokushima_weather, tokushima_temp, tokushima_pop = get_weather(tokushima_code, tokushima_north_code, tokushima_city_code)
    hyogo_weather, hyogo_temp, hyogo_pop = get_weather(hyogo_code, hyogo_south_code, kobe_city_code)
    # 天気予報を埋め込みメッセージで通知
    embed = discord.Embed(title="本日の天気予報",
                    url="https://www.jma.go.jp/bosai/#pattern=forecast",
                    colour=0x00b0f4,
                    timestamp=datetime.now())
    embed.add_field(name="徳島",
                    value=f"> 天気予報: {tokushima_weather}\n> 最高気温: {tokushima_temp} ℃\n> 降水確率: {tokushima_pop} %",
                    inline=True)
    embed.add_field(name="兵庫",
                    value=f"> 天気予報: {hyogo_weather}\n> 最高気温: {hyogo_temp} ℃\n> 降水確率: {hyogo_pop} %",
                    inline=True)
    await channel.send(embed=embed)


# 毎日6時に天気予報を通知する
@tasks.loop(seconds=60)
async def loop():
    if datetime.now().strftime('%H:%M') == '06:00':
        await weather_notify()

client.run(token)
