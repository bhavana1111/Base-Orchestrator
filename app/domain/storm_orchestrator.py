from dataclasses import dataclass

from .battery import Battery, BatteryHealth
from .fleet import Fleet
from .grid import Grid
from .storm_readiness import (
    BatteryStormAssessment,
    StormReadinessService,
)

EPSILON = 1e-9


@dataclass(frozen=True)
class LoadManagementRecommendation:
    battery_id: str
    current_load_kw: float
    recommended_max_load_kw: float
    reduction_kw: float
    storm_duration_hours: float


@dataclass(frozen=True)
class GridEnergyContribution:
    """
    Energy a battery can safely contribute to the shared grid pool.

    This is intentionally not a donor -> recipient transfer.
    The grid is the aggregation point for fleet energy.
    """

    battery_id: str
    energy_kwh: float
    power_kw: float
    duration_hours: float


@dataclass(frozen=True)
class GridEnergyDistribution:
    """
    Energy planned from the shared grid pool to a recipient battery.

    The source is the grid pool, not another battery.
    """

    battery_id: str
    energy_kwh: float
    power_kw: float
    duration_hours: float


@dataclass(frozen=True)
class StormReadinessPlan:
    assessments: list[BatteryStormAssessment]
    grid_contributions: list[GridEnergyContribution]
    grid_distributions: list[GridEnergyDistribution]
    load_recommendations: list[LoadManagementRecommendation]

    total_energy_needed_kwh: float
    total_safe_surplus_kwh: float
    total_grid_energy_kwh: float
    total_distributed_energy_kwh: float
    unfulfilled_deficit_kwh: float

    @property
    def is_ready(self) -> bool:
        return self.unfulfilled_deficit_kwh <= EPSILON

    @property
    def coverage_pct(self) -> float:
        if self.total_energy_needed_kwh <= EPSILON:
            return 100.0

        covered = (
            self.total_energy_needed_kwh
            - self.unfulfilled_deficit_kwh
        )

        return (
            max(0.0, covered)
            / self.total_energy_needed_kwh
            * 100.0
        )

    @property
    def total_planned_transfer_kwh(self) -> float:
        """Backward-compatible name for the distributed grid energy."""
        return self.total_distributed_energy_kwh

    @property
    def load_manageable_batteries(
        self,
    ) -> list[BatteryStormAssessment]:
        return [
            assessment
            for assessment in self.assessments
            if (
                assessment.participation_eligible
                and assessment.can_manage_with_load
            )
        ]

    @property
    def recipient_batteries(
        self,
    ) -> list[BatteryStormAssessment]:
        return [
            assessment
            for assessment in self.assessments
            if assessment.needs_energy
        ]

    @property
    def donor_batteries(
        self,
    ) -> list[BatteryStormAssessment]:
        """
        Return batteries eligible to contribute to the grid pool.

        Recipients are explicitly excluded. A battery must first
        satisfy its own storm requirement before it can contribute.
        """

        recipient_ids = {
            assessment.battery_id
            for assessment in self.recipient_batteries
        }

        return [
            assessment
            for assessment in self.assessments
            if (
                assessment.battery_id not in recipient_ids
                and assessment.participation_eligible
                and assessment.can_provide_energy
            )
        ]


@dataclass(frozen=True)
class StormExecutionReport:
    """
    Execution report for the grid-pool orchestration model.

    Actual grid collection/distribution execution is implemented by
    Grid in the next layer update.
    """

    results: list[object]
    collected_energy_kwh: float
    distributed_energy_kwh: float
    failed_operation_count: int
    partial_operation_count: int


