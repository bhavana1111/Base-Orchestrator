from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.domain.battery_factory import create_fabricated_batteries
from app.domain.fleet import Fleet


router = APIRouter(
    prefix="/api/fleet",
    tags=["fleet"],
)


# Temporary in-memory fleet for the UI prototype.
# This will later be replaced by the application/service layer.
fleet = Fleet(
    fleet_id="FLEET-001",
    batteries=create_fabricated_batteries(100),
)


class FleetSummaryResponse(BaseModel):
    fleet_id: str
    battery_count: int
    available_batteries: int
    unavailable_batteries: int
    total_capacity_kwh: float
    total_energy_kwh: float
    average_soc: float
    available_charge_kw: float
    available_discharge_kw: float


class BatterySummaryResponse(BaseModel):
    battery_id: str
    home_id: str
    soc: float
    health: str
    status: str
    home_load_kw: float
    backup_reserve_pct: float


class BatteryDetailResponse(BatterySummaryResponse):
    capacity_kwh: float
    energy_kwh: float
    max_charge_kw: float
    max_discharge_kw: float
    available_charge_kwh: float
    available_discharge_kwh: float
    is_available: bool


@router.get("", response_model=FleetSummaryResponse)
def get_fleet() -> FleetSummaryResponse:
    return FleetSummaryResponse(
        fleet_id=fleet.fleet_id,
        battery_count=fleet.battery_count,
        available_batteries=len(fleet.available_batteries),
        unavailable_batteries=len(fleet.unavailable_batteries),
        total_capacity_kwh=fleet.total_capacity_kwh,
        total_energy_kwh=fleet.total_energy_kwh,
        average_soc=fleet.average_soc,
        available_charge_kw=fleet.available_charge_kw,
        available_discharge_kw=fleet.available_discharge_kw,
    )


@router.get("/batteries", response_model=list[BatterySummaryResponse])
def get_batteries() -> list[BatterySummaryResponse]:
    return [
        BatterySummaryResponse(
            battery_id=battery.battery_id,
            home_id=battery.home_id,
            soc=battery.soc,
            health=battery.health.value,
            status=battery.status.value,
            home_load_kw=battery.home_load_kw,
            backup_reserve_pct=battery.backup_reserve_pct,
        )
        for battery in fleet.batteries
    ]


@router.get(
    "/batteries/{battery_id}",
    response_model=BatteryDetailResponse,
)
def get_battery(battery_id: str) -> BatteryDetailResponse:
    battery = fleet.get_battery(battery_id)

    if battery is None:
        raise HTTPException(
            status_code=404,
            detail=f"Battery {battery_id} not found.",
        )

    return BatteryDetailResponse(
        battery_id=battery.battery_id,
        home_id=battery.home_id,
        soc=battery.soc,
        health=battery.health.value,
        status=battery.status.value,
        home_load_kw=battery.home_load_kw,
        backup_reserve_pct=battery.backup_reserve_pct,
        capacity_kwh=battery.specs.capacity_kwh,
        energy_kwh=battery.energy_kwh,
        max_charge_kw=battery.specs.max_charge_kw,
        max_discharge_kw=battery.specs.max_discharge_kw,
        available_charge_kwh=battery.available_charge_kwh,
        available_discharge_kwh=battery.available_discharge_kwh,
        is_available=battery.is_available,
    )
