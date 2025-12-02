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
                import json

                def _dump_obj(obj: Any) -> str:
                    try:
                        return json.dumps(obj or {}, ensure_ascii=False)
                    except Exception:
                        return "{}"
                growth_rate_val = analysis_payload.get("growth_rate_3d")
                growth_rate_str = str(growth_rate_val) if growth_rate_val is not None else "0"
                growth_status_str = _str_or_blank(analysis_payload.get("growth_status")) or "unknown"
                image_url_val = analysis_payload.get("image_url")

                base_payload = {
                    "growth_rate_3d": growth_rate_str,
                    "growth_status": growth_status_str,
                    "metrics_snapshot": _dump_obj(analysis_payload.get("metrics_snapshot")),
                    "nickname": _str_or_blank(analysis_payload.get("nickname")) or "unknown",
                    "plant_id": _str_or_blank(analysis_payload.get("plant_id")) or "unknown",
                    "sensor_data": _dump_obj(analysis_payload.get("sensor_data")),
                    "stress_factors": _dump_obj(analysis_payload.get("stress_factors")),
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
        """
        Dream image generation (CN workflow when available), fallback to mock PNG.
        Returns: {"data": bytes|None, "ext": str, "url": str|None, "describe": str|None, "msg": str|None}
        """
        # Prefer CN workflow if configured
        if self.workflow and hasattr(self.workflow, "generate_dream_image_cn"):
            try:
                payload = {
                    "plant_id": str(plant_id),
                    "temperature": str(sensor_payload.get("temperature", "")),
                    "light": str(sensor_payload.get("light", "")),
                    "soil_moisture": str(sensor_payload.get("soil_moisture", "")),
                    "health_status": str(
                        sensor_payload.get("health_status")
                        or sensor_payload.get("full_analysis")
                        or sensor_payload.get("growth_status", "")
                    ),
                }
                self.logger.info("LLMService.generate_dream_image: sending payload to Coze CN", extra={"coze_payload": payload})
                result = self.workflow.generate_dream_image_cn(payload)
                if result:
                    output = result.get("output")
                    msg = result.get("msg")
                    describe = result.get("describe") or result.get("description")
                    # If output missing but msg contains JSON string with output/describe
                    if not output and isinstance(msg, str) and msg.strip().startswith("{"):
                        import json
                        try:
                            parsed_msg = json.loads(msg)
                            output = output or parsed_msg.get("output")
                            describe = describe or parsed_msg.get("describe") or parsed_msg.get("description")
                        except Exception:
                            pass
                    if isinstance(output, str):
                        # URL case
                        if output.startswith("http"):
                            return {"data": None, "ext": "url", "url": output, "describe": describe, "msg": msg}
                        # base64 string case
                        import base64
                        try:
                            data_bytes = base64.b64decode(output)
                            return {"data": data_bytes, "ext": "png", "url": None, "describe": describe, "msg": msg}
                        except Exception:
                            pass
                    elif isinstance(output, bytes):
                        return {"data": output, "ext": "png", "url": None, "describe": describe, "msg": msg}
                    # if output unusable, fall through to mock
                    self.logger.warning("LLMService.generate_dream_image: CN workflow returned unusable output, using mock. msg=%s", msg)
            except Exception as e:
                self.logger.warning("LLMService.generate_dream_image: CN workflow failed, fallback to mock. err=%s", e)

        # Mock fallback
        self.logger.info("LLMService.generate_dream_image: using mock fallback.")
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDAT\x08\xd7c```"
            b"\x00\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        return {
            "data": png_bytes,
            "ext": "png",
            "url": None,
            "describe": None,
            "msg": "mock",
        }
