# config.py
import os
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
PLANT_ID = 1

# 路径
PROJECT_ROOT = Path("/home/pi/smart-plant-advisor")
PHOTO_DIR = PROJECT_ROOT / "backend" / "data" / "images"
ART_DIR = PROJECT_ROOT / "art"
ASSETS = "/art"  # 你可以改成相对路径更稳

# 硬件
PIR_PIN = 27

# 显示参数
ART_SWITCH_INTERVAL = 8000    # 无人时换图间隔（毫秒）
DATA_REFRESH_INTERVAL = 10000 # 数据刷新间隔
PERSON_STAY_DELAY = 5         # 人离开后延迟几秒切回艺术模式