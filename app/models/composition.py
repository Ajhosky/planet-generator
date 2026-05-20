from pydantic import BaseModel, Field


class PlanetComposition(BaseModel):
    silicates: float = Field(0.35, ge=0.0, le=1.0)
    iron_magnesium: float = Field(0.25, ge=0.0, le=1.0)
    water_ice: float = Field(0.20, ge=0.0, le=1.0)
    carbon: float = Field(0.05, ge=0.0, le=1.0)
    sulfur: float = Field(0.03, ge=0.0, le=1.0)
    titanium: float = Field(0.02, ge=0.0, le=1.0)
    radioactive_elements: float = Field(0.02, ge=0.0, le=1.0)
    nitrogen: float = Field(0.03, ge=0.0, le=1.0)
    methane: float = Field(0.02, ge=0.0, le=1.0)
    ammonia: float = Field(0.02, ge=0.0, le=1.0)
    phosphorus: float = Field(0.01, ge=0.0, le=1.0)

    def normalized(self) -> "PlanetComposition":
        values = self.model_dump()
        total = sum(values.values())

        if total <= 0:
            return PlanetComposition()

        normalized_values = {
            key: value / total
            for key, value in values.items()
        }

        return PlanetComposition(**normalized_values)