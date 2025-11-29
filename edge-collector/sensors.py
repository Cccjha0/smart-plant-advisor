import glob
import os
import time
from typing import Optional


def read_temperature() -> Optional[float]:
    try:
        if not os.path.exists("/sys/bus/w1/devices"):
            os.system("sudo modprobe w1-gpio")
            os.system("sudo modprobe w1-therm")
            time.sleep(1)

        device_folder = glob.glob("/sys/bus/w1/devices/28-*")
        if not device_folder:
            return None
        device_file = os.path.join(device_folder[0], "w1_slave")

        for _ in range(5):
            with open(device_file, "r") as f:
                lines = f.readlines()
            if len(lines) < 2:
                raise ValueError("w1_slave content incomplete")
            if lines[0].strip().endswith("YES"):
                temp_str = lines[1].split("t=")[1]
                temp_c = round(float(temp_str) / 1000.0, 2)
                if -10 <= temp_c <= 80:
                    return temp_c
            time.sleep(0.3)
    except Exception:
        return None
    return None


def read_light() -> Optional[float]:
    try:
        import smbus2

        bus = smbus2.SMBus(1)
        bus.write_byte(0x23, 0x10)
        time.sleep(0.18)
        data = bus.read_i2c_block_data(0x23, 0x10, 2)
        lux = round((data[0] << 8 | data[1]) / 1.2, 2)
        bus.close()
        return lux
    except Exception:
        return None


def read_soil_moisture() -> Optional[int]:
    try:
        import smbus2

        PCF8591_ADDR = 0x48
        CHANNEL = 0
        MAX_RETRIES = 8

        bus = smbus2.SMBus(1)
        for _ in range(MAX_RETRIES):
            bus.write_byte(PCF8591_ADDR, 0x40 + CHANNEL)
            bus.read_byte(PCF8591_ADDR)
            value = bus.read_byte(PCF8591_ADDR)
            if value != 128:
                bus.close()
                return int(value)
            time.sleep(0.05)
        bus.close()
    except Exception:
        return None
    return None


def read_weight() -> Optional[float]:
    try:
        from HX711 import HX711

        OFFSET = -282730
        CAL_FACTOR = 236.12

        hx = HX711(dout=22, pd_sck=23, gain=128)
        hx.offset = OFFSET

        raw_values = []
        for _ in range(8):
            raw = hx.read()
            if raw not in (0x7FFFFF, -0x800000):
                raw_values.append(raw)
            time.sleep(0.05)
        hx.cleanup()

        if not raw_values:
            return None

        raw_values.sort()
        median_raw = raw_values[len(raw_values) // 2]
        weight = round((median_raw - OFFSET) / CAL_FACTOR, 2)
        if -10 < weight < 0:
            weight = 0.0
        return weight
    except Exception:
        return None
