import json
import requests
from fpdf import FPDF
from flask import Flask, request, render_template

from weather.constansts import *

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/predict_weather', methods=['POST'])
def predict_weather():
    if request.method == 'POST':
        location = request.form.get('location')
        try:
            response = fetch_weather_data(location)
            weather_data = parse_weather_data(response)
            print("API RESPONSE:", response)
            return render_template('home.html', **weather_data)
        except Exception as e:
            print("ERROR:", e)
            return render_template('home.html', error=str(e))


def fetch_weather_data(location):
    url = "https://api.weatherapi.com/v1/forecast.json"

    params = {
        "key": API_KEY,
        "q": location,
        "days": 1,
        "aqi": "yes",
        "alerts": "yes"
    }

    response = requests.get(url, params=params)
    return response.json()


def get_india_aqi(air_quality):
    """Calculate India AQI from pollutant breakpoints (CPCB standard)"""
    pm25 = air_quality.get('pm2_5', 0)
    pm10 = air_quality.get('pm10', 0)

    # India AQI breakpoints for PM2.5 (µg/m³)
    pm25_bp = [
        (0,   30,  0,   50),
        (30,  60,  51,  100),
        (60,  90,  101, 200),
        (90,  120, 201, 300),
        (120, 250, 301, 400),
        (250, 500, 401, 500),
    ]

    # India AQI breakpoints for PM10 (µg/m³)
    pm10_bp = [
        (0,   50,  0,   50),
        (50,  100, 51,  100),
        (100, 250, 101, 200),
        (250, 350, 201, 300),
        (350, 430, 301, 400),
        (430, 600, 401, 500),
    ]

    def calc(value, breakpoints):
        for (c_lo, c_hi, i_lo, i_hi) in breakpoints:
            if c_lo <= value <= c_hi:
                return round(((i_hi - i_lo) / (c_hi - c_lo)) * (value - c_lo) + i_lo)
        return 500  # Beyond scale

    aqi_value = max(calc(pm25, pm25_bp), calc(pm10, pm10_bp))

    if aqi_value <= 50:    category = "Good"
    elif aqi_value <= 100: category = "Satisfactory"
    elif aqi_value <= 200: category = "Moderate"
    elif aqi_value <= 300: category = "Poor"
    elif aqi_value <= 400: category = "Very Poor"
    else:                  category = "Severe"

    return aqi_value, category


def parse_weather_data(data):
    location_data = data['location']
    current_data = data['current']
    alerts_data = data.get('alerts', {}).get('alert', [])
    air_quality = current_data.get('air_quality', {})

    aqi_value, aqi_category = get_india_aqi(air_quality)

    return {
        'name': location_data['name'],
        'region': location_data['region'],
        'country': location_data['country'],
        'lat': location_data['lat'],
        'lon': location_data['lon'],
        'tz_id': location_data['tz_id'],
        'localtime_epoch': location_data['localtime_epoch'],
        'localtime': location_data['localtime'],
        'last_updated_epoch': current_data['last_updated_epoch'],
        'last_updated': current_data['last_updated'],
        'temp_c': current_data['temp_c'],
        'temp_f': current_data['temp_f'],
        'is_day': current_data['is_day'],
        'condition_text': current_data['condition']['text'],
        'condition_icon': current_data['condition']['icon'],
        'wind_mph': current_data['wind_mph'],
        'wind_kph': current_data['wind_kph'],
        'wind_degree': current_data['wind_degree'],
        'wind_dir': current_data['wind_dir'],
        'pressure_mb': current_data['pressure_mb'],
        'pressure_in': current_data['pressure_in'],
        'precip_mm': current_data['precip_mm'],
        'precip_in': current_data['precip_in'],
        'humidity': current_data['humidity'],
        'cloud': current_data['cloud'],
        'feelslike_c': current_data['feelslike_c'],
        'feelslike_f': current_data['feelslike_f'],
        'vis_km': current_data['vis_km'],
        'vis_miles': current_data['vis_miles'],
        'uv': current_data['uv'],
        'gust_mph': current_data['gust_mph'],
        'gust_kph': current_data['gust_kph'],
        'aqi_co':       round(air_quality.get('co', 0), 1),
        'aqi_no2':      round(air_quality.get('no2', 0), 1),
        'aqi_o3':       round(air_quality.get('o3', 0), 1),
        'aqi_so2':      round(air_quality.get('so2', 0), 1),
        'aqi_pm25':     round(air_quality.get('pm2_5', 0), 1),
        'aqi_pm10':     round(air_quality.get('pm10', 0), 1),
        'aqi_value':    aqi_value,
        'aqi_category': aqi_category,
        'alerts':       alerts_data,
    }


if __name__ == '__main__':
    app.run(debug=True)