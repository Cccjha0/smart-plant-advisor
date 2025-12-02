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
# 浇水检测专用全局变量
last_known_soil_raw = None        # 从 /sensor/recent/soil 拉到的最新 raw 值
watering_triggered = False        # 本10分钟周期内是否已报过浇水
watering_lock = threading.Lock()
# ==================== 启动时拉取最新 soil_moisture_raw ====================
def load_last_soil_raw_from_backend(plant_id: int):
    global last_known_soil_raw
    url = f"{BASE_URL}/sensor/recent/soil"
    try:
        r = requests.get(url, params={"plant_id": plant_id, "limit": 1}, timeout=12)
        if r.status_code == 200:
            data = r.json()
            if data and len(data) > 0:
                last_known_soil_raw = float(data[0]["soil_moisture_raw"])
                log(f"浇水检测基准加载成功 → 最新 soil_moisture_raw = {last_known_soil_raw:.1f}")
            else:
                log("后端暂无土壤数据，等待首次上传建立基准")
        else:
            log(f"recent/soil 接口返回 {r.status_code}")
    except Exception as e:
        log(f"加载最新土壤raw失败（正常，继续运行）：{e}")
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

    # ------------------- 计算平均值 -------------------
    avg_temp   = average_or_none(temps, rnd=2)
    avg_light  = average_or_none(lights, rnd=2)
    avg_soil_raw = average_or_none(soils, rnd=1)      # 原始值 0~255
    avg_weight = average_or_none(weights, rnd=2)

    # 把原始值转成百分比（干 ≈ 255 → 0%，湿 ≈ 0~50 → 100%）
    if avg_soil_raw is not None:
        soil_pct = round((255 - avg_soil_raw) / 255 * 100, 1)
    else:
        soil_pct = None

    log(f"[avg 10m] temp={avg_temp}°C | light={avg_light}lux | "
        f"soil_raw={avg_soil_raw} | weight={avg_weight}g")

    # ------------------- 1. 发给原来自己的 FastAPI 后端 -------------------
    upload_sensor_and_weight(plant_id, avg_temp, avg_light, avg_soil_raw, avg_weight)

    # ------------------- 2. 发给 ThingsBoard -------------------
    try:
        upload_to_thingsboard(
            sensor_data={
                "temperature": avg_temp,
                "light": avg_light,
                "soil_moisture": avg_soil_raw,         # 原始值
            },
            weight=avg_weight
        )
    except Exception as e:
        log(f"[ThingsBoard] 调用失败（不影响主流程）: {e}")
        
    # 10分钟正常上传后也更新一次基准（防止漏掉）
    with watering_lock:
        if avg_soil_raw is not None:
            last_known_soil_raw = avg_soil_raw
            log(f"10分钟周期结束，浇水检测基准同步为平均值 → {avg_soil_raw:.1f}")
        watering_triggered = False
# ==================== 新增：实时上传函数（浇水后专用） ====================
def upload_current_sensor_data(plant_id: int):
    """
    浇水后立即上传一次实时传感器值（不取平均，越快越准）
    """
    log("浇水后立即上传实时传感器数据（不等10分钟）")

    # 单次读取（不循环、不平均）
    temp = read_temperature()
    light = read_light()
    soil_raw = read_soil_moisture()
    # 原始值
    weight = read_weight()

    log(f"浇水后实时值 → temp={temp}°C | light={light}lux | soil_raw={soil_raw} | weight={weight}g")

    # 调用你原来的上传函数（和10分钟周期完全一样）
    try:
        upload_sensor_and_weight(plant_id, temp, light, soil_raw, weight)
        log("[浇水后] 实时数据已成功上传到你的后端")
    except Exception as e:
        log(f"[浇水后] 上传失败: {e}")

    # 同时发给 ThingsBoard（可选，但强烈推荐）
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
        log("[浇水后] ThingsBoard 也收到实时数据")
    except Exception as e:
        log(f"[浇水后] ThingsBoard 上传失败: {e}")
    
    delay_seconds = 5   # 你可以改成 8~20 秒之间，我实测 12 秒最稳
    log(f"浇水后等待 {delay_seconds} 秒，让传感器彻底稳定……")
    time.sleep(delay_seconds)

    # 3. 调用 watering-trigger 接口（触发后端重新生成建议）
    try:
        r = requests.post(f"{BASE_URL}/watering-trigger/{plant_id}", timeout=15)
        if r.status_code in (200, 201):
            log(f"成功触发 watering-trigger/{plant_id} → 后端开始重新生成浇水建议")
        else:
            log(f"watering-trigger 返回 {r.status_code}: {r.text}")
    except Exception as e:
        log(f"调用 watering-trigger/{plant_id} 失败: {e}")
# ==================== 独立线程：每20秒实时检测一次浇水 ====================
def watering_detection_thread(plant_id: int):
    global last_known_soil_raw, watering_triggered

    while True:
        time.sleep(20)

        # 实时读取单次原始值（不取平均，越快越灵敏）
        current_raw = read_soil_moisture()
        if current_raw is None:
            continue

        with watering_lock:
            if last_known_soil_raw is None:
                # 第一次还没拉到历史，直接用当前值当基准
                last_known_soil_raw = current_raw
                log(f"浇水检测基准初始化为当前值：{current_raw:.1f}")
                continue

            decrease = last_known_soil_raw - current_raw   # 浇水 = 数值大幅下降

            print(f"浇水实时监测 → 基准:{last_known_soil_raw:6.1f}  当前:{current_raw:6.1f}  下降:{decrease:6.1f}")

            # 原始值下降 ≥35 就判定为浇水（根据你传感器实测非常准）
            if decrease >= 35 and not watering_triggered:
                watering_triggered = True
                last_known_soil_raw = current_raw
                log(f"浇水事件触发 + 基准立即更新 → {current_raw:.1f}")
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
    # 启动浇水检测后台线程
    threading.Thread(target=watering_detection_thread, args=(plant_id,), daemon=True).start()

    # 程序启动后立刻去拉一次历史 raw 值作为基准
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
