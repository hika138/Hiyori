import discord
from discord.ext import tasks
import os
from os.path import join, dirname
from dotenv import load_dotenv
import aiohttp
from datetime import datetime

# .envファイルを読み込む
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# 環境変数を取得
channel_id = int(os.getenv('CHANNEL_ID'))
token = os.getenv('TOKEN')

# Discordのクライアントを作成
intent = discord.Intents.default()
intent.message_content = True
client = discord.Client(intents=intent)

# 天気予報の地域コード
tokushima_code = 360000
hyogo_code = 280000

tokushima_north_code = 360010
hyogo_south_code = 280010

tokushima_city_code = 71106
kobe_city_code = 63518

# 天気予報の地域クラス
class Area:
    def __init__(self, pref_code, area_code, local_code):
        self.pref_code = pref_code
        self.area_code = area_code
        self.local_code = local_code

        self.weather = ""
        self.temp = {0, 0}
        self.pop = 0

    # 天気予報を取得するメソッド
    async def update_weather(self, day:int=0):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://www.jma.go.jp/bosai/forecast/data/forecast/{str(self.pref_code)}.json') as response:
                weather_json = await response.json()
        
        # 該当地域の天気予報を取得
        for weather_area in weather_json[0]["timeSeries"][0]["areas"]:
            if int(weather_area["area"]["code"]) == self.area_code:
                self.weather = str(weather_area["weathers"][day]).replace("\u3000", "")
        # 該当地域の予想最高気温を取得
        for temp_area in weather_json[0]["timeSeries"][2]["areas"]:
            if int(temp_area["area"]["code"]) == self.local_code:
                    self.temp = temp_area["temps"][day]
        # 該当地域の日中予想降水確率を取得
        for pops_area in weather_json[0]["timeSeries"][1]["areas"]:
            if int(pops_area["area"]["code"]) == self.area_code:
                if day == 0:    # 当日の降水確率の平均値
                    pops = {pops_area["pops"][0], pops_area["pops"][1], pops_area["pops"][2]}
                elif day == 1:  # 翌日の降水確率の平均値
                    pops = {pops_area["pops"][2], pops_area["pops"][3], pops_area["pops"][4]}
                else:           # それ以外を指定した場合は当日の降水確率の平均値
                    pops = {pops_area["pops"][0], pops_area["pops"][1], pops_area["pops"][2]}
                pop_sum = 0
                for pop in pops:
                     pop_sum += int(pop)
            self.pop = round(pop_sum / len(pops), 1)   # 降水確率の平均値を取得

tokushima = Area(tokushima_code, tokushima_north_code, tokushima_city_code)
hyogo = Area(hyogo_code, hyogo_south_code, kobe_city_code)

# 天気予報を通知する関数
async def weather_notify(tokushima:Area, hyogo:Area, day: int = 0):
    # 通知するチャンネルを取得
    channel = client.get_channel(channel_id) 
    tokushima.update_weather(day)
    hyogo.update_weather(day)

    # 天気予報を埋め込みメッセージで通知
    embed = discord.Embed()
    if day == 0:
        embed = discord.Embed(title="本日の天気予報",
                        url="https://www.jma.go.jp/bosai/#pattern=forecast",
                        colour=0x00b0f4,
                        timestamp=datetime.now())
    elif day == 1:
        embed = discord.Embed(title="明日の天気予報",
                        url="https://www.jma.go.jp/bosai/#pattern=forecast",
                        colour=0x00b0f4,
                        timestamp=datetime.now())
    embed.add_field(name="徳島",
                    value=f"> 天気予報: {tokushima.weather}\n> 最高気温: {tokushima.temp} ℃\n> 降水確率: {tokushima.pop} %",
                    inline=True)
    embed.add_field(name="兵庫",
                    value=f"> 天気予報: {hyogo.weather}\n> 最高気温: {hyogo.temp} ℃\n> 降水確率: {hyogo.pop} %",
                    inline=True)
    embed.set_footer(text="気象庁提供")
    await channel.send(embed=embed)

@client.event
async def on_ready():
    loop.start()
    print("Get on ready!")

# 毎日6時に天気予報を通知する
@tasks.loop(seconds=60)
async def loop():
    now = datetime.now().strftime('%H:%M')
    if now == '06:00':
        await weather_notify(tokushima, hyogo, 0)
    elif now == '18:00':
        await weather_notify(tokushima, hyogo, 1)
client.run(token)
