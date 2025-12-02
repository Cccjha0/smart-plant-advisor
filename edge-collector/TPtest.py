# 文件名随便，比如 tb_http.py
import requests
import json
import time

# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
# 把这行改成你刚刚复制的那串 Token！！！
ACCESS_TOKEN = "qcw9jm9ev86ij1ifj928"   # ←←← 改这里！！！
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←

URL = f"https://thingsboard.cloud/api/v1/{ACCESS_TOKEN}/telemetry"

while True:
    data = {
        "temperature": round(20 + 10* (time.time() % 1000)/1000, 1),  # 模拟变化
        "humidity": round(50 + 20* (time.time() % 1000)/1000, 1),
        "light": int(300 + 700* (time.time() % 1000)/1000),
        "soil_moisture_pct": round(30 + 40* (time.time() % 1000)/1000, 1)
    }

    try:
        r = requests.post(URL, json=data, timeout=10)
        print(f"[{time.strftime('%X')}] → {data}   状态码: {r.status_code}")
        if r.status_code != 200:
            print("   错误返回:", r.text)
    except Exception as e:
        print("发送失败:", e)

    time.sleep(15)   # 15秒发一次，免费版完全够用