from dataclasses import dataclass

from .battery_health import BatteryHealth
from .battery_status import BatteryStatus


@dataclass
class BatteryState:
    soc: float = 0.50
    health: BatteryHealth = BatteryHealth.HEALTHY
    status: BatteryStatus = BatteryStatus.AVAILABLE
    home_load_kw: float = 0.0
    backup_reserve_pct: float = 0.20

    def validate(self, min_soc: float, max_soc: float) -> None:
        if not min_soc <= self.soc <= max_soc:
            raise ValueError(
                f"SOC must be between {min_soc:.0%} and {max_soc:.0%}."
            )
        if self.home_load_kw < 0:
            raise ValueError("home_load_kw cannot be negative.")
        if not 0 <= self.backup_reserve_pct <= 1:
            raise ValueError("backup_reserve_pct must be between 0 and 1.")
