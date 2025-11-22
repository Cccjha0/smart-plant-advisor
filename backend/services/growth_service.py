from typing import Dict

from sqlalchemy.orm import Session

from external_modules.growth import analyzer


class GrowthService:
    def analyze(self, plant_id: int, db: Session) -> Dict:
        """
        Delegate to external_modules.growth.analyzer.analyze_growth.
        """
        return analyzer.analyze_growth(plant_id, db)
