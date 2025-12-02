import time
from datetime import datetime
from statistics import mean
from typing import List

from api import get_plant_id_by_nickname, upload_image_file, upload_sensor_and_weight
from camera import capture_photo
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

    avg_temp = average_or_none(temps, rnd=2)
    avg_light = average_or_none(lights, rnd=2)
    avg_soil = average_or_none(soils, rnd=1)
    avg_weight = average_or_none(weights, rnd=2)

    log(f"[avg 10m] temp={avg_temp} °C | light={avg_light} lux | soil={avg_soil} | weight={avg_weight} g")
    upload_sensor_and_weight(plant_id, avg_temp, avg_light, avg_soil, avg_weight)

    # ===== 新增：同时发到 ThingsBoard（只加这三行！）=====
    try:
        from tb_client import upload_to_thingsboard
        sensor_dict = {
            "temperature": avg_temp,
            "light": avg_light,
            "soil_moisture": avg_soil,           # 原始值 0~255
        }
        upload_to_thingsboard(sensor_dict, weight=avg_weight)
    except Exception as e:
        log(f"[ThingsBoard] 调用失败（不影响主流程）: {e}")
def main():
    log("Smart Plant Advisor edge collector (modular)")
    plant_id = PLANT_ID_DEFAULT
    if PLANT_NICKNAME:
        pid = get_plant_id_by_nickname(PLANT_NICKNAME)
        if pid:
            plant_id = pid
    log(f"Using plant_id={plant_id}, backend={BASE_URL}")

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
                # ===== 新增：把照片路径也同步到 ThingsBoard =====
                # try:
                    #from tb_client import upload_to_thingsboard
                    # upload_to_thingsboard({}, photo_path=photo_path)  # 只传照片
                # except Exception as e:
                    # log(f"[ThingsBoard] 照片同步失败: {e}")
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
