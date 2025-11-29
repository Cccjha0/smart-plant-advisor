from datetime import datetime
from typing import Dict, Any


class LLMService:
    def generate(self, analysis_payload: Dict) -> Dict:
        """Mock LLM text report."""
        plant_type = analysis_payload.get("plant_type") or "your plant"
        growth_status = analysis_payload.get("growth_status") or "normal"

        short = (
            f"Status: {growth_status}. "
            f"Keep monitoring temperature, light, and soil moisture. "
            f"Adjust watering and light if conditions move out of the recommended range."
        )

        long = (
            "This is a mock weekly report.\n\n"
            f"Plant type: {plant_type}\n"
            f"Growth status: {growth_status}\n\n"
            "In the real version, this section will contain a detailed bilingual (CN/EN) "
            "analysis of sensor trends, leaf health, and recommended actions."
        )

        return {
            "short_report": short,
            "long_report": long,
        }

    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Mock vision analysis using LLM (placeholder)."""
        # In production, call a vision-capable LLM here.
        return {
            "plant_type": "unknown",
            "leaf_health": "healthy",
            "symptoms": [],
        }

    def generate_dream_image(self, plant_id: int, sensor_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Mock dream garden image generation based on sensor snapshot."""
        # 1x1 transparent PNG bytes
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDAT\x08\xd7c```"
            b"\x00\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        return {
            "data": png_bytes,
            "ext": "png",
        }
