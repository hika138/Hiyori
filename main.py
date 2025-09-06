import discord
from discord.ext import tasks
import os
from os.path import join, dirname
from dotenv import load_dotenv
import datetime
from typing import Literal
from typing import Optional
from Area import Area  # Areaクラスをインポート

# .envファイルを読み込む
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# 環境変数を取得
channel_id_str = os.getenv('CHANNEL_ID')
if channel_id_str is None:
    raise ValueError("CHANNEL_ID environment variable is not set.")
channel_id = int(channel_id_str)
notify_channel: Optional[discord.TextChannel] = None
token = os.getenv('TOKEN')

# Discordのクライアントを作成
intent = discord.Intents.default()
intent.message_content = True
client = discord.Client(intents=intent)

# Areaクラスのインスタンスを作成
tokushima: Area = Area(360000, 360010, 71106) # 徳島県
hyogo: Area = Area(280000, 280010, 63518)

@client.event
async def on_ready():
    global notify_channel
    channel = client.get_channel(channel_id)
    if isinstance(channel, discord.TextChannel):
        notify_channel = channel
    else:
        notify_channel = None
    today_forecast.start()
    tomorrow_forecast.start()
    print("Get on Ready!")

# 天気予報を通知する関数
async def forecast_notify(channel: discord.TextChannel, areas, day: Literal["今日", "明日"]):
    embed = discord.Embed(title=f"{day}の天気予報",
                          url="https://www.jma.go.jp/bosai/#pattern=forecast",
                          colour=0x00b0f4,
                          timestamp=datetime.datetime.now()
                        )
    for area in areas:
        # 天気予報を取得
        await area.get_forecast(day) 
        # 埋め込みを作成
        embed.add_field(
            name=f"{await area.local_name()}",
            value=f"天気: {area.weather}\n"
                  f"最高気温: {area.temp_max} ℃\n"
                  f"最低気温: {area.temp_min} ℃\n"
                  f"降水確率: {area.pop} %",
            inline=True
        )
    embed.set_footer(text="気象庁提供")
    await channel.send(embed=embed)


# 毎日6時に今日の天気予報を通知する
@tasks.loop(time=datetime.time(hour=6, minute=0, second=0, tzinfo=datetime.timezone(datetime.timedelta(hours=+9), 'JST')))
async def today_forecast():
    if notify_channel is not None:
        await forecast_notify(notify_channel, [tokushima, hyogo], "今日")

@tasks.loop(time=datetime.time(hour=18, minute=0, second=0, tzinfo=datetime.timezone(datetime.timedelta(hours=+9), 'JST')))
async def tomorrow_forecast():
    if notify_channel is not None:
        await forecast_notify(notify_channel, [tokushima, hyogo], "明日")
    
client.run(token)