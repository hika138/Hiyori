import datetime
import os
from typing import Optional

import discord
from discord.ext import commands, tasks

from module.area import Area
from module.weathercodeconverter import WetherCodeConverter


class WeatherCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        channel_id_str = os.getenv("CHANNEL_ID")
        if channel_id_str is None:
            raise ValueError("CHANNEL_ID environment variable is not set.")

        self.channel_id = int(channel_id_str)
        self.notify_channel: Optional[discord.TextChannel] = None

        self.areas: list[Area] = [
            Area("徳島県", 34.0667, 134.5594),  # 徳島県
            Area("兵庫県", 34.6913, 135.1830),  # 兵庫県
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
            await self.forecast_notify(self.notify_channel, datetime.datetime.now())
            
        else:
            self.notify_channel = None
            print("Notify channel is not found or is not a text channel.")

    async def forecast_notify(self, channel: discord.TextChannel, day: datetime.datetime):
        embed = discord.Embed(
            title=f"{day.strftime('%m/%d')}の天気予報",
            url="https://www.jma.go.jp/bosai/#pattern=forecast",
            colour=0x00B0F4,
            timestamp=datetime.datetime.now(),
        )

        for area in self.areas:
            forecast = await area.get_forecast(day)
            if forecast is None:
                print(f"Failed to get forecast for {area.name} on {day}.")
                continue

            weather_code = int(forecast["weather_code"])
            weather_text = WetherCodeConverter.convert(weather_code)
            embed.add_field(
                name=area.name,
                value=
                f"天気: {weather_text} \n"
                f"最高気温: {forecast['temperature_max']:.1f} ℃\n"
                f"最低気温: {forecast['temperature_min']:.1f} ℃\n"
                f"降水確率: {forecast['precipitation_probability_max']} %",
                inline=True,
            )
        
        embed.set_footer(text=f"{datetime.datetime.now().strftime('%m/%d %H:%M')}時点")
        await channel.send(embed=embed)

    @tasks.loop(
        time=datetime.time(
            hour=6,
            minute=3,
            second=0,
            tzinfo=datetime.timezone(datetime.timedelta(hours=+9), "JST"),
        )
    )
    async def today_forecast(self):
        if self.notify_channel is not None:
            await self.forecast_notify(self.notify_channel, datetime.datetime.today())

    @tasks.loop(
        time=datetime.time(
            hour=18,
            minute=3,
            second=0,
            tzinfo=datetime.timezone(datetime.timedelta(hours=+9), "JST"),
        )
    )
    async def tomorrow_forecast(self):
        if self.notify_channel is not None:
            await self.forecast_notify(self.notify_channel, datetime.datetime.now() + datetime.timedelta(days=1))


async def setup(bot: commands.Bot):
    await bot.add_cog(WeatherCog(bot))
