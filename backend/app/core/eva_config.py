"""Configuration for weather-aware routing and the segment EVA model.

Every number here is one of three kinds, and the API reports the kind next
to the value:

* ``modeled``  - a planning-model parameter chosen for this prototype. It has
                 not been validated against EVA or rover data.
* ``assumed``  - a planning input (masses, defaults) that a mission planner
                 is expected to replace.
* a constant with a cited source (unit conversions, Pandolf coefficients,
  gravity). Those sources are given in the comments next to each value.

A few values can be overridden through environment variables so that an
operator can change them without editing code:

    MARSWALK_WEATHER_INTENSITY_PATH   path to Task 1 weather_intensity.parquet
    MARSWALK_WEATHER_BETA             beta (float >= 0)
    MARSWALK_WEATHER_REQUIRED         "1"/"true" -> 422 when W_t is unavailable
    MARSWALK_WEATHER_WINDOW_S         selection window in LMST seconds
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Task 1 output directory: MEDA weather pipeline runtime data.
# Contains weather_intensity.parquet and manifest.json.
# These files are included in the repository for deployment.

WEATHER_PROCESSED_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "resources"
    / "MEDA_Weather_ds"
    / "processed"
)

DEFAULT_WEATHER_INTENSITY_PATH = (
    WEATHER_PROCESSED_DIR / "weather_intensity.parquet"
)




def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# ============================================================
# Weather in the route cost
# ============================================================


@dataclass(frozen=True)
class WeatherCostConfig:
    """C(i) = T(i) * F(i) + P(i), F(i) = 1 + beta * W_t * s(i).

    beta (modeled, not validated): how strongly the regional weather index
    raises the cost of sloped cells. With beta = 0.5 and the largest W_t in
    the Task 1 output for Sols 230-239 (0.737), the steepest cells
    (s = 1) cost 1.37x their terrain-only value. Flat cells (s = 0) are never
    changed.

    Weather penalty P(i) = penalty_coefficient * W_t * s(i). It is OFF
    (coefficient 0). It can only be switched on together with a written
    scientific justification; see validate().

    Weather hard constraints (blocking cells because of weather) are not
    implemented. The only hard constraint stays the 20 deg slope mask.
    """

    beta: float = 0.5
    penalty_coefficient: float = 0.0
    penalty_justification: str = ""
    # When True, a request whose W_t cannot be found is rejected (HTTP 422)
    # instead of being routed with weather switched off.
    weather_required: bool = False

    def validate(self) -> None:
        if not (self.beta >= 0.0):
            raise ValueError("Weather beta must be >= 0.")
        if not (self.penalty_coefficient >= 0.0):
            raise ValueError("Weather penalty coefficient must be >= 0 (P >= 0 keeps A* admissible).")
        if self.penalty_coefficient > 0.0 and not self.penalty_justification.strip():
            raise ValueError(
                "A weather penalty can only be enabled with a documented scientific "
                "justification (penalty_justification)."
            )


# ============================================================
# Weather time selection (Task 1 W_t records)
# ============================================================


@dataclass(frozen=True)
class WeatherTimeConfig:
    """How a requested (sol, start_time) is matched to a W_t record.

    Time basis: LMST (local mean solar time). The ``sol`` column of the Task 1
    output is the LMST sol (its LMST strings always start with the same sol,
    while LTST strings roll into the next sol near midnight), and LMST is a
    uniform clock, so differences are well defined. Time differences are
    reported in LMST seconds (1/86400 of a mean sol, about 1.0275 SI s).

    Window: the nearest record of the SAME sol whose LMST is within
    ``window_s`` of the requested time. Records of neighbouring sols are
    never used.

    Quality: only records whose quality_status is in ``accepted_quality``.
    Task 1 marks a record 'suspect' when some components are missing; for
    those, W_t is the weighted mean of the remaining components only (for
    example air temperature alone), which is on a different footing from a
    complete record, so they are not used by default.

    Defaults when the request has no sol / start_time:
      default_sol = None   -> the latest sol present in the Task 1 output
      default_start_time   -> 12:00:00 LMST
    """

    path: Path = DEFAULT_WEATHER_INTENSITY_PATH
    window_s: float = 1800.0
    accepted_quality: tuple[str, ...] = ("valid",)
    default_sol: int | None = None
    default_start_time: str = "12:00:00"
    time_basis: str = "lmst"
    # Two LMST times closer than this are reported as an exact match.
    exact_match_tolerance_s: float = 0.0005


# ============================================================
# Segment EVA model
# ============================================================

STANDARD_GRAVITY_M_S2 = 9.80665  # CGPM 1901 standard acceleration of gravity
MARS_GRAVITY_M_S2 = 3.71  # mean surface gravity of Mars (task specification)

# 1 W = 3600 J/h / 4186.8 J/kcal (International Table calorie) = 0.859845 kcal/h
KCAL_PER_HOUR_PER_WATT = 0.859845

# Energy equivalent of oxygen. 4.86 kcal per litre O2 is the Zuntz-Schumburg
# table value (4.862) at a non-protein respiratory quotient of about 0.85.
KCAL_PER_LITER_O2 = 4.86


@dataclass(frozen=True)
class EvaModelConfig:
    """Segment speed and Pandolf energy model.

    Speed (modeled):
        v = v0 / (1 + k_t * (C_t - 1)) / (1 + k_s * slope_pct)
      C_t is the raw terrain cost of the cell (no mode weight, no weather
      factor). The task text writes T = 1 + w (C_t - 1) here; using the mode
      weight would make the same ground slower to walk in "conservative" mode
      than in "fastest" mode, which has no physical basis, so the raw value
      is the default. speed_uses_mode_weighted_terrain = True restores T.
      k_t and k_s are modeled constants without a validation source. Their
      magnitudes are carried over from the prototype (0.15 and 0.02) and are
      labelled as modeled in every response.

    Default v0 (assumed): 0.75 m/s = 2.7 km/h, the average speed Apollo
      planners assumed for suited walkbacks of over an hour (Apollo Lunar
      Surface Journal, "Lunar Gaits"). It is a planning value for a suited
      walker on unprepared ground; terrain and slope slow it further.

    Energy: Pandolf, Givoni & Goldman (1977), J. Appl. Physiol. 43:577-581,
        M [W] = 1.5 W + 2.0 (W + L)(L / W)^2 + eta (W + L)(1.5 V^2 + 0.35 V G)
      W body mass (kg), L carried load (kg), V speed (m/s), G grade (%),
      eta terrain factor (1.0 = treadmill / paved reference surface).

    Mars gravity (modeled): the two terms that pay for weight are scaled by
    g_mars / g_earth = 3.71 / 9.80665:
      * the load-support term 2.0 (W + L)(L / W)^2,
      * the grade term 0.35 V G (lifting work; its coefficient corresponds to
        g * 0.01 divided by a muscular efficiency, so it is proportional to g).
      The 1.5 W standing term (largely resting metabolism) and the 1.5 V^2
      level-walking term are NOT scaled: neither is proportional to weight in
      the source, and reduced-gravity walking studies do not show the level
      cost falling in proportion to gravity. Leaving them unscaled errs on the
      high side.

    Downhill (modeled): Pandolf is defined for level and uphill walking. For
      negative grades the grade term is set to 0 (no credit for descending).
      The Santee et al. (2003) downhill correction is not implemented.

    The suit is treated as carried load L. Masses are planning assumptions.
    """

    # modeled
    k_t: float = 0.15
    k_s: float = 0.02
    speed_uses_mode_weighted_terrain: bool = False
    # assumed
    body_mass_kg: float = 80.0
    suit_mass_kg: float = 100.0
    terrain_factor_eta: float = 1.0
    default_base_walking_speed_ms: float = 0.75
    default_suit_capacity_hours: float = 8.5
    # Reporting bounds for the average metabolic rate (kcal/h). Values outside
    # are NOT silently clamped: the raw value is kept in all totals, and a
    # clamped value plus a warning are reported next to it.
    min_metabolic_rate_kcal_hr: float = 100.0
    max_metabolic_rate_kcal_hr: float = 500.0
    # Weather effect on energy: no supported, documented model -> 0.
    weather_energy_coefficient: float = 0.0
    # constants (sourced above)
    mars_gravity_m_s2: float = MARS_GRAVITY_M_S2
    earth_gravity_m_s2: float = STANDARD_GRAVITY_M_S2
    kcal_per_hour_per_watt: float = KCAL_PER_HOUR_PER_WATT
    kcal_per_liter_o2: float = KCAL_PER_LITER_O2

    @property
    def gravity_scale(self) -> float:
        return self.mars_gravity_m_s2 / self.earth_gravity_m_s2


@dataclass(frozen=True)
class EvaWeatherSettings:
    cost: WeatherCostConfig = field(default_factory=WeatherCostConfig)
    time: WeatherTimeConfig = field(default_factory=WeatherTimeConfig)
    eva: EvaModelConfig = field(default_factory=EvaModelConfig)


def load_settings() -> EvaWeatherSettings:
    """Defaults above, with the documented environment overrides applied."""
    cost = WeatherCostConfig(
        beta=_env_float("MARSWALK_WEATHER_BETA", WeatherCostConfig.beta),
        weather_required=_env_bool("MARSWALK_WEATHER_REQUIRED", WeatherCostConfig.weather_required),
    )
    cost.validate()

    path_override = os.environ.get("MARSWALK_WEATHER_INTENSITY_PATH")
    time = WeatherTimeConfig(
        path=Path(path_override) if path_override else DEFAULT_WEATHER_INTENSITY_PATH,
        window_s=_env_float("MARSWALK_WEATHER_WINDOW_S", WeatherTimeConfig.window_s),
    )
    if not (time.window_s >= 0.0):
        raise ValueError("Weather selection window must be >= 0 seconds.")

    return EvaWeatherSettings(cost=cost, time=time, eva=EvaModelConfig())


_SETTINGS: EvaWeatherSettings | None = None


def get_settings() -> EvaWeatherSettings:
    """Settings for this process (read once). Tests may call set_settings()."""
    global _SETTINGS
    if _SETTINGS is None:
        _SETTINGS = load_settings()
    return _SETTINGS


def set_settings(settings: EvaWeatherSettings | None) -> None:
    """Replace the process settings (None -> re-read defaults on next use)."""
    global _SETTINGS
    if settings is not None:
        settings.cost.validate()
    _SETTINGS = settings
