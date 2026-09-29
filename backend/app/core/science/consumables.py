import math
from app.schemas.mission import (
    ConsumablesAssumptions,
    ConsumablesRequest,
    ConsumablesResponse,
)

MARS_GRAVITY = 3.71  # m/s^2
KCAL_PER_LITER_O2 = 4.86  # Standard indirect calorimetry ratio
MIN_METABOLIC_RATE = 100.0  # Min rate in kcal/hr
BASE_METABOLIC_RATE = 200.0  # Nominal flat rate in kcal/hr
MAX_METABOLIC_RATE = 500.0  # Peak allowable EMU suit cooling threshold in kcal/hr

TERRAIN_SPEED_DEGRADATION_K = 0.15
METABOLIC_TERRAIN_FACTOR = 0.25
BASE_SYSTEM_MASS_KG = 180.0  # Suit (100kg) + Astronaut (80kg)
MUSCULAR_EFFICIENCY = 0.22  # NASA HIDH human concentric muscular efficiency (~22%)


def calculate_eva_consumables(request: ConsumablesRequest) -> ConsumablesResponse:
    base_speed_ms = request.base_walking_speed_ms or 0.35
    suit_cap_hrs = request.suit_capacity_hours or 8.5
    payload_kg = request.payload_kg or 0.0

    total_mass_kg = BASE_SYSTEM_MASS_KG + payload_kg

    # 1. Calculate effective speed based on terrain cost, slope, and payload drag
    slope_pct = request.average_slope_percent or 0.0
    slope_abs = abs(slope_pct)
    slope_speed_factor = 1.0 + (0.02 * slope_abs)
    payload_speed_factor = 1.0 + (0.005 * payload_kg)

    effective_speed_ms = base_speed_ms / (
        (1.0 + TERRAIN_SPEED_DEGRADATION_K * request.average_raw_terrain_cost)
        * slope_speed_factor
        * payload_speed_factor
    )
    effective_speed_kmh = effective_speed_ms * 3.6

    duration_hours = request.distance_km / effective_speed_kmh

    # 2. Base metabolic expenditure scaled by terrain cost
    raw_metabolic = BASE_METABOLIC_RATE * (
        1.0 + METABOLIC_TERRAIN_FACTOR * request.average_raw_terrain_cost
    )

    # 3. Flat load carriage penalty (Pandolf formulation adjusted for Martian gravity)
    payload_penalty_kcal_hr = (
        1.2 * payload_kg * (0.38 + 0.5 * (effective_speed_ms**2))
    )

    # 4. Incline work penalty using total mass (Base + Payload)
    slope_rad = math.atan(slope_pct / 100.0)
    if slope_pct > 0:
        mechanical_power_watts = (
            total_mass_kg * MARS_GRAVITY * effective_speed_ms * math.sin(slope_rad)
        )
        metabolic_power_watts = mechanical_power_watts / MUSCULAR_EFFICIENCY
        slope_penalty_kcal_hr = metabolic_power_watts * 0.859845
    else:
        slope_penalty_kcal_hr = max(-30.0, slope_pct * 1.5)

    # Sum up metabolic contributions and clamp to EMU cooling limits
    total_metabolic_rate = raw_metabolic + slope_penalty_kcal_hr + payload_penalty_kcal_hr
    bounded_metabolic_rate = min(
        MAX_METABOLIC_RATE, max(MIN_METABOLIC_RATE, total_metabolic_rate)
    )

    # 5. Total consumable expenditure calculations
    total_kcal = bounded_metabolic_rate * duration_hours
    estimated_oxygen_liters = total_kcal / KCAL_PER_LITER_O2
    oxygen_percent = (duration_hours / suit_cap_hrs) * 100.0
    safety_margin = max(0.0, suit_cap_hrs - duration_hours)

    assumptions = ConsumablesAssumptions(
        base_walking_speed_ms=base_speed_ms,
        kcal_per_liter_o2=KCAL_PER_LITER_O2,
        suit_capacity_hours=suit_cap_hrs,
        min_metabolic_rate_kcal_hr=MIN_METABOLIC_RATE,
        max_metabolic_rate_kcal_hr=MAX_METABOLIC_RATE,
        mars_gravity_m_s2=MARS_GRAVITY,
        base_system_mass_kg=BASE_SYSTEM_MASS_KG,
        payload_mass_kg=payload_kg,
        muscular_efficiency=MUSCULAR_EFFICIENCY,
        disclaimer=(
            "Calculations incorporate Pandolf load carriage formulations and NASA Bioastronautics "
            "gravity scaling for combined astronaut, suit, and carried payload masses."
        ),
    )

    return ConsumablesResponse(
        estimated_duration_hours=round(duration_hours, 3),
        estimated_oxygen_liters=round(estimated_oxygen_liters, 2),
        oxygen_percent_of_suit_capacity=round(oxygen_percent, 2),
        average_metabolic_rate_kcal_hr=round(bounded_metabolic_rate, 2),
        slope_penalty_kcal_hr=round(slope_penalty_kcal_hr, 2),
        payload_penalty_kcal_hr=round(payload_penalty_kcal_hr, 2),
        safety_margin_hours=round(safety_margin, 3),
        assumptions=assumptions,
    )
