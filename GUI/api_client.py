# api_client.py  

import requests
import time
from config import BASE_URL, PLANT_ID


_cache = None
_cache_time = 0
CACHE_SECONDS = 20

def fetch_latest_summary():

    global _cache, _cache_time

    now = time.time()
    if _cache and (now - _cache_time) < CACHE_SECONDS:
        return _cache  

    url = f"{BASE_URL}/plants/{PLANT_ID}/latest-summary"
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            data = r.json()

            result = {
                "temperature": round(data["sensors"]["temperature"]["value"], 1),
                "light": round(data["sensors"]["light"]["value"], 1),
                "soil_moisture": int(data["sensors"]["soil_moisture"]["value"]),
                "weight": round(data["sensors"]["weight"]["value"], 1),
                "suggestions": data.get("suggestions", "Good condition").strip()
            }

            # 缓存结果
            _cache = result
            _cache_time = now
            return result

    except Exception as e:
        print(f"API request fail: {e}")

    
    if _cache:
        return _cache

    return {
        "temperature": 0.0,
        "light": 0.0,
        "soil_moisture": 0,
        "weight": 0.0,
        "suggestions": "Fail connect to backend"
    }
