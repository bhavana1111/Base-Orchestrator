from dataclasses import dataclass

from .battery import Battery

EPSILON = 1e-9


@dataclass(frozen=True)
class BatteryStormAssessment:
    battery_id: str

    current_energy_kwh: float

    # Energy required to maintain the current home load
    # for the entire storm while protecting reserve.
    current_load_required_energy_kwh: float

    # Energy requirement after applying the maximum
    # sustainable load management.
    required_energy_kwh: float

    deficit_kwh: float
    safe_surplus_kwh: float
    unachievable_energy_kwh: float

    participation_eligible: bool

    current_home_load_kw: float
    sustainable_load_kw: float

    can_manage_with_load: bool

    @property
    def needs_energy(self) -> bool:
        return (
            self.participation_eligible
            and not self.can_manage_with_load
            and self.deficit_kwh > EPSILON
        )

    @property
    def can_provide_energy(self) -> bool:
        return (
            self.participation_eligible
            and self.safe_surplus_kwh > EPSILON
        )

    @property
    def is_ready(self) -> bool:
        return (
            self.participation_eligible
            and self.deficit_kwh <= EPSILON
        )

    @property
    def needs_load_management(self) -> bool:
        return (
            self.participation_eligible
            and self.current_home_load_kw
            > self.sustainable_load_kw + EPSILON
        )


class StormReadinessService:
    def assess_battery(
        self,
        battery: Battery,
        storm_duration_hours: float,
    ) -> BatteryStormAssessment:

        if storm_duration_hours <= 0:
            raise ValueError(
                "storm_duration_hours must be greater than 0."
            )

        current_energy_kwh = battery.energy_kwh

        capacity_kwh = battery.specs.capacity_kwh

        min_energy_kwh = (
            capacity_kwh * battery.specs.min_soc
        )

        max_energy_kwh = (
            capacity_kwh * battery.specs.max_soc
        )

        reserve_energy_kwh = (
            capacity_kwh * battery.backup_reserve_pct
        )

        protected_energy_kwh = max(
            min_energy_kwh,
            reserve_energy_kwh,
        )

        current_home_load_kw = battery.home_load_kw

        # ---------------------------------------------------------
        # 1. Requirement at the CURRENT home load
        # ---------------------------------------------------------

        current_load_energy_kwh = (
            current_home_load_kw
            * storm_duration_hours
        )

        current_load_required_energy_kwh = min(
            max_energy_kwh,
            max(
                min_energy_kwh,
                current_load_energy_kwh
                + protected_energy_kwh,
            ),
        )

        # ---------------------------------------------------------
        # 2. Determine the maximum sustainable home load
        #    using the energy currently available.
        # ---------------------------------------------------------

        energy_available_for_home_kwh = max(
            0.0,
            current_energy_kwh
            - protected_energy_kwh,
        )

        sustainable_load_kw = (
            energy_available_for_home_kwh
            / storm_duration_hours
        )

        # Never recommend a load above the battery's
        # discharge capability.
        sustainable_load_kw = min(
            sustainable_load_kw,
            battery.specs.max_discharge_kw,
        )

        # Never recommend a negative load.
        sustainable_load_kw = max(
            0.0,
            sustainable_load_kw,
        )

        # ---------------------------------------------------------
        # 3. Can load management alone solve the problem?
        # ---------------------------------------------------------

        can_manage_with_load = (
            current_home_load_kw
            <= sustainable_load_kw + EPSILON
        )

        # ---------------------------------------------------------
        # 4. Determine the energy requirement used by
        #    the orchestration decision.
        #
        # If the current load is sustainable, no transfer
        # is required.
        #
        # Otherwise the battery becomes an energy recipient.
        # ---------------------------------------------------------

        if can_manage_with_load:
            required_energy_kwh = current_load_required_energy_kwh

        else:
            # The battery cannot sustain its current load.
            #
            # We retain the current-load requirement as the
            # target for energy replenishment. After receiving
            # energy, we calculate the sustainable load again.
            required_energy_kwh = current_load_required_energy_kwh

        required_energy_kwh = min(
            max_energy_kwh,
            max(
                min_energy_kwh,
                required_energy_kwh,
            ),
        )

        # ---------------------------------------------------------
        # 5. Calculate deficit / safe donor surplus
        # ---------------------------------------------------------

        deficit_kwh = max(
            0.0,
            required_energy_kwh
            - current_energy_kwh,
        )

        safe_surplus_kwh = max(
            0.0,
            current_energy_kwh
            - required_energy_kwh,
        )

        # Unachievable means even a completely charged battery
        # cannot satisfy the requested current load + reserve.
        raw_current_load_requirement_kwh = (
            current_load_energy_kwh
            + protected_energy_kwh
        )

        unachievable_energy_kwh = max(
            0.0,
            raw_current_load_requirement_kwh
            - max_energy_kwh,
        )

        participation_eligible = battery.is_available

        if not participation_eligible:
            safe_surplus_kwh = 0.0
            deficit_kwh = 0.0

        return BatteryStormAssessment(
            battery_id=battery.battery_id,
            current_energy_kwh=current_energy_kwh,
            current_load_required_energy_kwh=(
                current_load_required_energy_kwh
            ),
            required_energy_kwh=required_energy_kwh,
            deficit_kwh=deficit_kwh,
            safe_surplus_kwh=safe_surplus_kwh,
            unachievable_energy_kwh=(
                unachievable_energy_kwh
            ),
            participation_eligible=(
                participation_eligible
            ),
            current_home_load_kw=current_home_load_kw,
            sustainable_load_kw=sustainable_load_kw,
            can_manage_with_load=can_manage_with_load,
        )

    def assess_fleet(
        self,
        batteries: list[Battery],
        storm_duration_hours: float,
    ) -> list[BatteryStormAssessment]:

        return [
            self.assess_battery(
                battery,
                storm_duration_hours,
            )
            for battery in batteries
        ]