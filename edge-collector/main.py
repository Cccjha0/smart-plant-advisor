import time
import threading
import requests
from datetime import datetime
from statistics import mean
from typing import List
from watering_detector import watering_detector
from api import get_plant_id_by_nickname, upload_image_file, upload_sensor_and_weight
from camera import capture_photo
from tb_client import upload_to_thingsboard
from config import (
    BASE_URL,
    CYCLE_INTERVAL,
    PLANT_ID_DEFAULT,
    PLANT_NICKNAME,
    SAMPLE_INTERVAL,
    SAMPLES_PER_CYCLE,
)
from sensors import read_light, read_soil_moisture, read_temperature, read_weight
from utils import log

last_known_soil_raw = None        
watering_triggered = False        
watering_lock = threading.Lock()

def load_last_soil_raw_from_backend(plant_id: int):
    global last_known_soil_raw
    url = f"{BASE_URL}/sensor/recent/soil"
    try:
        r = requests.get(url, params={"plant_id": plant_id, "limit": 1}, timeout=12)
        if r.status_code == 200:
            data = r.json()
            if data and len(data) > 0:
                last_known_soil_raw = float(data[0]["soil_moisture_raw"])
                log(f"Watering test loading successful → Latest data: soil_moisture_raw = {last_known_soil_raw:.1f}")
            else:
                log("The backend currently no soil data available. It is waiting for the first upload to establish the baseline.")
        else:
            log(f"recent/soil API return {r.status_code}")
    except Exception as e:
        log(f"Failed to load the latest soil raw data.{e}")
def average_or_none(values: List[float], rnd: int = None):
    if not values:
        return None
    val = mean(values)
    return round(val, rnd) if rnd is not None else val


def run_cycle(plant_id: int):
    temps: list = []
    lights: list = []
    soils: list = []
    weights: list = []

    for i in range(SAMPLES_PER_CYCLE):
        log(f"[sample] {i+1}/{SAMPLES_PER_CYCLE}")
        temp = read_temperature()
        light = read_light()
        soil = read_soil_moisture()
        weight = read_weight()

        if temp is not None:
            temps.append(temp)
        if light is not None:
            lights.append(light)
        if soil is not None:
            soils.append(soil)
        if weight is not None:
            weights.append(weight)

        log(f"  temp={temp} °C | light={light} lux | soil={soil} | weight={weight} g")
        time.sleep(SAMPLE_INTERVAL)

    
    avg_temp   = average_or_none(temps, rnd=2)
    avg_light  = average_or_none(lights, rnd=2)
    avg_soil_raw = average_or_none(soils, rnd=1)      
    avg_weight = average_or_none(weights, rnd=2)

    
    if avg_soil_raw is not None:
        soil_pct = round((255 - avg_soil_raw) / 255 * 100, 1)
    else:
        soil_pct = None

    log(f"[avg 10m] temp={avg_temp}°C | light={avg_light}lux | "
        f"soil_raw={avg_soil_raw} | weight={avg_weight}g")

    
    upload_sensor_and_weight(plant_id, avg_temp, avg_light, avg_soil_raw, avg_weight)

    
    try:
        upload_to_thingsboard(
            sensor_data={
                "temperature": avg_temp,
                "light": avg_light,
                "soil_moisture": avg_soil_raw,         
            },
            weight=avg_weight
        )
    except Exception as e:
        log(f"[ThingsBoard] Call failed: {e}")
        
    
    if avg_soil_raw is not None:
        with watering_lock:                     
            global last_known_soil_raw          
            last_known_soil_raw = avg_soil_raw
            
            
            watering_triggered = False
      
        log(f"End of 10-minute cycle.  Watering inspection benchmark is automatically updated to the latest average value:{avg_soil_raw:.1f}")
    else:
        log("The avg_soil_raw is None，Skip the benchmark update")

