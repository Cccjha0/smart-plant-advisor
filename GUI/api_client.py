# api_client.py  ——  完美修复版，适配 /plants/{id}/latest-summary

import requests
import time
from config import BASE_URL, PLANT_ID

# 简单缓存：20秒内只请求一次，极大减轻后端压力
_cache = None
_cache_time = 0
CACHE_SECONDS = 20

def fetch_latest_summary():
    """获取最新的传感器值和养护建议（只调用一个接口！）"""
    global _cache, _cache_time

    now = time.time()
    if _cache and (now - _cache_time) < CACHE_SECONDS:
        return _cache  # 直接返回缓存

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
                "suggestions": data.get("suggestions", "状态良好～").strip()
            }

            # 缓存结果
            _cache = result
            _cache_time = now
            return result

    except Exception as e:
        print(f"API 请求失败: {e}")

    # 失败时返回上次缓存或兜底值
    if _cache:
        return _cache

    return {
        "temperature": 0.0,
        "light": 0.0,
        "soil_moisture": 0,
        "weight": 0.0,
        "suggestions": "无法连接到后端"
    }
