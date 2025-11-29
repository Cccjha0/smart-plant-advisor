import os
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

    log(f"[photo] warming camera for {CAMERA_WARMUP_SEC}s")
    subprocess.run(["rpicam-hello", "-t", str(CAMERA_WARMUP_SEC * 1000)], check=False)

    log("[photo] capturing...")
    result = subprocess.run(
        [
            "rpicam-jpeg",
            "-o",
            str(photo_path),
            "--width",
            "3280",
            "--height",
            "2464",
            "--ev",
            str(CAMERA_EV),
            "--gain",
            str(CAMERA_GAIN),
            "--denoise",
            "cdn_off",
            "-t",
            "2000",
        ],
        capture_output=True,
    )

    if result.returncode == 0 and photo_path.exists() and photo_path.stat().st_size > 50_000:
        log(f"[photo] saved: {photo_path}")
        return str(photo_path)

    log(f"[photo] capture failed (code {result.returncode})")
    return None
