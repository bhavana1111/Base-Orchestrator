from dataclasses import dataclass


@dataclass(frozen=True)
class BatterySpecs:
    capacity_kwh: float = 39.2
    max_charge_kw: float = 11.0
    max_discharge_kw: float = 11.0
    min_soc: float = 0.20
    max_soc: float = 0.95

    def __post_init__(self) -> None:
        if self.capacity_kwh <= 0:
            raise ValueError("capacity_kwh must be greater than 0.")
        if self.max_charge_kw <= 0:
            raise ValueError("max_charge_kw must be greater than 0.")
        if self.max_discharge_kw <= 0:
            raise ValueError("max_discharge_kw must be greater than 0.")
        if not 0 <= self.min_soc < self.max_soc <= 1:
            raise ValueError(
                "SOC limits must satisfy 0 <= min_soc < max_soc <= 1."
            )
