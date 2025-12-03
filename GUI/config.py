# config.py
import os
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
PLANT_ID = 1


PROJECT_ROOT = Path("/home/pi/smart-plant-advisor")
PHOTO_DIR = PROJECT_ROOT / "backend" / "data" / "images"
ART_DIR = PROJECT_ROOT / "art"
ASSETS = "/art"  

PIR_PIN = 27


ART_SWITCH_INTERVAL = 8000    
DATA_REFRESH_INTERVAL = 10000 
PERSON_STAY_DELAY = 5         
