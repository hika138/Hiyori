import openmeteo_requests
from datetime import datetime

class Area:
    def __init__(self, name: str, latitude: float, longitude: float):
        self.name = name  # 地域名
        self.latitude = latitude  # 緯度
        self.longitude = longitude  # 経度
        
        self.openmeteo = openmeteo_requests.Client()
        

    # 天気予報を取得するメソッド
    async def get_forecast(self, day: datetime):
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "precipitation_probability_max"],
            "timezone": "Asia/Tokyo",
            "start_date": day.strftime("%Y-%m-%d"),
            "end_date": day.strftime("%Y-%m-%d"),
        }
        response = self.openmeteo.weather_api(url, params = params)[0]
        daily = response.Daily()
        if daily is None:
            return None
        daily_weather_code_var = daily.Variables(0)
        daily_temperature_2m_max_var = daily.Variables(1)
        daily_temperature_2m_min_var = daily.Variables(2)
        daily_precipitation_probability_max_var = daily.Variables(3)

        if (
            daily_weather_code_var is None
            or daily_temperature_2m_max_var is None
            or daily_temperature_2m_min_var is None
            or daily_precipitation_probability_max_var is None
        ):
            return None

        daily_weather_code = daily_weather_code_var.ValuesAsNumpy()
        daily_temperature__max = daily_temperature_2m_max_var.ValuesAsNumpy()
        daily_temperature_min = daily_temperature_2m_min_var.ValuesAsNumpy()
        daily_precipitation_probability_max = daily_precipitation_probability_max_var.ValuesAsNumpy()
        
        return {
            "weather_code": daily_weather_code[0],
            "temperature_max": daily_temperature__max[0],
            "temperature_min": daily_temperature_min[0],
            "precipitation_probability_max": daily_precipitation_probability_max[0],
        }