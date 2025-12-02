from typing import Dict, Any, Optional
import logging

try:
    from external_modules.llm.workflow_service import WorkflowService  # type: ignore
except Exception:
    WorkflowService = None


class LLMService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            logging.basicConfig(level=logging.INFO)
        self.workflow: Optional[WorkflowService] = None
        if WorkflowService:
            try:
                self.workflow = WorkflowService()
                self.logger.info("LLMService: workflow_service loaded.")
            except Exception:
                # If Coze is not configured/installed, keep mock fallback
                self.workflow = None
                self.logger.warning("LLMService: workflow_service init failed, using mock.")
        else:
            self.logger.info("LLMService: workflow_service not available, using mock.")

    def generate(self, analysis_payload: Dict) -> Dict:
        """
        Generate LLM text report.
        - If workflow_service is configured, call workflow with full JSON payload.
        - Otherwise, return mock fallback.
        """
        if self.workflow:
            try:
                self.logger.info("LLMService.generate: using workflow_service with full payload JSON")
                def _str_or_blank(v):
                    return "" if v is None else str(v)
                growth_rate_val = analysis_payload.get("growth_rate_3d")
                growth_rate_str = str(growth_rate_val) if growth_rate_val is not None else "0"
                growth_status_str = _str_or_blank(analysis_payload.get("growth_status")) or "unknown"
                image_url_val = analysis_payload.get("image_url")

                base_payload = {
                    "growth_rate_3d": growth_rate_str,
                    "growth_status": growth_status_str,
                    "metrics_snapshot": analysis_payload.get("metrics_snapshot") or {},
                    "nickname": _str_or_blank(analysis_payload.get("nickname")) or "unknown",
                    "plant_id": _str_or_blank(analysis_payload.get("plant_id")) or "unknown",
                    "sensor_data": analysis_payload.get("sensor_data") or {},
                    "stress_factors": analysis_payload.get("stress_factors") or {},
                }
                if image_url_val:
                    base_payload["image_url"] = image_url_val

                # drop any None values to avoid invalid inputs
                full_payload = {k: v for k, v in base_payload.items() if v is not None}
                self.logger.info("LLMService.generate: sending payload to Coze", extra={"coze_payload_keys": list(full_payload.keys())})
                result = self.workflow.analyze_with_growth_payload(full_payload)
                if result:
                    return result
            except Exception as e:
                self.logger.warning("LLMService.generate: workflow call failed, fallback to mock. err=%s", e)

        # Mock fallback
        self.logger.info("LLMService.generate: using mock fallback.")
        plant_type = analysis_payload.get("plant_type") or "your plant"
        growth_status = analysis_payload.get("growth_status") or "normal"

        growth_overview = f"Growth status: {growth_status}. Trending stable."
        environment_assessment = "Env OK. Keep light and watering in recommended range."
        suggestions = "Monitor moisture daily; adjust light if below target."
        full_analysis = (
            "This is a mock analysis.\n\n"
            f"Plant type: {plant_type}\n"
            f"Growth status: {growth_status}\n"
            "In production, this will include detailed CN/EN analysis of sensor trends and actions."
        )

        return {
            "plant_type": plant_type,
            "growth_overview": growth_overview,
            "environment_assessment": environment_assessment,
            "suggestions": suggestions,
            "full_analysis": full_analysis,
            "alert": None,
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
