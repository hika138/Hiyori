import aiohttp
from typing import Literal

class Area:
    def __init__(self, pref_code, area_code, local_code):
        self.pref_code = pref_code  # 都道府県コード
        self.area_code = area_code  # 地域コード
        self.local_code = local_code # 市町村コード

        self.weather = ""
        self.temp_max = 0
        self.temp_min = 0
        self.pop = 0
        
    
    async def local_name(self) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://www.jma.go.jp/bosai/forecast/data/forecast/{str(self.pref_code)}.json') as response:
                forecast_json = await response.json()
        # 該当市町村を取得
        for local_area in forecast_json[0]["timeSeries"][2]["areas"]:
            if int(local_area["area"]["code"]) == self.local_code:
                return str(local_area["area"]["name"])
        return ""  # 該当市町村が見つからない場合は空文字列を返す

    # 天気予報を取得するメソッド
    async def get_forecast(self, day:Literal["今日", "明日"]):
        if day == "今日":
            day_num = 0
        elif day == "明日":
            day_num = 1
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://www.jma.go.jp/bosai/forecast/data/forecast/{str(self.pref_code)}.json') as response:
                forecast_json = await response.json()
                
        # 該当地域の天気予報を取得
        for weather_area in forecast_json[0]["timeSeries"][0]["areas"]:
            if int(weather_area["area"]["code"]) == self.area_code:
                self.weather = str(weather_area["weathers"][day_num]).replace("\u3000", "")
                
        # 該当地域の予想最高低気温を取得
        for temp_area in forecast_json[0]["timeSeries"][2]["areas"]:
            if int(temp_area["area"]["code"]) == self.local_code:
                # 当日の最高気温と最低気温を取得
                self.temp_min = float(temp_area["temps"][0])
                self.temp_max = float(temp_area["temps"][1])
                

        # 該当地域の日中予想降水確率を取得
        pops = set()  # popsを初期化    
        for pops_area in forecast_json[0]["timeSeries"][1]["areas"]:
            if int(pops_area["area"]["code"]) == self.area_code:
                if day == "今日":
                    # 当日の降水確率の平均値
                    pops = {pops_area["pops"][0], pops_area["pops"][1], pops_area["pops"][2]}
                elif day == "明日":
                    # 翌日の降水確率の平均値
                    pops = {pops_area["pops"][2], pops_area["pops"][3], pops_area["pops"][4]}
        pop_sum = 0
        for pop in pops:
            pop_sum += int(pop)
        # 降水確率の平均値を取得
        self.pop = round(pop_sum / len(pops), 1) if pops else 0  # popsが空の場合は0
