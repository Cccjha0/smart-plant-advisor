from pathlib import Path

# Backend config
PLANT_NICKNAME = "testPlant"
PLANT_ID_DEFAULT = 0
BASE_URL = "http://127.0.0.1:8000"

# Paths
PHOTO_BASE_DIR = Path("/home/pi/smart-plant-advisor/edge-collector/photo")
LOG_DIR = Path("/home/pi/smart-plant-advisor/edge-collector/logs")

# Sampling
CYCLE_INTERVAL = 10 * 60        # seconds
SAMPLES_PER_CYCLE = 4
SAMPLE_INTERVAL = 3             # seconds between samples

# Camera
CAMERA_EV = 6
CAMERA_GAIN = 4
CAMERA_WARMUP_SEC = 5

# Network
TIMEOUT = 30
MAX_RETRIES = 3

# Ensure directories
PHOTO_BASE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
