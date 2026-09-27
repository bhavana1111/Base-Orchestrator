from dataclasses import dataclass

from .battery import Battery


@dataclass(frozen=True)
class BatteryStormAssessment:
    battery_id: str
    current_energy_kwh: float
    required_energy_kwh: float
    deficit_kwh: float
    safe_surplus_kwh: float
    unachievable_energy_kwh: float
    participation_eligible: bool

    @property
    def needs_energy(self) -> bool:
        return self.deficit_kwh > 1e-9

    @property
    def can_provide_energy(self) -> bool:
        return self.safe_surplus_kwh > 1e-9

    @property
    def is_ready(self) -> bool:
        return self.deficit_kwh <= 1e-9


class StormReadinessService:
    def assess_battery(
        self,
        battery: Battery,
        storm_duration_hours: float,
    ) -> BatteryStormAssessment:
        if storm_duration_hours <= 0:
            raise ValueError("storm_duration_hours must be greater than 0.")

        current_energy_kwh = battery.energy_kwh
        expected_home_energy_kwh = battery.home_load_kw * storm_duration_hours
        reserve_energy_kwh = (
            battery.specs.capacity_kwh * battery.backup_reserve_pct
        )
        min_energy_kwh = battery.specs.capacity_kwh * battery.specs.min_soc
        max_energy_kwh = battery.specs.capacity_kwh * battery.specs.max_soc

        raw_required_energy_kwh = (
            expected_home_energy_kwh + reserve_energy_kwh
        )

        required_energy_kwh = min(
            max_energy_kwh,
            max(min_energy_kwh, raw_required_energy_kwh),
        )

        unachievable_energy_kwh = max(
            0.0,
            raw_required_energy_kwh - max_energy_kwh,
        )

        deficit_kwh = max(
            0.0,
            required_energy_kwh - current_energy_kwh,
        )

        safe_surplus_kwh = max(
            0.0,
            current_energy_kwh - required_energy_kwh,
        )

        participation_eligible = battery.is_available

        if not participation_eligible:
            safe_surplus_kwh = 0.0

        return BatteryStormAssessment(
            battery_id=battery.battery_id,
            current_energy_kwh=current_energy_kwh,
            required_energy_kwh=required_energy_kwh,
            deficit_kwh=deficit_kwh,
            safe_surplus_kwh=safe_surplus_kwh,
            unachievable_energy_kwh=unachievable_energy_kwh,
            participation_eligible=participation_eligible,
        )

    def assess_fleet(
        self,
        batteries: list[Battery],
        storm_duration_hours: float,
    ) -> list[BatteryStormAssessment]:
        return [
            self.assess_battery(battery, storm_duration_hours)
            for battery in batteries
        ]