class StormReadinessOrchestrator:
    def __init__(
        self,
        readiness_service: StormReadinessService | None = None,
    ) -> None:
        self.readiness_service = (
            readiness_service
            or StormReadinessService()
        )

    def create_plan(
        self,
        batteries: list[Battery],
        storm_duration_hours: float,
        transfer_power_kw: float = 5.0,
    ) -> StormReadinessPlan:
        """
        Build a fleet-level storm preparation plan.

        Flow:
        1. Assess every battery for the requested storm duration.
        2. Identify recipients that cannot survive at their current load.
        3. Remove recipients from the donor candidate pool.
        4. Ask remaining healthy batteries how much safe surplus
           they can contribute to the shared grid pool.
        5. Aggregate those contributions into one grid energy pool.
        6. Distribute the grid pool to recipients according to
           recipient priority.
        7. Calculate post-distribution load recommendations.
        """

        if storm_duration_hours <= 0:
            raise ValueError(
                "storm_duration_hours must be greater than 0."
            )

        if transfer_power_kw <= 0:
            raise ValueError(
                "transfer_power_kw must be greater than zero."
            )

        assessments = self.readiness_service.assess_fleet(
            batteries=batteries,
            storm_duration_hours=storm_duration_hours,
        )

        battery_by_id = {
            battery.battery_id: battery
            for battery in batteries
        }

        # ---------------------------------------------------------
        # STEP 1
        # Identify recipients first.
        #
        # A recipient is a battery that cannot survive the storm
        # at its current load, even though it is otherwise eligible.
        # ---------------------------------------------------------

        recipients = [
            assessment
            for assessment in assessments
            if assessment.needs_energy
        ]

        recipient_ids = {
            assessment.battery_id
            for assessment in recipients
        }

        # ---------------------------------------------------------
        # STEP 2
        # Remove recipients from the donor candidate pool.
        #
        # We never ask a battery that needs energy to contribute
        # energy to the grid.
        # ---------------------------------------------------------

        donor_candidates = [
            assessment
            for assessment in assessments
            if (
                assessment.battery_id not in recipient_ids
                and assessment.participation_eligible
                and battery_by_id[
                    assessment.battery_id
                ].health == BatteryHealth.HEALTHY
                and assessment.can_provide_energy
            )
        ]

        # Highest safe contribution first makes the pool deterministic
        # and uses fewer contributing batteries for the MVP.
        donors = sorted(
            donor_candidates,
            key=lambda assessment: (
                assessment.safe_surplus_kwh,
                assessment.battery_id,
            ),
            reverse=True,
        )

        # ---------------------------------------------------------
        # STEP 3
        # Aggregate safe donor energy into the shared grid pool.
        #
        # There is intentionally NO donor -> recipient pairing here.
        # ---------------------------------------------------------

        total_needed = sum(
            assessment.deficit_kwh
            for assessment in recipients
        )

        total_surplus = sum(
            assessment.safe_surplus_kwh
            for assessment in donors
        )

        grid_contributions = [
            GridEnergyContribution(
                battery_id=donor.battery_id,
                energy_kwh=round(
                    donor.safe_surplus_kwh,
                    4,
                ),
                power_kw=transfer_power_kw,
                duration_hours=(
                    donor.safe_surplus_kwh
                    / transfer_power_kw
                ),
            )
            for donor in donors
            if donor.safe_surplus_kwh > EPSILON
        ]

        total_grid_energy = sum(
            contribution.energy_kwh
            for contribution in grid_contributions
        )

        # ---------------------------------------------------------
        # STEP 4
        # Determine how the shared grid pool should be distributed.
        #
        # Priority:
        #   1. Larger energy deficit
        #   2. Larger required load reduction
        #   3. Battery id for deterministic ordering
        #
        # This keeps the decision fleet-level while allowing the
        # load-management recommendation to influence priority.
        # ---------------------------------------------------------

        recipients = sorted(
            recipients,
            key=lambda assessment: (
                assessment.deficit_kwh,
                max(
                    0.0,
                    assessment.current_home_load_kw
                    - assessment.sustainable_load_kw,
                ),
                assessment.battery_id,
            ),
            reverse=True,
        )

        grid_remaining = total_grid_energy
        grid_distributions: list[GridEnergyDistribution] = []

        for recipient in recipients:
            if grid_remaining <= EPSILON:
                break

            distribution_energy = min(
                recipient.deficit_kwh,
                grid_remaining,
            )

            if distribution_energy <= EPSILON:
                continue

            grid_distributions.append(
                GridEnergyDistribution(
                    battery_id=recipient.battery_id,
                    energy_kwh=round(
                        distribution_energy,
                        4,
                    ),
                    power_kw=transfer_power_kw,
                    duration_hours=(
                        distribution_energy
                        / transfer_power_kw
                    ),
                )
            )

            grid_remaining -= distribution_energy

        total_distributed = sum(
            distribution.energy_kwh
            for distribution in grid_distributions
        )

        unfulfilled_deficit = max(
            0.0,
            total_needed - total_distributed,
        )

        # ---------------------------------------------------------
        # STEP 5
        # Calculate load recommendations using the energy that
        # each recipient will receive from the shared grid pool.
        # ---------------------------------------------------------

        planned_incoming = (
            self._planned_incoming_energy(
                grid_distributions
            )
        )

        load_recommendations = (
            self._build_load_recommendations(
                assessments=assessments,
                planned_incoming_by_battery=planned_incoming,
                storm_duration_hours=storm_duration_hours,
            )
        )

        return StormReadinessPlan(
            assessments=assessments,
            grid_contributions=grid_contributions,
            grid_distributions=grid_distributions,
            load_recommendations=load_recommendations,
            total_energy_needed_kwh=round(
                total_needed,
                4,
            ),
            total_safe_surplus_kwh=round(
                total_surplus,
                4,
            ),
            total_grid_energy_kwh=round(
                total_grid_energy,
                4,
            ),
            total_distributed_energy_kwh=round(
                total_distributed,
                4,
            ),
            unfulfilled_deficit_kwh=round(
                unfulfilled_deficit,
                4,
            ),
        )

    def execute_plan(
        self,
        fleet: Fleet,
        grid: Grid,
        plan: StormReadinessPlan,
    ) -> StormExecutionReport:
        """
        Execute the fleet-level grid plan.

        Energy flow is modeled as:

            donor batteries -> shared grid pool -> recipients

        There is intentionally no donor-to-recipient pairing.
        """

        # Always start execution with an empty pool for this plan.
        grid.reset_pool()

        results: list[object] = []
        collected_energy_kwh = 0.0
        distributed_energy_kwh = 0.0
        failed_operation_count = 0
        partial_operation_count = 0

        # ---------------------------------------------------------
        # STEP 1
        # Collect the planned safe energy from donor batteries
        # into the shared grid pool.
        # ---------------------------------------------------------

        for contribution in plan.grid_contributions:
            donor = fleet.get_battery(
                contribution.battery_id
            )

            if donor is None:
                failed_operation_count += 1
                results.append(
                    {
                        "operation": "collect",
                        "battery_id": contribution.battery_id,
                        "status": "failed",
                        "reason": "Battery not found in fleet.",
                    }
                )
                continue

            result = grid.collect_energy(
                donor=donor,
                energy_kwh=contribution.energy_kwh,
                power_kw=contribution.power_kw,
            )

            results.append(result)
            collected_energy_kwh += result.collected_energy_kwh

            if result.status == "failed":
                failed_operation_count += 1
            elif result.status == "partial":
                partial_operation_count += 1

        # ---------------------------------------------------------
        # STEP 2
        # Distribute the aggregated grid energy to recipients.
        # The source is the grid pool, not a specific donor.
        # ---------------------------------------------------------

        for distribution in plan.grid_distributions:
            recipient = fleet.get_battery(
                distribution.battery_id
            )

            if recipient is None:
                failed_operation_count += 1
                results.append(
                    {
                        "operation": "distribute",
                        "battery_id": distribution.battery_id,
                        "status": "failed",
                        "reason": "Battery not found in fleet.",
                    }
                )
                continue

            result = grid.distribute_energy(
                recipient=recipient,
                energy_kwh=distribution.energy_kwh,
                power_kw=distribution.power_kw,
            )

            results.append(result)
            distributed_energy_kwh += result.delivered_energy_kwh

            if result.status == "failed":
                failed_operation_count += 1
            elif result.status == "partial":
                partial_operation_count += 1

        return StormExecutionReport(
            results=results,
            collected_energy_kwh=round(
                collected_energy_kwh,
                4,
            ),
            distributed_energy_kwh=round(
                distributed_energy_kwh,
                4,
            ),
            failed_operation_count=failed_operation_count,
            partial_operation_count=partial_operation_count,
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
        distributions: list[GridEnergyDistribution],
    ) -> dict[str, float]:
        incoming: dict[str, float] = {}

        for distribution in distributions:
            incoming[distribution.battery_id] = (
                incoming.get(
                    distribution.battery_id,
                    0.0,
                )
                + distribution.energy_kwh
            )

        return incoming

    @staticmethod
    def _build_load_recommendations(
        assessments: list[BatteryStormAssessment],
        planned_incoming_by_battery: dict[str, float],
        storm_duration_hours: float,
    ) -> list[LoadManagementRecommendation]:
        recommendations: list[
            LoadManagementRecommendation
        ] = []

        for assessment in assessments:
            if not assessment.participation_eligible:
                continue

            incoming = planned_incoming_by_battery.get(
                assessment.battery_id,
                0.0,
            )

            final_energy_kwh = (
                assessment.current_energy_kwh
                + incoming
            )

            # Preserve the battery's reserve/minimum protected energy.
            protected_energy_kwh = max(
                assessment.required_energy_kwh
                - (
                    assessment.current_home_load_kw
                    * storm_duration_hours
                ),
                0.0,
            )

            usable_energy_kwh = max(
                0.0,
                final_energy_kwh
                - protected_energy_kwh,
            )

            recommended_max_load_kw = (
                usable_energy_kwh
                / storm_duration_hours
            )

            # Never recommend increasing the home's current load.
            recommended_max_load_kw = min(
                recommended_max_load_kw,
                assessment.current_home_load_kw,
            )

            reduction_kw = max(
                0.0,
                assessment.current_home_load_kw
                - recommended_max_load_kw,
            )

            if reduction_kw > EPSILON:
                recommendations.append(
                    LoadManagementRecommendation(
                        battery_id=assessment.battery_id,
                        current_load_kw=round(
                            assessment.current_home_load_kw,
                            4,
                        ),
                        recommended_max_load_kw=round(
                            recommended_max_load_kw,
                            4,
                        ),
                        reduction_kw=round(
                            reduction_kw,
                            4,
                        ),
                        storm_duration_hours=(
                            storm_duration_hours
                        ),
                    )
                )

        return recommendations
