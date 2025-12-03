# tb_client.py
import os
import requests
import time
import json
from pathlib import Path
from utils import log
from dotenv import load_dotenv

load_dotenv()
TB_ACCESS_TOKEN = os.environ["TB_ACCESS_TOKEN"]   


TB_URL = f"https://thingsboard.cloud/api/v1/{TB_ACCESS_TOKEN}/telemetry"
HEADERS = {"Content-Type": "application/json"}
TIMEOUT = 15

def upload_to_thingsboard(sensor_data: dict, weight: float = None, photo_path: str = None):
    
    payload = {
        "temperature": sensor_data.get("temperature"),
        "light": sensor_data.get("light"),
        "soil_moisture_raw": sensor_data.get("soil_moisture"),        
        "soil_moisture_pct": sensor_data.get("soil_moisture_pct", 0), 
        "weight_g": weight,
    }

    
    payload = {k: v for k, v in payload.items() if v is not None}

    try:
        r = requests.post(TB_URL, data=json.dumps(payload), headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 200:
            log(f"[ThingsBoard] Data upload Success → {payload}")
        else:
            log(f"[ThingsBoard] Data upload Fail {r.status_code} → {r.text}")
    except Exception as e:
        log(f"[ThingsBoard] Exception: {e}")

    
    if photo_path and Path(photo_path).exists():
        try:
            
            attr_payload = {"latest_photo": Path(photo_path).name}
            attr_url = f"https://thingsboard.cloud/api/v1/{TB_ACCESS_TOKEN}/attributes"
            requests.post(attr_url, json=attr_payload, timeout=10)
            log(f"[ThingsBoard] Image update → {Path(photo_path).name}")
        except Exception as e:
            log(f"[ThingsBoard] Image marking fail: {e}")
