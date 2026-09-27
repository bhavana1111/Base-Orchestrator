from app.domain.battery import (
    Battery,
    BatteryHealth,
    BatterySpecs,
    BatteryState,
    BatteryStatus,
)
from app.domain.storm_readiness import StormReadinessService


def create_battery(battery_id="BASE-001", soc=0.50, home_load_kw=2.0, health=BatteryHealth.HEALTHY, status=BatteryStatus.AVAILABLE):
    return Battery(
        battery_id=battery_id,
        home_id=f"HOME-{battery_id}",
        specs=BatterySpecs(),
        state=BatteryState(
            soc=soc,
            health=health,
            status=status,
            home_load_kw=home_load_kw,
            backup_reserve_pct=0.30,
        ),
    )


def test_battery_with_deficit_is_identified():
    assessment = StormReadinessService().assess_battery(
        create_battery(soc=0.40, home_load_kw=3.0), 4
    )
    assert assessment.needs_energy
    assert assessment.deficit_kwh > 0
    assert assessment.safe_surplus_kwh == 0


def test_battery_with_surplus_is_identified():
    assessment = StormReadinessService().assess_battery(
        create_battery(soc=0.90, home_load_kw=1.0), 4
    )
    assert assessment.can_provide_energy
    assert assessment.safe_surplus_kwh > 0


def test_unavailable_battery_cannot_provide_surplus():
    assessment = StormReadinessService().assess_battery(
        create_battery(soc=0.90, status=BatteryStatus.OFFLINE), 4
    )
    assert not assessment.participation_eligible
    assert assessment.safe_surplus_kwh == 0


def test_failed_battery_cannot_participate():
    assessment = StormReadinessService().assess_battery(
        create_battery(soc=0.90, health=BatteryHealth.FAILED, status=BatteryStatus.OFFLINE), 4
    )
    assert not assessment.participation_eligible


def test_invalid_storm_duration():
    import pytest
    with pytest.raises(ValueError):
        StormReadinessService().assess_battery(create_battery(), 0)
