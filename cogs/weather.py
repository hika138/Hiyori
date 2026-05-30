import datetime
import os
from typing import Literal, Optional

import discord
from discord.ext import commands, tasks

from module.Area import Area


class WeatherCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        channel_id_str = os.getenv("CHANNEL_ID")
        if channel_id_str is None:
            raise ValueError("CHANNEL_ID environment variable is not set.")

        self.channel_id = int(channel_id_str)
        self.notify_channel: Optional[discord.TextChannel] = None

        self.areas: list[Area] = [
            Area(360000, 360010, 71106),  # 徳島県
            Area(280000, 280010, 63518),
        ]

    @commands.Cog.listener()
    async def on_ready(self):
        channel = self.bot.get_channel(self.channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(self.channel_id)
            except discord.HTTPException:
                channel = None

        if isinstance(channel, discord.TextChannel):
            self.notify_channel = channel

            if not self.today_forecast.is_running():
                self.today_forecast.start()
            if not self.tomorrow_forecast.is_running():
                self.tomorrow_forecast.start()

            print("Weather forecast loops started.")
        else:
            self.notify_channel = None
            print("Notify channel is not found or is not a text channel.")

    async def forecast_notify(self, channel: discord.TextChannel, day: Literal["今日", "明日"]):
        embed = discord.Embed(
            title=f"{day}の天気予報",
            url="https://www.jma.go.jp/bosai/#pattern=forecast",
            colour=0x00B0F4,
            timestamp=datetime.datetime.now(),
        )

        for area in self.areas:
            await area.get_forecast(day)
            embed.add_field(
                name=await area.local_name(),
                value=f"天気: {area.weather}\n"
                f"最高気温: {area.temp_max} ℃\n"
                f"最低気温: {area.temp_min} ℃\n"
                f"降水確率: {area.pop} %",
                inline=True,
            )

        embed.set_footer(text="気象庁提供")
        await channel.send(embed=embed)

    @tasks.loop(
        time=datetime.time(
            hour=6,
            minute=0,
            second=0,
            tzinfo=datetime.timezone(datetime.timedelta(hours=+9), "JST"),
        )
    )
    async def today_forecast(self):
        if self.notify_channel is not None:
            await self.forecast_notify(self.notify_channel, "今日")

    @tasks.loop(
        time=datetime.time(
            hour=18,
            minute=0,
            second=0,
            tzinfo=datetime.timezone(datetime.timedelta(hours=+9), "JST"),
        )
    )
    async def tomorrow_forecast(self):
        if self.notify_channel is not None:
            await self.forecast_notify(self.notify_channel, "明日")


async def setup(bot: commands.Bot):
    await bot.add_cog(WeatherCog(bot))
