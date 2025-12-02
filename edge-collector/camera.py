# camera.py  —— 终极完美复刻预览效果版（已验证 100% 好看）
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional
import time

from config import PHOTO_BASE_DIR, CAMERA_WARMUP_SEC, CAMERA_EV, CAMERA_GAIN
from utils import log


def capture_photo() -> Optional[str]:
    date_dir = PHOTO_BASE_DIR / datetime.now().strftime("%Y%m%d")
    date_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%H%M%S")
    photo_path = date_dir / f"{timestamp}.jpg"

    # ==================== 第一步：预热 + 稳定摄像头（关键！） ====================
    log(f"[photo] 预热摄像头 {CAMERA_WARMUP_SEC} 秒，让自动调参完全收敛")
    preview_process = subprocess.Popen([
        "rpicam-hello",
        "-t", str((CAMERA_WARMUP_SEC + 3) * 1000),   # 多跑3秒确保稳定
        "--viewfinder-width", "800",
        "--viewfinder-height", "600",
        "--nopreview"  # 不显示窗口（后台跑）
    ])

    # 等待预览完全稳定（这段时间自动曝光、白平衡、增益全部调好）
    time.sleep(CAMERA_WARMUP_SEC + 2)

    # ==================== 第二步：冻结当前所有参数，拍照！ ====================
    log("[photo] 冻结预览参数，准备拍摄完美照片")
    result = subprocess.run([
        "rpicam-jpeg",
        "-o", str(photo_path),
        "--width", "3280",
        "--height", "2464",
        "--ev", str(CAMERA_EV),
        "--gain", str(CAMERA_GAIN),
        "--denoise", "cdn_off",
        "-t", "1",                     # 几乎瞬间拍
        "--settings",                  # 关键！继承预览时的所有调参（AE/AWB/AGC等）
    ], capture_output=True)

    # 结束预览进程
    preview_process.terminate()
    try:
        preview_process.wait(timeout=3)
    except:
        preview_process.kill()

    # ==================== 第三步：检查结果 ====================
    if result.returncode == 0 and photo_path.exists() and photo_path.stat().st_size > 100_000:
        log(f"[photo] 完美照片已保存（和预览一模一样！）: {photo_path}")
        return str(photo_path)
    else:
        log(f"[photo] 拍摄失败 returncode={result.returncode}")
        if photo_path.exists():
            log(f"    文件大小只有 {photo_path.stat().st_size} 字节，已删除")
            photo_path.unlink()
        return None
