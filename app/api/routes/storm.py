from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domain.battery import (
    Battery,
    BatteryHealth,
    BatterySpecs,
    BatteryState,
    BatteryStatus,
)
from app.domain.fleet import Fleet
from app.domain.grid import Grid
from app.domain.storm_orchestrator import StormReadinessOrchestrator

router = APIRouter(prefix="/api/storm", tags=["storm"])


# ---------------------------------------------------------------------------
# Fabricated fleet
# ---------------------------------------------------------------------------

fleet = Fleet(
    fleet_id="FLEET-001",
    batteries=[],
)

_specs = BatterySpecs()

for index in range(1, 101):
    soc = 0.40 + ((index - 1) % 10) * 0.05
    home_load_kw = 2.0 + ((index - 1) % 10) * 0.5

    health = (
        BatteryHealth.DEGRADED
        if index in {20, 40, 60, 80}
        else BatteryHealth.HEALTHY
    )

    status = (
        BatteryStatus.OFFLINE
        if index in {25, 50, 75, 100}
        else BatteryStatus.AVAILABLE
    )

    if index in {30, 90}:
        health = BatteryHealth.FAILED
        status = BatteryStatus.OFFLINE

    fleet.add_battery(
        Battery(
            battery_id=f"BASE-{index:03d}",
            home_id=f"HOME-{index:03d}",
            specs=_specs,
            state=BatteryState(
                soc=soc,
                health=health,
                status=status,
                home_load_kw=home_load_kw,
                backup_reserve_pct=0.30 + ((index - 1) % 6) * 0.05,
            ),
        )
    )


orchestrator = StormReadinessOrchestrator()
grid = Grid()


# ---------------------------------------------------------------------------
# API request models
# ---------------------------------------------------------------------------

class StormPlanRequest(BaseModel):
    storm_duration_hours: float = Field(gt=0)
    transfer_power_kw: float = Field(default=5.0, gt=0)


class ExecutePlanRequest(StormPlanRequest):
    pass


# ---------------------------------------------------------------------------
# Response mapping
# ---------------------------------------------------------------------------

