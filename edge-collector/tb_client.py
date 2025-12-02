# tb_client.py
import requests
import json
from pathlib import Path
from utils import log
from dotenv import load_dotenv
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
# 第一步：在这里填你设备的 Access Token（只填一次！）
load_dotenv()
TB_ACCESS_TOKEN = os.environ["TB_ACCESS_TOKEN"]   # ←←← 必填！！！
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←

TB_URL = f"https://thingsboard.cloud/api/v1/{TB_ACCESS_TOKEN}/telemetry"
HEADERS = {"Content-Type": "application/json"}
TIMEOUT = 15

def upload_to_thingsboard(sensor_data: dict, weight: float = None, photo_path: str = None):
    """
    把传感器数据、重量、照片同时推送到 ThingsBoard
    sensor_data 里至少要有 temperature, light, soil_moisture（你现在的字段）
    """
    payload = {
        "temperature": sensor_data.get("temperature"),
        "light": sensor_data.get("light"),
        "soil_moisture_raw": sensor_data.get("soil_moisture"),        # 原始 0~255
        "soil_moisture_pct": sensor_data.get("soil_moisture_pct", 0), # 你原来算好的百分比
        "weight_g": weight,
    }

    # 移除 None 值（ThingsBoard 不喜欢 null）
    payload = {k: v for k, v in payload.items() if v is not None}

    try:
        r = requests.post(TB_URL, data=json.dumps(payload), headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 200:
            log(f"[ThingsBoard] 数据上传成功 → {payload}")
        else:
            log(f"[ThingsBoard] 数据上传失败 {r.status_code} → {r.text}")
    except Exception as e:
        log(f"[ThingsBoard] 上传异常: {e}")

    # 照片单独走属性接口（ThingsBoard 目前 HTTP 只支持 telemetry，图片用 attribute 存路径或 base64）
    if photo_path and Path(photo_path).exists():
        try:
            # 这里我们只上传照片路径（更省流量），你也可以改成 base64
            attr_payload = {"latest_photo": Path(photo_path).name}
            attr_url = f"https://thingsboard.cloud/api/v1/{TB_ACCESS_TOKEN}/attributes"
            requests.post(attr_url, json=attr_payload, timeout=10)
            log(f"[ThingsBoard] 照片标记更新 → {Path(photo_path).name}")
        except Exception as e:
            log(f"[ThingsBoard] 照片标记失败: {e}")