def upload_current_sensor_data(plant_id: int):
    log("Upload real-time sensor data immediately after watering")

    
    temp = read_temperature()
    light = read_light()
    soil_raw = read_soil_moisture()
    
    weight = read_weight()

    log(f"After Watering → temp={temp}°C | light={light}lux | soil_raw={soil_raw} | weight={weight}g")

    
    try:
        upload_sensor_and_weight(plant_id, temp, light, soil_raw, weight)
        log("[After watering] The data has been successfully uploaded to your backend.")
    except Exception as e:
        log(f"[After watering] Upload failed: {e}")

    
    try:
        from tb_client import upload_to_thingsboard
        upload_to_thingsboard(
            sensor_data={
                "temperature": temp,
                "light": light,
                "soil_moisture": soil_raw,
            },
            weight=weight
        )
        log("[After watering] The data has been successfully uploaded to your ThingsBoard.")
    except Exception as e:
        log(f"[After watering] ThingsBoard Upload failed: {e}")
    
    delay_seconds = 5
    log(f"Wait {delay_seconds} seconds")
    time.sleep(delay_seconds)

    
    try:
        r = requests.post(f"{BASE_URL}/watering-trigger/{plant_id}", timeout=15)
        if r.status_code in (200, 201):
            log(f"Successfully triggered: watering-trigger/{plant_id} → The backend has started to regenerate the suggestions.")
        else:
            log(f"watering-trigger return {r.status_code}: {r.text}")
    except Exception as e:
        log(f"Call watering-trigger/{plant_id} fail: {e}")

def watering_detection_thread(plant_id: int):
    global last_known_soil_raw, watering_triggered

    while True:
        time.sleep(20)

        
        current_raw = read_soil_moisture()
        if current_raw is None:
            continue

        with watering_lock:
            if last_known_soil_raw is None:
                
                last_known_soil_raw = current_raw
                log(f"The watering detection threshold is initialized to the current value.：{current_raw:.1f}")
                continue

            decrease = last_known_soil_raw - current_raw   

            print(f"Real-time irrigation monitoring → Benchmark:{last_known_soil_raw:6.1f}  Current:{current_raw:6.1f}  decrease:{decrease:6.1f}")

            
            if decrease >= 35 and not watering_triggered:
                watering_triggered = True
                last_known_soil_raw = current_raw
                log(f"Watering event triggered + Benchmark updated immediately → {current_raw:.1f}")
                try:
                    upload_current_sensor_data(plant_id)
                except:
                    pass
def main():
    log("Smart Plant Advisor edge collector (modular)")
    plant_id = PLANT_ID_DEFAULT
    if PLANT_NICKNAME:
        pid = get_plant_id_by_nickname(PLANT_NICKNAME)
        if pid:
            plant_id = pid
    log(f"Using plant_id={plant_id}, backend={BASE_URL}")
    
    threading.Thread(target=watering_detection_thread, args=(plant_id,), daemon=True).start()

    
    load_last_soil_raw_from_backend(plant_id)
    last_photo_time = time.time() - 3600

    while True:
        cycle_start = time.time()
        log(f"\n{'='*20} {datetime.now():%Y-%m-%d %H:%M:%S} cycle {'='*20}")

        run_cycle(plant_id)

        current_time = time.time()
        if current_time - last_photo_time >= 3600:
            log(f"\n{'!'*20} hourly photo {'!'*20}")
            photo_path = capture_photo()
            if photo_path:
                upload_image_file(plant_id, photo_path)
                
            else:
                log("[photo] capture failed; will retry next hour")
            last_photo_time = current_time
        else:
            minutes_left = int((3600 - (current_time - last_photo_time)) // 60)
            log(f"[photo] next capture in ~{minutes_left} minutes")

        elapsed = time.time() - cycle_start
        sleep_time = max(0, CYCLE_INTERVAL - elapsed)
        log(f"[sleep] {sleep_time:.1f}s\n")
        time.sleep(sleep_time)


if __name__ == "__main__":
    main()