def _plan_response(plan):
    return {
        "ready": plan.is_ready,
        "is_ready": plan.is_ready,
        "coverage_pct": round(plan.coverage_pct, 2),

        # ------------------------------------------------------------------
        # Fleet-level energy summary
        # ------------------------------------------------------------------

        "total_energy_needed_kwh": round(
            plan.total_energy_needed_kwh,
            3,
        ),
        "total_safe_surplus_kwh": round(
            plan.total_safe_surplus_kwh,
            3,
        ),
        "total_grid_energy_kwh": round(
            plan.total_grid_energy_kwh,
            3,
        ),
        "total_distributed_energy_kwh": round(
            plan.total_distributed_energy_kwh,
            3,
        ),
        "total_planned_transfer_kwh": round(
            plan.total_planned_transfer_kwh,
            3,
        ),
        "unfulfilled_deficit_kwh": round(
            plan.unfulfilled_deficit_kwh,
            3,
        ),

        # ------------------------------------------------------------------
        # Fleet-level classifications
        # ------------------------------------------------------------------

        "load_manageable_batteries": [
            {
                "battery_id": assessment.battery_id,
                "current_energy_kwh": round(
                    assessment.current_energy_kwh,
                    3,
                ),
                "current_load_kw": round(
                    assessment.current_home_load_kw,
                    3,
                ),
                "sustainable_load_kw": round(
                    assessment.sustainable_load_kw,
                    3,
                ),
            }
            for assessment in plan.load_manageable_batteries
        ],

        # ------------------------------------------------------------------
        # Recipients
        #
        # Batteries that cannot sustain their storm requirement
        # from their own available energy/load profile.
        # ------------------------------------------------------------------

        "recipients": [
            {
                "battery_id": assessment.battery_id,
                "current_energy_kwh": round(
                    assessment.current_energy_kwh,
                    3,
                ),
                "required_energy_kwh": round(
                    assessment.required_energy_kwh,
                    3,
                ),
                "deficit_kwh": round(
                    assessment.deficit_kwh,
                    3,
                ),
                "current_load_kw": round(
                    assessment.current_home_load_kw,
                    3,
                ),
                "sustainable_load_kw": round(
                    assessment.sustainable_load_kw,
                    3,
                ),
            }
            for assessment in plan.recipient_batteries
        ],

        # ------------------------------------------------------------------
        # Donors
        #
        # Donors are selected only after recipients have been identified.
        # Recipients are therefore excluded from this list.
        # ------------------------------------------------------------------

        "donors": [
            {
                "battery_id": assessment.battery_id,
                "current_energy_kwh": round(
                    assessment.current_energy_kwh,
                    3,
                ),
                "safe_surplus_kwh": round(
                    assessment.safe_surplus_kwh,
                    3,
                ),
            }
            for assessment in plan.donor_batteries
        ],

        # ------------------------------------------------------------------
        # Detailed assessment for every battery
        # ------------------------------------------------------------------

        "assessments": [
            {
                "battery_id": assessment.battery_id,

                "current_energy_kwh": round(
                    assessment.current_energy_kwh,
                    3,
                ),

                "current_load_required_energy_kwh": round(
                    assessment.current_load_required_energy_kwh,
                    3,
                ),

                "required_energy_kwh": round(
                    assessment.required_energy_kwh,
                    3,
                ),

                "deficit_kwh": round(
                    assessment.deficit_kwh,
                    3,
                ),

                "safe_surplus_kwh": round(
                    assessment.safe_surplus_kwh,
                    3,
                ),

                "unachievable_energy_kwh": round(
                    assessment.unachievable_energy_kwh,
                    3,
                ),

                "participation_eligible": (
                    assessment.participation_eligible
                ),

                "current_load_kw": round(
                    assessment.current_home_load_kw,
                    3,
                ),

                "sustainable_load_kw": round(
                    assessment.sustainable_load_kw,
                    3,
                ),

                "can_manage_with_load": (
                    assessment.can_manage_with_load
                ),

                "needs_energy": assessment.needs_energy,

                "can_provide_energy": (
                    assessment.can_provide_energy
                ),

                "is_ready": assessment.is_ready,
            }
            for assessment in plan.assessments
        ],

        # ------------------------------------------------------------------
        # Grid energy contribution plan
        #
        # Donor -> GRID POOL
        # ------------------------------------------------------------------

        "grid_contributions": [
            {
                "battery_id": contribution.battery_id,
                "energy_kwh": round(
                    contribution.energy_kwh,
                    3,
                ),
                "power_kw": round(
                    contribution.power_kw,
                    3,
                ),
                "duration_hours": round(
                    contribution.duration_hours,
                    3,
                ),
            }
            for contribution in plan.grid_contributions
        ],

        # ------------------------------------------------------------------
        # Grid energy distribution plan
        #
        # GRID POOL -> RECIPIENT
        # ------------------------------------------------------------------

        "grid_distributions": [
            {
                "battery_id": distribution.battery_id,
                "energy_kwh": round(
                    distribution.energy_kwh,
                    3,
                ),
                "power_kw": round(
                    distribution.power_kw,
                    3,
                ),
                "duration_hours": round(
                    distribution.duration_hours,
                    3,
                ),
            }
            for distribution in plan.grid_distributions
        ],

        # ------------------------------------------------------------------
        # Load management
        # ------------------------------------------------------------------

        "load_recommendations": [
            {
                "battery_id": recommendation.battery_id,
                "current_load_kw": round(
                    recommendation.current_load_kw,
                    3,
                ),
                "recommended_max_load_kw": round(
                    recommendation.recommended_max_load_kw,
                    3,
                ),
                "reduction_kw": round(
                    recommendation.reduction_kw,
                    3,
                ),
                "storm_duration_hours": (
                    recommendation.storm_duration_hours
                ),
            }
            for recommendation in plan.load_recommendations
        ],
    }


# ---------------------------------------------------------------------------
# Create storm plan
# ---------------------------------------------------------------------------

@router.post("/plan")
def create_storm_plan(request: StormPlanRequest):
    plan = orchestrator.create_plan(
        batteries=fleet.batteries,
        storm_duration_hours=request.storm_duration_hours,
        transfer_power_kw=request.transfer_power_kw,
    )

    return _plan_response(plan)


# ---------------------------------------------------------------------------
# Execute storm plan
# ---------------------------------------------------------------------------

@router.post("/execute")
def execute_storm_plan(request: ExecutePlanRequest):
    plan = orchestrator.create_plan(
        batteries=fleet.batteries,
        storm_duration_hours=request.storm_duration_hours,
        transfer_power_kw=request.transfer_power_kw,
    )

    report = orchestrator.execute_plan(
        fleet=fleet,
        grid=grid,
        plan=plan,
    )

    return {
        "plan": _plan_response(plan),

        "execution": {
            "collected_energy_kwh": round(
                report.collected_energy_kwh,
                3,
            ),
            "distributed_energy_kwh": round(
                report.distributed_energy_kwh,
                3,
            ),
            "failed_operation_count": (
                report.failed_operation_count
            ),
            "partial_operation_count": (
                report.partial_operation_count
            ),

            "grid_energy_pool_kwh": round(
                grid.available_energy_kwh,
                3,
            ),

            "results": report.results,
        },
    }


# ---------------------------------------------------------------------------
# Replan
# ---------------------------------------------------------------------------

@router.post("/replan")
def replan(request: StormPlanRequest):
    plan = orchestrator.replan(
        fleet=fleet,
        storm_duration_hours=request.storm_duration_hours,
        transfer_power_kw=request.transfer_power_kw,
    )

    return _plan_response(plan)