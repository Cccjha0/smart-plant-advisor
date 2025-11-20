from sqlalchemy.orm import Session


class GrowthService:
    def analyze(self, plant_id: int, db: Session) -> dict:
        # Mock implementation for now.
        # Later this can call external_modules.growth.analyzer.
        return {
            "growth_status": "normal",
            "growth_rate_3d": 3.2,
            "stress_factors": [],
        }
