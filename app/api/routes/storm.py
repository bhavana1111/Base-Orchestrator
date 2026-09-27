from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domain.fleet import Fleet
from app.domain.grid import Grid
from app.domain.storm_orchestrator import StormReadinessOrchestrator
from app.domain.battery import BatteryHealth, BatteryStatus, BatterySpecs, BatteryState, Battery

router = APIRouter(prefix="/api/storm", tags=["storm"])

fleet = Fleet(
    fleet_id="FLEET-001",
    batteries=[],
)

_specs = BatterySpecs()
for index in range(1, 101):
    soc = 0.40 + ((index - 1) % 10) * 0.05
    home_load_kw = 2.0 + ((index - 1) % 10) * 0.5

    health = BatteryHealth.DEGRADED if index in {20, 40, 60, 80} else BatteryHealth.HEALTHY
    status = BatteryStatus.OFFLINE if index in {25, 50, 75, 100} else BatteryStatus.AVAILABLE

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


class StormPlanRequest(BaseModel):
    storm_duration_hours: float = Field(gt=0)
    transfer_power_kw: float = Field(default=5.0, gt=0)


class ExecutePlanRequest(StormPlanRequest):
    pass


def _plan_response(plan):
    return {
        "ready": plan.is_ready,
        "coverage_pct": round(plan.coverage_pct, 2),
        "total_energy_needed_kwh": round(plan.total_energy_needed_kwh, 3),
        "total_safe_surplus_kwh": round(plan.total_safe_surplus_kwh, 3),
        "total_planned_transfer_kwh": round(plan.total_planned_transfer_kwh, 3),
        "unfulfilled_deficit_kwh": round(plan.unfulfilled_deficit_kwh, 3),
        "assessments": [
            {
                "battery_id": a.battery_id,
                "current_energy_kwh": round(a.current_energy_kwh, 3),
                "required_energy_kwh": round(a.required_energy_kwh, 3),
                "deficit_kwh": round(a.deficit_kwh, 3),
                "safe_surplus_kwh": round(a.safe_surplus_kwh, 3),
                "unachievable_energy_kwh": round(a.unachievable_energy_kwh, 3),
                "participation_eligible": a.participation_eligible,
            }
            for a in plan.assessments
        ],
        "transfers": [
            {
                "donor_battery_id": t.donor_battery_id,
                "recipient_battery_id": t.recipient_battery_id,
                "energy_kwh": round(t.energy_kwh, 3),
                "power_kw": round(t.power_kw, 3),
                "duration_hours": round(t.duration_hours, 3),
            }
            for t in plan.transfers
        ],
        "load_recommendations": [
            {
                "battery_id": r.battery_id,
                "current_load_kw": r.current_load_kw,
                "recommended_max_load_kw": r.recommended_max_load_kw,
                "reduction_kw": r.reduction_kw,
                "storm_duration_hours": r.storm_duration_hours,
            }
            for r in plan.load_recommendations
        ],
    }


@router.post("/plan")
def create_storm_plan(request: StormPlanRequest):
    plan = orchestrator.create_plan(
        batteries=fleet.batteries,
        storm_duration_hours=request.storm_duration_hours,
        transfer_power_kw=request.transfer_power_kw,
    )
    return _plan_response(plan)


@router.post("/execute")
def execute_storm_plan(request: StormPlanRequest):
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
            "transferred_energy_kwh": round(report.transferred_energy_kwh, 3),
            "failed_transfer_count": report.failed_transfer_count,
            "partial_transfer_count": report.partial_transfer_count,
            "results": [
                {
                    "donor_battery_id": r.donor_battery_id,
                    "recipient_battery_id": r.recipient_battery_id,
                    "requested_energy_kwh": round(r.requested_energy_kwh, 3),
                    "transferred_energy_kwh": round(r.transferred_energy_kwh, 3),
                    "status": r.status.value,
                    "reason": r.reason,
                }
                for r in report.results
            ],
        },
    }


@router.post("/replan")
def replan(request: StormPlanRequest):
    plan = orchestrator.replan(
        fleet=fleet,
        storm_duration_hours=request.storm_duration_hours,
        transfer_power_kw=request.transfer_power_kw,
    )
    return _plan_response(plan)
