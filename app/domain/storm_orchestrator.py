from dataclasses import dataclass

from .battery import Battery, BatteryHealth
from .energy_transfer import (
    EnergyTransfer,
    EnergyTransferResult,
)
from .fleet import Fleet
from .grid import Grid
from .storm_readiness import (
    BatteryStormAssessment,
    StormReadinessService,
)


@dataclass(frozen=True)
class LoadManagementRecommendation:
    battery_id: str
    current_load_kw: float
    recommended_max_load_kw: float
    reduction_kw: float
    storm_duration_hours: float


@dataclass(frozen=True)
class StormReadinessPlan:
    assessments: list[BatteryStormAssessment]
    transfers: list[EnergyTransfer]
    load_recommendations: list[LoadManagementRecommendation]
    total_energy_needed_kwh: float
    total_safe_surplus_kwh: float
    total_planned_transfer_kwh: float
    unfulfilled_deficit_kwh: float

    @property
    def is_ready(self) -> bool:
        return self.unfulfilled_deficit_kwh <= 1e-9

    @property
    def coverage_pct(self) -> float:
        if self.total_energy_needed_kwh <= 0:
            return 100.0
        covered = self.total_energy_needed_kwh - self.unfulfilled_deficit_kwh
        return max(0.0, covered) / self.total_energy_needed_kwh * 100.0


@dataclass(frozen=True)
class StormExecutionReport:
    results: list[EnergyTransferResult]
    transferred_energy_kwh: float
    failed_transfer_count: int
    partial_transfer_count: int


class StormReadinessOrchestrator:
    def __init__(
        self,
        readiness_service: StormReadinessService | None = None,
    ) -> None:
        self.readiness_service = readiness_service or StormReadinessService()

    def create_plan(
        self,
        batteries: list[Battery],
        storm_duration_hours: float,
        transfer_power_kw: float = 5.0,
    ) -> StormReadinessPlan:

        if transfer_power_kw <= 0:
            raise ValueError("transfer_power_kw must be greater than zero.")

        assessments = self.readiness_service.assess_fleet(
            batteries=batteries,
            storm_duration_hours=storm_duration_hours,
        )

        battery_by_id = {battery.battery_id: battery for battery in batteries}

        recipients = sorted(
            (
                a for a in assessments
                if a.participation_eligible and a.needs_energy
            ),
            key=lambda a: a.deficit_kwh,
            reverse=True,
        )

        donors = sorted(
            (
                a for a in assessments
                if (
                    a.participation_eligible
                    and a.can_provide_energy
                    and battery_by_id[a.battery_id].health == BatteryHealth.HEALTHY
                )
            ),
            key=lambda a: a.safe_surplus_kwh,
            reverse=True,
        )

        total_needed = sum(a.deficit_kwh for a in recipients)
        total_surplus = sum(a.safe_surplus_kwh for a in donors)

        donor_remaining = {
            donor.battery_id: donor.safe_surplus_kwh
            for donor in donors
        }

        transfers: list[EnergyTransfer] = []

        for recipient in recipients:
            remaining_need = recipient.deficit_kwh

            for donor in donors:
                if remaining_need <= 1e-9:
                    break

                available = donor_remaining[donor.battery_id]
                if available <= 1e-9:
                    continue

                transfer_energy = min(remaining_need, available)

                transfers.append(
                    EnergyTransfer(
                        donor_battery_id=donor.battery_id,
                        recipient_battery_id=recipient.battery_id,
                        energy_kwh=transfer_energy,
                        power_kw=transfer_power_kw,
                        duration_hours=transfer_energy / transfer_power_kw,
                    )
                )

                donor_remaining[donor.battery_id] -= transfer_energy
                remaining_need -= transfer_energy

        total_planned_transfer = sum(t.energy_kwh for t in transfers)
        unfulfilled_deficit = max(
            0.0,
            total_needed - total_planned_transfer,
        )

        load_recommendations = self._build_load_recommendations(
            assessments=assessments,
            planned_transfer_by_battery=self._planned_incoming_energy(transfers),
            storm_duration_hours=storm_duration_hours,
        )

        return StormReadinessPlan(
            assessments=assessments,
            transfers=transfers,
            load_recommendations=load_recommendations,
            total_energy_needed_kwh=total_needed,
            total_safe_surplus_kwh=total_surplus,
            total_planned_transfer_kwh=total_planned_transfer,
            unfulfilled_deficit_kwh=unfulfilled_deficit,
        )

    def execute_plan(
        self,
        fleet: Fleet,
        grid: Grid,
        plan: StormReadinessPlan,
    ) -> StormExecutionReport:

        results = [
            fleet.execute_energy_transfer(transfer, grid)
            for transfer in plan.transfers
        ]

        return StormExecutionReport(
            results=results,
            transferred_energy_kwh=sum(
                result.transferred_energy_kwh for result in results
            ),
            failed_transfer_count=sum(
                result.status.value == "failed" for result in results
            ),
            partial_transfer_count=sum(
                result.status.value == "partial" for result in results
            ),
        )

    def replan(
        self,
        fleet: Fleet,
        storm_duration_hours: float,
        transfer_power_kw: float = 5.0,
    ) -> StormReadinessPlan:
        return self.create_plan(
            batteries=fleet.batteries,
            storm_duration_hours=storm_duration_hours,
            transfer_power_kw=transfer_power_kw,
        )

    @staticmethod
    def _planned_incoming_energy(
        transfers: list[EnergyTransfer],
    ) -> dict[str, float]:
        incoming: dict[str, float] = {}
        for transfer in transfers:
            incoming[transfer.recipient_battery_id] = (
                incoming.get(transfer.recipient_battery_id, 0.0)
                + transfer.energy_kwh
            )
        return incoming

    @staticmethod
    def _build_load_recommendations(
        assessments: list[BatteryStormAssessment],
        planned_transfer_by_battery: dict[str, float],
        storm_duration_hours: float,
    ) -> list[LoadManagementRecommendation]:

        recommendations: list[LoadManagementRecommendation] = []

        for assessment in assessments:
            if not assessment.participation_eligible:
                continue

            incoming = planned_transfer_by_battery.get(
                assessment.battery_id,
                0.0,
            )

            available_energy = (
                assessment.current_energy_kwh + incoming
            )

            reserve_energy = (
                assessment.required_energy_kwh
                - assessment.current_energy_kwh
            )

            # If the battery already has enough energy for its modeled
            # requirement, its current load is sustainable under this model.
            if assessment.deficit_kwh <= incoming + 1e-9:
                continue

            reserve_energy = max(0.0, reserve_energy)

            recommended_max_load = max(
                0.0,
                (
                    available_energy
                    - reserve_energy
                )
                / storm_duration_hours
            )

            reduction = max(
                0.0,
                assessment.current_energy_kwh
                / storm_duration_hours
                - recommended_max_load,
            )

            if recommended_max_load < assessment.current_energy_kwh / storm_duration_hours:
                recommendations.append(
                    LoadManagementRecommendation(
                        battery_id=assessment.battery_id,
                        current_load_kw=0.0,
                        recommended_max_load_kw=round(recommended_max_load, 4),
                        reduction_kw=round(reduction, 4),
                        storm_duration_hours=storm_duration_hours,
                    )
                )

        return recommendations
