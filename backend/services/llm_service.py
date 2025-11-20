from typing import Dict


class LLMService:
    def generate(self, analysis_payload: Dict) -> Dict:
        # Mock implementation for now.
        # Later this can call external_modules.llm.generate_report.
        plant_type = analysis_payload.get("plant_type") or "your plant"
        growth_status = analysis_payload.get("growth_status") or "normal"

        short = (
            f"Status: {growth_status}. "
            f"Keep monitoring temperature, humidity, and soil moisture. "
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
