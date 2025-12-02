# watering_detector.py   ←←← 直接全部替换成这版！保证一次成功
import time
from utils import log
from typing import Optional, Dict, Any

class WateringDetector:
    """
    只用原始值（0~255）检测浇水
    浇水时数值会从高（干）突然降到低（湿），我们检测“下降幅度”
    """
    def __init__(self, threshold_raw: int = 30, window_seconds: int = 120):
        self.threshold = threshold_raw       # 下降多少算浇水，默认 30（可改成 25~40 都行）
        self.window = window_seconds         # 检测窗口秒数
        self.history = []
        self.last_trigger = 0                # 防止 1 分钟内重复报

    def add_sample(self, soil_moisture_raw: float) -> bool:
        if soil_moisture_raw is None:
            return False

        ts = time.time()
        self.history.append({"ts": ts, "soil": soil_moisture_raw})

        # 清理旧数据
        cutoff = ts - self.window
        self.history = [x for x in self.history if x["ts"] > cutoff]

        if len(self.history) < 3:
            return False

        # 窗口内最干的值（最高数值） vs 当前值
        max_soil = max(item["soil"] for item in self.history)
        decrease = max_soil - soil_moisture_raw

        if decrease >= self.threshold and (ts - self.last_trigger) > 60:
            self.last_trigger = ts
            log(f"浇水事件触发！土壤原始值从 {max_soil:.1f} → {soil_moisture_raw:.1f} "
                f"(下降 {decrease:.1f}，阈值 {self.threshold})")
            return True
        return False


# 全局单例 —— 只用原始值，阈值 30 可自行调小/大
watering_detector = WateringDetector(threshold_raw=30, window_seconds=120)
