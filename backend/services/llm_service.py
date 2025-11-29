from typing import Dict, Any, Optional

try:
    from external_modules.llm.workflow_service import WorkflowService  # type: ignore
except Exception:
    WorkflowService = None


class LLMService:
    def __init__(self) -> None:
        self.workflow: Optional[WorkflowService] = None
        if WorkflowService:
            try:
                self.workflow = WorkflowService()
            except Exception:
                # If Coze is not configured/installed, keep mock fallback
                self.workflow = None

    def generate(self, analysis_payload: Dict) -> Dict:
        """Generate LLM text report (mock fallback)."""
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

    def analyze_image(self, image_url: str) -> Dict[str, Any]:
        """
        Run vision analysis via Coze workflow when available; fallback to mock.
        """
        if self.workflow:
            try:
                result = self.workflow.analyze_plant(image_url=image_url, sensor_data={})
                return {
                    "plant_type": result.get("plant_type"),
                    "leaf_health": result.get("leaf_health"),
                    "symptoms": result.get("symptoms", []),
                    "report_short": result.get("report_short"),
                    "report_long": result.get("report_long"),
                    "raw_response": result.get("raw_response"),
                }
            except Exception:
                # On any failure, fall back to mock
                pass

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
