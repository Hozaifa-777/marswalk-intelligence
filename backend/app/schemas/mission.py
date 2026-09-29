from typing import Optional
from pydantic import BaseModel, Field


class ConsumablesRequest(BaseModel):
    distance_km: float = Field(
        ..., gt=0, description="Total route distance in kilometers"
    )
    average_raw_terrain_cost: float = Field(
        ..., ge=0, description="Average terrain cost multiplier from route response"
    )
    average_slope_percent: Optional[float] = Field(
        default=0.0, description="Average route slope percentage"
    )
    payload_kg: Optional[float] = Field(
        default=0.0, ge=0, description="Carried equipment or sample payload in kg"
    )
    base_walking_speed_ms: Optional[float] = Field(
        default=0.35, gt=0, description="Base EVA walking speed in meters per second"
    )
    suit_capacity_hours: Optional[float] = Field(
        default=8.5, gt=0, description="Maximum EMU suit capacity in hours"
    )


class ConsumablesAssumptions(BaseModel):
    base_walking_speed_ms: float
    kcal_per_liter_o2: float
    suit_capacity_hours: float
    min_metabolic_rate_kcal_hr: float
    max_metabolic_rate_kcal_hr: float
    mars_gravity_m_s2: float
    base_system_mass_kg: float
    payload_mass_kg: float
    muscular_efficiency: float
    disclaimer: str


class ConsumablesResponse(BaseModel):
    estimated_duration_hours: float
    estimated_oxygen_liters: float
    oxygen_percent_of_suit_capacity: float
    average_metabolic_rate_kcal_hr: float
    slope_penalty_kcal_hr: float
    payload_penalty_kcal_hr: float
    safety_margin_hours: float
    assumptions: ConsumablesAssumptions
