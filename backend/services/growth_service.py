from typing import Dict

from sqlalchemy.orm import Session

from external_modules.growth import analyzer


class GrowthService:
    def analyze(self, plant_id: int, db: Session) -> Dict:
        return analyzer.analyze_growth(plant_id, db)
