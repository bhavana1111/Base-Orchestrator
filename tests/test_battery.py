import pytest

from app.domain.battery import Battery
from app.domain.battery_health import BatteryHealth
from app.domain.battery_specs import BatterySpecs
from app.domain.battery_state import BatteryState
from app.domain.battery_status import BatteryStatus


def create_battery() -> Battery:
    specs = BatterySpecs(
        capacity_kwh=39.2,
        max_charge_kw=11.0,
        max_discharge_kw=11.0,
        min_soc=0.20,
        max_soc=0.95,
    )
    state = BatteryState(
        soc=0.50,
        health=BatteryHealth.HEALTHY,
        status=BatteryStatus.AVAILABLE,
        home_load_kw=2.5,
        backup_reserve_pct=0.40,
    )
    return Battery(
        battery_id="BASE-001",
        home_id="HOME-001",
        specs=specs,
        state=state,
    )


def test_battery_creation():
    battery = create_battery()
    assert battery.battery_id == "BASE-001"
    assert battery.home_id == "HOME-001"
    assert battery.specs.capacity_kwh == pytest.approx(39.2)
    assert battery.soc == pytest.approx(0.50)


def test_battery_is_healthy_and_available_by_default():
    battery = create_battery()
    assert battery.health == BatteryHealth.HEALTHY
    assert battery.status == BatteryStatus.AVAILABLE
    assert battery.is_available is True


def test_battery_can_be_marked_degraded():
    battery = create_battery()
    battery.mark_degraded()
    assert battery.health == BatteryHealth.DEGRADED
    assert battery.is_available is True


def test_battery_can_be_marked_failed():
    battery = create_battery()
    battery.mark_failed()
    assert battery.health == BatteryHealth.FAILED
    assert battery.status == BatteryStatus.OFFLINE
    assert battery.is_available is False


def test_failed_battery_cannot_operate():
    battery = create_battery()
    battery.mark_failed()
    with pytest.raises(RuntimeError):
        battery.charge(power_kw=5, duration_hours=1)


def test_offline_battery_cannot_operate():
    battery = create_battery()
    battery.mark_offline()
    with pytest.raises(RuntimeError):
        battery.discharge(power_kw=5, duration_hours=1)


def test_battery_can_be_marked_available_again():
    battery = create_battery()
    battery.mark_offline()
    battery.mark_available()
    assert battery.status == BatteryStatus.AVAILABLE
    assert battery.is_available is True


def test_battery_can_be_marked_healthy_again():
    battery = create_battery()
    battery.mark_failed()
    battery.mark_healthy()
    battery.mark_available()
    assert battery.health == BatteryHealth.HEALTHY
    assert battery.status == BatteryStatus.AVAILABLE


def test_home_load_and_backup_reserve():
    battery = create_battery()
    assert battery.home_load_kw == pytest.approx(2.5)
    assert battery.backup_reserve_pct == pytest.approx(0.40)


def test_home_load_can_be_updated():
    battery = create_battery()
    battery.update_home_load(4.0)
    assert battery.home_load_kw == pytest.approx(4.0)


def test_backup_reserve_can_be_updated():
    battery = create_battery()
    battery.update_backup_reserve(0.50)
    assert battery.backup_reserve_pct == pytest.approx(0.50)


def test_energy_calculation():
    battery = create_battery()
    assert battery.energy_kwh == pytest.approx(19.6)


def test_available_charge_energy():
    battery = create_battery()
    assert battery.available_charge_kwh == pytest.approx(39.2 * 0.45)


def test_available_discharge_energy():
    battery = create_battery()
    assert battery.available_discharge_kwh == pytest.approx(39.2 * 0.30)


def test_battery_charge():
    battery = create_battery()
    energy_added = battery.charge(power_kw=11, duration_hours=1)
    assert energy_added == pytest.approx(11)
    assert battery.energy_kwh == pytest.approx(30.6)
    assert battery.soc == pytest.approx(30.6 / 39.2)
    assert battery.status == BatteryStatus.CHARGING


def test_charge_respects_max_power():
    battery = create_battery()
    assert battery.charge(power_kw=20, duration_hours=1) == pytest.approx(11)


def test_battery_cannot_charge_above_max_soc():
    battery = create_battery()
    energy_added = battery.charge(power_kw=11, duration_hours=5)
    assert energy_added == pytest.approx(39.2 * 0.45)
    assert battery.soc == pytest.approx(0.95)


def test_battery_discharge():
    battery = create_battery()
    energy_removed = battery.discharge(power_kw=11, duration_hours=1)
    assert energy_removed == pytest.approx(11)
    assert battery.energy_kwh == pytest.approx(8.6)
    assert battery.soc == pytest.approx(8.6 / 39.2)
    assert battery.status == BatteryStatus.DISCHARGING


def test_discharge_respects_max_power():
    battery = create_battery()
    assert battery.discharge(power_kw=20, duration_hours=1) == pytest.approx(11)


def test_battery_cannot_discharge_below_min_soc():
    battery = create_battery()
    energy_removed = battery.discharge(power_kw=11, duration_hours=2)
    assert energy_removed == pytest.approx(39.2 * 0.30)
    assert battery.soc == pytest.approx(0.20)


@pytest.mark.parametrize(
    "operation",
    ["charge", "discharge"],
)
def test_negative_power_is_rejected(operation):
    battery = create_battery()
    with pytest.raises(ValueError):
        getattr(battery, operation)(power_kw=-5, duration_hours=1)


@pytest.mark.parametrize(
    "operation",
    ["charge", "discharge"],
)
def test_non_positive_duration_is_rejected(operation):
    battery = create_battery()
    with pytest.raises(ValueError):
        getattr(battery, operation)(power_kw=5, duration_hours=0)


def test_negative_home_load_is_rejected():
    battery = create_battery()
    with pytest.raises(ValueError):
        battery.update_home_load(-1)


def test_invalid_backup_reserve_is_rejected():
    battery = create_battery()
    with pytest.raises(ValueError):
        battery.update_backup_reserve(1.5)
