# camera.py  
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

    
    cmd = [
        "rpicam-still",
        "-o", str(photo_path),
        "--width", "3280",
        "--height", "2464",
        "--ev", str(CAMERA_EV),
        "--gain", str(CAMERA_GAIN),
        "--denoise", "cdn_off",
        
        "-t", str((CAMERA_WARMUP_SEC + 2) * 1000),  
        "--autofocus-mode", "continuous",            
        "--immediate",                               #
    ]

    log(f"[photo] Shooting（Preview {CAMERA_WARMUP_SEC}s ）")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0 and photo_path.exists() and photo_path.stat().st_size > 100_000:
        log(f"[photo] The photo has been saved: {photo_path}")
        return str(photo_path)
    else:
        log(f"[photo] Fail returncode={result.returncode}")
        if result.stderr:
            log(f"Fail message: {result.stderr.strip()}")
        if photo_path.exists() and photo_path.stat().st_size < 50_000:
            photo_path.unlink()
        return None
