import requests
from typing import Optional

from pathlib import Path

from config import BASE_URL, TIMEOUT, MAX_RETRIES
from utils import log

session = requests.Session()


def get_plant_id_by_nickname(nickname: str) -> Optional[int]:
    url = f"{BASE_URL}/plants/by-nickname/{nickname}"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log(f"[plant] resolving nickname='{nickname}' (try {attempt}/{MAX_RETRIES})")
            r = session.get(url, timeout=15)
            if r.status_code == 200:
                data = r.json()
                pid = data.get("id")
                if isinstance(pid, int):
                    log(f"[plant] resolved: {nickname} -> plant_id={pid}")
                    return pid
                log(f"[plant] missing id in response: {data}")
                return None
            if r.status_code == 404:
                log(f"[plant] nickname '{nickname}' not found")
                return None
            log(f"[plant] HTTP {r.status_code}: {r.text}")
        except Exception as e:  # pragma: no cover
            log(f"[plant] request failed: {e}")
            if attempt < MAX_RETRIES:
                continue
    return None


def upload_sensor_and_weight(plant_id: int, temp, light, soil, weight):
    url_sensor = f"{BASE_URL}/sensor"
    url_weight = f"{BASE_URL}/weight"
    payload_sensor = {
        "plant_id": plant_id,
        "temperature": temp,
        "light": light,
        "soil_moisture": soil,
    }
    payload_weight = {
        "plant_id": plant_id,
        "weight": weight,
    }
    r1 = session.post(url_sensor, json=payload_sensor, timeout=TIMEOUT)
    r2 = session.post(url_weight, json=payload_weight, timeout=TIMEOUT)
    return r1, r2


def upload_image_file(plant_id: int, photo_path: str):
    """
    Upload a local image file to backend /upload_image (multipart form-data).
    The backend now uploads to Supabase Storage and stores the public URL.
    """
    url = f"{BASE_URL}/upload_image"
    path_obj = Path(photo_path)
    if not path_obj.exists():
        log(f"[upload_image] file not found: {photo_path}")
        return None

    with path_obj.open("rb") as f:
        files = {
            "plant_id": (None, str(plant_id)),
            "image": (path_obj.name, f, "image/jpeg"),
        }
        try:
            return requests.post(url, files=files, timeout=TIMEOUT)
        except Exception as e:  # pragma: no cover
            log(f"[upload_image] request failed: {e}")
            return None
