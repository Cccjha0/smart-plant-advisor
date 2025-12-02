# camera.py  —— 终极稳定版（一条命令完美复刻预览效果，再见 returncode=255）
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import PHOTO_BASE_DIR, CAMERA_WARMUP_SEC, CAMERA_EV, CAMERA_GAIN
from utils import log


def capture_photo() -> Optional[str]:
    date_dir = PHOTO_BASE_DIR / datetime.now().strftime("%Y%m%d")
    date_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%H%M%S")
    photo_path = date_dir / f"{timestamp}.jpg"

    # 一条命令解决所有问题！（重点在最后几行参数）
    cmd = [
        "rpicam-still",
        "-o", str(photo_path),
        "--width", "3280",
        "--height", "2464",
        "--ev", str(CAMERA_EV),
        "--gain", str(CAMERA_GAIN),
        "--denoise", "cdn_off",
        # 下面这三行是核心！让它先预览稳定再拍照，和你眼睛看到的完全一样
        "-t", str((CAMERA_WARMUP_SEC + 2) * 1000),   # 预览时间（毫秒）
        "--autofocus-mode", "continuous",            # 可选：持续对焦
        "--immediate",                               # 预览结束后立即拍照（不闪一下黑屏）
    ]

    log(f"[photo] 正在拍摄（预览 {CAMERA_WARMUP_SEC}s + 立即拍照）")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0 and photo_path.exists() and photo_path.stat().st_size > 100_000:
        log(f"[photo] 完美照片已保存（和预览一模一样！）: {photo_path}")
        return str(photo_path)
    else:
        log(f"[photo] 拍摄失败 returncode={result.returncode}")
        if result.stderr:
            log(f"    错误信息: {result.stderr.strip()}")
        if photo_path.exists() and photo_path.stat().st_size < 50_000:
            photo_path.unlink()
        return None
