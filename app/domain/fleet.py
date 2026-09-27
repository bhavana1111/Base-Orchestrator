from dataclasses import dataclass, field

from .battery import Battery


@dataclass
class Fleet:
    """
    Represents a collection of batteries that can be
    controlled as one aggregate resource.

    Fleet is responsible for:
    - Managing batteries
    - Providing aggregate fleet state
    - Executing fleet-level charge/discharge operations

    Fleet does not decide orchestration strategy and does not
    coordinate battery-to-battery energy transfers.
    """

    fleet_id: str
    batteries: list[Battery] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.fleet_id:
            raise ValueError("fleet_id cannot be empty.")

        self._validate_unique_battery_ids()

    # ----------------------------------------------------------------
    # Battery Access
    # ----------------------------------------------------------------

    @property
    def battery_count(self) -> int:
        return len(self.batteries)

    def add_battery(self, battery: Battery) -> None:
        if self.get_battery(battery.battery_id) is not None:
            raise ValueError(
                f"Battery {battery.battery_id} already exists."
            )

        self.batteries.append(battery)

    def remove_battery(self, battery_id: str) -> Battery:
        battery = self.get_battery(battery_id)

        if battery is None:
            raise ValueError(
                f"Battery {battery_id} not found."
            )

        self.batteries.remove(battery)
        return battery

    def get_battery(self, battery_id: str) -> Battery | None:
        for battery in self.batteries:
            if battery.battery_id == battery_id:
                return battery

        return None

    # ----------------------------------------------------------------
    # Fleet State
    # ----------------------------------------------------------------

    @property
    def available_batteries(self) -> list[Battery]:
        return [
            battery
            for battery in self.batteries
            if battery.is_available
        ]

    @property
    def unavailable_batteries(self) -> list[Battery]:
        return [
            battery
            for battery in self.batteries
            if not battery.is_available
        ]

    @property
    def total_capacity_kwh(self) -> float:
        return sum(
            battery.specs.capacity_kwh
            for battery in self.batteries
        )

    @property
    def total_energy_kwh(self) -> float:
        return sum(
            battery.energy_kwh
            for battery in self.batteries
        )

    @property
    def average_soc(self) -> float:
        if not self.batteries:
            return 0.0

        return sum(
            battery.soc
            for battery in self.batteries
        ) / len(self.batteries)

    @property
    def available_charge_kw(self) -> float:
        return sum(
            battery.specs.max_charge_kw
            for battery in self.available_batteries
        )

    @property
    def available_discharge_kw(self) -> float:
        return sum(
            battery.specs.max_discharge_kw
            for battery in self.available_batteries
        )

    # ----------------------------------------------------------------
    # Fleet Operations
    # ----------------------------------------------------------------

    def charge(
        self,
        target_power_kw: float,
        duration_hours: float,
    ) -> float:
        self._validate_target(target_power_kw)
        self._validate_duration(duration_hours)

        remaining_power_kw = target_power_kw
        actual_power_kw = 0.0

        for battery in self.available_batteries:
            if remaining_power_kw <= 0:
                break

            battery_power_kw = min(
                remaining_power_kw,
                battery.specs.max_charge_kw,
            )

            energy_added = battery.charge(
                power_kw=battery_power_kw,
                duration_hours=duration_hours,
            )

            actual_power_kw += (
                energy_added / duration_hours
            )

            remaining_power_kw -= (
                energy_added / duration_hours
            )

        return actual_power_kw

    def discharge(
        self,
        target_power_kw: float,
        duration_hours: float,
    ) -> float:
        self._validate_target(target_power_kw)
        self._validate_duration(duration_hours)

        remaining_power_kw = target_power_kw
        actual_power_kw = 0.0

        for battery in self.available_batteries:
            if remaining_power_kw <= 0:
                break

            battery_power_kw = min(
                remaining_power_kw,
                battery.specs.max_discharge_kw,
            )

            energy_removed = battery.discharge(
                power_kw=battery_power_kw,
                duration_hours=duration_hours,
            )

            actual_power_kw += (
                energy_removed / duration_hours
            )

            remaining_power_kw -= (
                energy_removed / duration_hours
            )

        return actual_power_kw

    # ----------------------------------------------------------------
    # Validation
    # ----------------------------------------------------------------

    def _validate_target(self, target_power_kw: float) -> None:
        if target_power_kw < 0:
            raise ValueError(
                "target_power_kw cannot be negative."
            )

    def _validate_duration(
        self,
        duration_hours: float,
    ) -> None:
        if duration_hours <= 0:
            raise ValueError(
                "duration_hours must be greater than zero."
            )

    def _validate_unique_battery_ids(self) -> None:
        battery_ids = [
            battery.battery_id
            for battery in self.batteries
        ]

        if len(battery_ids) != len(set(battery_ids)):
            raise ValueError(
                "Fleet cannot contain duplicate battery IDs."
            )
