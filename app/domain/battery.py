from dataclasses import dataclass

from .battery_health import BatteryHealth
from .battery_specs import BatterySpecs
from .battery_state import BatteryState
from .battery_status import BatteryStatus


@dataclass
class Battery:
    battery_id: str
    home_id: str
    specs: BatterySpecs
    state: BatteryState

    def __post_init__(self) -> None:
        if not self.battery_id:
            raise ValueError("battery_id cannot be empty.")
        if not self.home_id:
            raise ValueError("home_id cannot be empty.")
        self.state.validate(
            min_soc=self.specs.min_soc,
            max_soc=self.specs.max_soc,
        )

    @property
    def soc(self) -> float:
        return self.state.soc

    @property
    def health(self) -> BatteryHealth:
        return self.state.health

    @property
    def status(self) -> BatteryStatus:
        return self.state.status

    @property
    def is_available(self) -> bool:
        return (
            self.health != BatteryHealth.FAILED
            and self.status != BatteryStatus.OFFLINE
        )

    @property
    def home_load_kw(self) -> float:
        return self.state.home_load_kw

    @property
    def backup_reserve_pct(self) -> float:
        return self.state.backup_reserve_pct

    @property
    def energy_kwh(self) -> float:
        return self.specs.capacity_kwh * self.state.soc

    @property
    def available_charge_kwh(self) -> float:
        max_energy = self.specs.capacity_kwh * self.specs.max_soc
        return max_energy - self.energy_kwh

    @property
    def available_discharge_kwh(self) -> float:
        min_energy = self.specs.capacity_kwh * self.specs.min_soc
        return self.energy_kwh - min_energy

    def charge(self, power_kw: float, duration_hours: float) -> float:
        self._validate_operation(power_kw, duration_hours)
        self._ensure_available()

        actual_power_kw = min(power_kw, self.specs.max_charge_kw)
        requested_energy_kwh = actual_power_kw * duration_hours

        actual_energy_kwh = min(
            requested_energy_kwh,
            self.available_charge_kwh,
        )

        if actual_energy_kwh > 0:
            self.state.soc += actual_energy_kwh / self.specs.capacity_kwh
            self.state.status = BatteryStatus.CHARGING

        return actual_energy_kwh

    def discharge(self, power_kw: float, duration_hours: float) -> float:
        self._validate_operation(power_kw, duration_hours)
        self._ensure_available()

        actual_power_kw = min(power_kw, self.specs.max_discharge_kw)
        requested_energy_kwh = actual_power_kw * duration_hours

        actual_energy_kwh = min(
            requested_energy_kwh,
            self.available_discharge_kwh,
        )

        if actual_energy_kwh > 0:
            self.state.soc -= actual_energy_kwh / self.specs.capacity_kwh
            self.state.status = BatteryStatus.DISCHARGING

        return actual_energy_kwh

    def mark_available(self) -> None:
        self.state.status = BatteryStatus.AVAILABLE

    def mark_offline(self) -> None:
        self.state.status = BatteryStatus.OFFLINE

    def mark_healthy(self) -> None:
        self.state.health = BatteryHealth.HEALTHY

    def mark_degraded(self) -> None:
        self.state.health = BatteryHealth.DEGRADED

    def mark_failed(self) -> None:
        self.state.health = BatteryHealth.FAILED
        self.state.status = BatteryStatus.OFFLINE

    def update_home_load(self, home_load_kw: float) -> None:
        if home_load_kw < 0:
            raise ValueError("home_load_kw cannot be negative.")
        self.state.home_load_kw = home_load_kw

    def update_backup_reserve(self, backup_reserve_pct: float) -> None:
        if not 0 <= backup_reserve_pct <= 1:
            raise ValueError("backup_reserve_pct must be between 0 and 1.")
        self.state.backup_reserve_pct = backup_reserve_pct

    def _validate_operation(
        self,
        power_kw: float,
        duration_hours: float,
    ) -> None:
        if power_kw <= 0:
            raise ValueError("power_kw must be greater than zero.")
        if duration_hours <= 0:
            raise ValueError("duration_hours must be greater than zero.")

    def _ensure_available(self) -> None:
        if not self.is_available:
            raise ValueError(
                f"Battery {self.battery_id} is not available."
            )
