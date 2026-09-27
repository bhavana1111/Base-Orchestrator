import pytest

from app.domain.battery import Battery
from app.domain.battery_factory import create_fabricated_batteries
from app.domain.battery_health import BatteryHealth
from app.domain.battery_specs import BatterySpecs
from app.domain.battery_state import BatteryState
from app.domain.battery_status import BatteryStatus
from app.domain.energy_transfer import EnergyTransfer
from app.domain.fleet import Fleet
from app.domain.grid import Grid


def create_fleet(count: int = 100) -> Fleet:
    """Create a deterministic fabricated fleet."""
    batteries = create_fabricated_batteries(count)

    return Fleet(
        fleet_id="FLEET-001",
        batteries=batteries,
    )


# -------------------------------------------------------------------
# Fleet Creation
# -------------------------------------------------------------------


def test_fleet_creation():
    fleet = create_fleet()

    assert fleet.fleet_id == "FLEET-001"
    assert fleet.battery_count == 100


def test_fleet_can_be_created_with_different_sizes():
    fleet = create_fleet(10)

    assert fleet.battery_count == 10


def test_empty_fleet_can_be_created():
    fleet = Fleet(
        fleet_id="EMPTY-FLEET",
        batteries=[],
    )

    assert fleet.battery_count == 0


def test_empty_fleet_id_is_rejected():
    with pytest.raises(ValueError):
        Fleet(
            fleet_id="",
            batteries=[],
        )


# -------------------------------------------------------------------
# Battery Access
# -------------------------------------------------------------------


def test_get_battery():
    fleet = create_fleet()

    battery = fleet.get_battery("BASE-001")

    assert battery is not None
    assert battery.battery_id == "BASE-001"
    assert battery.home_id == "HOME-001"


def test_get_missing_battery_returns_none():
    fleet = create_fleet()

    battery = fleet.get_battery("BASE-999")

    assert battery is None


def test_add_battery():
    fleet = create_fleet(99)

    specs = BatterySpecs(
        capacity_kwh=39.2,
        max_charge_kw=11.0,
        max_discharge_kw=11.0,
        min_soc=0.20,
        max_soc=0.95,
    )

    state = BatteryState(
        soc=0.50,
    )

    battery = Battery(
        battery_id="BASE-100",
        home_id="HOME-100",
        specs=specs,
        state=state,
    )

    fleet.add_battery(battery)

    assert fleet.battery_count == 100
    assert fleet.get_battery("BASE-100") is battery


def test_duplicate_battery_is_rejected():
    fleet = create_fleet()

    duplicate = create_fabricated_batteries(1)[0]

    with pytest.raises(ValueError):
        fleet.add_battery(duplicate)


def test_remove_battery():
    fleet = create_fleet()

    removed = fleet.remove_battery("BASE-001")

    assert removed.battery_id == "BASE-001"
    assert fleet.battery_count == 99
    assert fleet.get_battery("BASE-001") is None


def test_remove_missing_battery_is_rejected():
    fleet = create_fleet()

    with pytest.raises(ValueError):
        fleet.remove_battery("BASE-999")


# -------------------------------------------------------------------
# Available / Unavailable Batteries
# -------------------------------------------------------------------


def test_available_batteries():
    fleet = create_fleet()

    available = fleet.available_batteries

    # Factory creates:
    # 4 offline batteries: 25, 50, 75, 100
    # 2 failed batteries: 30, 90
    # Total unavailable = 6
    #
    # Degraded batteries remain available.
    assert len(available) == 94


def test_unavailable_batteries():
    fleet = create_fleet()

    unavailable = fleet.unavailable_batteries

    assert len(unavailable) == 6


def test_available_and_unavailable_batteries_cover_fleet():
    fleet = create_fleet()

    assert (
        len(fleet.available_batteries)
        + len(fleet.unavailable_batteries)
        == fleet.battery_count
    )


def test_failed_battery_is_not_available():
    fleet = create_fleet()

    battery = fleet.get_battery("BASE-030")

    assert battery is not None
    assert battery.health == BatteryHealth.FAILED
    assert battery.status == BatteryStatus.OFFLINE
    assert battery.is_available is False


def test_offline_battery_is_not_available():
    fleet = create_fleet()

    battery = fleet.get_battery("BASE-025")

    assert battery is not None
    assert battery.status == BatteryStatus.OFFLINE
    assert battery.is_available is False


def test_degraded_battery_can_still_be_available():
    fleet = create_fleet()

    battery = fleet.get_battery("BASE-020")

    assert battery is not None
    assert battery.health == BatteryHealth.DEGRADED
    assert battery.status == BatteryStatus.AVAILABLE
    assert battery.is_available is True


# -------------------------------------------------------------------
# Fleet Aggregation
# -------------------------------------------------------------------


def test_total_capacity():
    fleet = create_fleet()

    assert fleet.total_capacity_kwh == pytest.approx(
        100 * 39.2
    )


def test_total_energy():
    fleet = create_fleet()

    expected = sum(
        battery.energy_kwh
        for battery in fleet.batteries
    )

    assert fleet.total_energy_kwh == pytest.approx(
        expected
    )


def test_average_soc():
    fleet = create_fleet()

    expected = sum(
        battery.soc
        for battery in fleet.batteries
    ) / fleet.battery_count

    assert fleet.average_soc == pytest.approx(
        expected
    )


def test_empty_fleet_average_soc_is_zero():
    fleet = Fleet(
        fleet_id="EMPTY-FLEET",
        batteries=[],
    )

    assert fleet.average_soc == 0.0


def test_available_charge_power():
    fleet = create_fleet()

    expected = (
        len(fleet.available_batteries)
        * 11.0
    )

    assert fleet.available_charge_kw == pytest.approx(
        expected
    )


def test_available_discharge_power():
    fleet = create_fleet()

    expected = (
        len(fleet.available_batteries)
        * 11.0
    )

    assert fleet.available_discharge_kw == pytest.approx(
        expected
    )


def test_empty_fleet_has_zero_capacity():
    fleet = Fleet(
        fleet_id="EMPTY-FLEET",
        batteries=[],
    )

    assert fleet.total_capacity_kwh == 0.0
    assert fleet.total_energy_kwh == 0.0
    assert fleet.available_charge_kw == 0.0
    assert fleet.available_discharge_kw == 0.0


# -------------------------------------------------------------------
# Fleet Charging
# -------------------------------------------------------------------


def test_fleet_can_charge():
    fleet = create_fleet()

    initial_energy = fleet.total_energy_kwh

    actual_power = fleet.charge(
        target_power_kw=100,
        duration_hours=1,
    )

    assert actual_power == pytest.approx(100)
    assert fleet.total_energy_kwh > initial_energy


def test_fleet_charge_updates_battery_state():
    fleet = create_fleet()

    battery = fleet.get_battery("BASE-001")

    assert battery is not None

    initial_soc = battery.soc

    fleet.charge(
        target_power_kw=11,
        duration_hours=1,
    )

    assert battery.soc > initial_soc
    assert battery.status == BatteryStatus.CHARGING


def test_fleet_does_not_charge_unavailable_battery():
    fleet = create_fleet()

    battery = fleet.get_battery("BASE-025")

    assert battery is not None

    initial_soc = battery.soc

    fleet.charge(
        target_power_kw=11,
        duration_hours=1,
    )

    assert battery.soc == pytest.approx(initial_soc)


def test_fleet_charge_distributes_power_across_batteries():
    fleet = create_fleet()

    first = fleet.get_battery("BASE-001")
    second = fleet.get_battery("BASE-002")

    assert first is not None
    assert second is not None

    initial_first_soc = first.soc
    initial_second_soc = second.soc

    actual_power = fleet.charge(
        target_power_kw=22,
        duration_hours=1,
    )

    assert actual_power == pytest.approx(22)

    assert first.soc > initial_first_soc
    assert second.soc > initial_second_soc


# -------------------------------------------------------------------
# Fleet Discharging
# -------------------------------------------------------------------


def test_fleet_can_discharge():
    fleet = create_fleet()

    initial_energy = fleet.total_energy_kwh

    actual_power = fleet.discharge(
        target_power_kw=100,
        duration_hours=1,
    )

    assert actual_power == pytest.approx(100)
    assert fleet.total_energy_kwh < initial_energy


def test_fleet_discharge_updates_battery_state():
    fleet = create_fleet()

    battery = fleet.get_battery("BASE-001")

    assert battery is not None

    initial_soc = battery.soc

    fleet.discharge(
        target_power_kw=11,
        duration_hours=1,
    )

    assert battery.soc < initial_soc
    assert battery.status == BatteryStatus.DISCHARGING


def test_fleet_does_not_discharge_unavailable_battery():
    fleet = create_fleet()

    battery = fleet.get_battery("BASE-025")

    assert battery is not None

    initial_soc = battery.soc

    fleet.discharge(
        target_power_kw=11,
        duration_hours=1,
    )

    assert battery.soc == pytest.approx(initial_soc)


def test_fleet_discharge_distributes_power_across_batteries():
    fleet = create_fleet()

    first = fleet.get_battery("BASE-001")
    second = fleet.get_battery("BASE-002")

    assert first is not None
    assert second is not None

    initial_first_soc = first.soc
    initial_second_soc = second.soc

    actual_power = fleet.discharge(
        target_power_kw=22,
        duration_hours=1,
    )

    assert actual_power == pytest.approx(22)

    assert first.soc < initial_first_soc
    assert second.soc < initial_second_soc


# -------------------------------------------------------------------
# Fleet Energy Transfer
# -------------------------------------------------------------------


def test_fleet_can_execute_energy_transfer():
    fleet = create_fleet()

    donor = fleet.get_battery("BASE-001")
    recipient = fleet.get_battery("BASE-002")

    assert donor is not None
    assert recipient is not None

    initial_donor_energy = donor.energy_kwh
    initial_recipient_energy = recipient.energy_kwh

    transfer = EnergyTransfer(
        donor_battery_id="BASE-001",
        recipient_battery_id="BASE-002",
        energy_kwh=5.0,
        power_kw=5.0,
        duration_hours=1.0,
    )

    grid = Grid()

    result = fleet.execute_energy_transfer(
        transfer=transfer,
        grid=grid,
    )

    assert result.transferred_energy_kwh == pytest.approx(5.0)
    assert donor.energy_kwh < initial_donor_energy
    assert recipient.energy_kwh > initial_recipient_energy


def test_fleet_energy_transfer_updates_correct_batteries():
    fleet = create_fleet()

    donor = fleet.get_battery("BASE-001")
    recipient = fleet.get_battery("BASE-002")
    unrelated = fleet.get_battery("BASE-003")

    assert donor is not None
    assert recipient is not None
    assert unrelated is not None

    initial_donor_energy = donor.energy_kwh
    initial_recipient_energy = recipient.energy_kwh
    initial_unrelated_energy = unrelated.energy_kwh

    transfer = EnergyTransfer(
        donor_battery_id="BASE-001",
        recipient_battery_id="BASE-002",
        energy_kwh=5.0,
        power_kw=5.0,
        duration_hours=1.0,
    )

    grid = Grid()

    fleet.execute_energy_transfer(
        transfer=transfer,
        grid=grid,
    )

    assert donor.energy_kwh < initial_donor_energy
    assert recipient.energy_kwh > initial_recipient_energy
    assert unrelated.energy_kwh == pytest.approx(
        initial_unrelated_energy
    )


def test_fleet_energy_transfer_missing_donor_is_rejected():
    fleet = create_fleet()

    transfer = EnergyTransfer(
        donor_battery_id="BASE-999",
        recipient_battery_id="BASE-002",
        energy_kwh=5.0,
        power_kw=5.0,
        duration_hours=1.0,
    )

    grid = Grid()

    with pytest.raises(ValueError, match="Donor battery"):
        fleet.execute_energy_transfer(
            transfer=transfer,
            grid=grid,
        )


def test_fleet_energy_transfer_missing_recipient_is_rejected():
    fleet = create_fleet()

    transfer = EnergyTransfer(
        donor_battery_id="BASE-001",
        recipient_battery_id="BASE-999",
        energy_kwh=5.0,
        power_kw=5.0,
        duration_hours=1.0,
    )

    grid = Grid()

    with pytest.raises(ValueError, match="Recipient battery"):
        fleet.execute_energy_transfer(
            transfer=transfer,
            grid=grid,
        )


def test_fleet_energy_transfer_with_unavailable_donor():
    fleet = create_fleet()

    donor = fleet.get_battery("BASE-025")

    assert donor is not None
    assert donor.is_available is False

    transfer = EnergyTransfer(
        donor_battery_id="BASE-025",
        recipient_battery_id="BASE-001",
        energy_kwh=5.0,
        power_kw=5.0,
        duration_hours=1.0,
    )

    grid = Grid()

    result = fleet.execute_energy_transfer(
        transfer=transfer,
        grid=grid,
    )

    assert result.transferred_energy_kwh == pytest.approx(0.0)


# -------------------------------------------------------------------
# Fleet Capacity Limits
# -------------------------------------------------------------------


def test_fleet_cannot_charge_above_available_power():
    fleet = create_fleet()

    requested_power = fleet.available_charge_kw + 100

    actual_power = fleet.charge(
        target_power_kw=requested_power,
        duration_hours=1,
    )

    assert actual_power <= fleet.available_charge_kw


def test_fleet_cannot_discharge_above_available_power():
    fleet = create_fleet()

    requested_power = fleet.available_discharge_kw + 100

    actual_power = fleet.discharge(
        target_power_kw=requested_power,
        duration_hours=1,
    )

    assert actual_power <= fleet.available_discharge_kw


# -------------------------------------------------------------------
# Fleet Response When Batteries Become Unavailable
# -------------------------------------------------------------------


def test_available_capacity_changes_when_battery_goes_offline():
    fleet = create_fleet()

    initial_available_power = fleet.available_discharge_kw

    battery = fleet.get_battery("BASE-001")

    assert battery is not None

    battery.mark_offline()

    assert fleet.available_discharge_kw == pytest.approx(
        initial_available_power - 11.0
    )


def test_failed_battery_is_excluded_from_fleet_dispatch():
    fleet = create_fleet()

    battery = fleet.get_battery("BASE-001")

    assert battery is not None

    battery.mark_failed()

    initial_soc = battery.soc

    fleet.discharge(
        target_power_kw=11,
        duration_hours=1,
    )

    assert battery.soc == pytest.approx(initial_soc)
    assert battery.is_available is False


# -------------------------------------------------------------------
# Invalid Inputs
# -------------------------------------------------------------------


def test_negative_charge_target_is_rejected():
    fleet = create_fleet()

    with pytest.raises(ValueError):
        fleet.charge(
            target_power_kw=-100,
            duration_hours=1,
        )


def test_negative_discharge_target_is_rejected():
    fleet = create_fleet()

    with pytest.raises(ValueError):
        fleet.discharge(
            target_power_kw=-100,
            duration_hours=1,
        )


def test_zero_duration_charge_is_rejected():
    fleet = create_fleet()

    with pytest.raises(
        ValueError,
        match="duration_hours must be greater than zero",
    ):
        fleet.charge(
            target_power_kw=10,
            duration_hours=0,
        )


def test_negative_duration_charge_is_rejected():
    fleet = create_fleet()

    with pytest.raises(
        ValueError,
        match="duration_hours must be greater than zero",
    ):
        fleet.charge(
            target_power_kw=10,
            duration_hours=-1,
        )


def test_zero_duration_discharge_is_rejected():
    fleet = create_fleet()

    with pytest.raises(
        ValueError,
        match="duration_hours must be greater than zero",
    ):
        fleet.discharge(
            target_power_kw=10,
            duration_hours=0,
        )


def test_negative_duration_discharge_is_rejected():
    fleet = create_fleet()

    with pytest.raises(
        ValueError,
        match="duration_hours must be greater than zero",
    ):
        fleet.discharge(
            target_power_kw=10,
            duration_hours=-1,
        )


# -------------------------------------------------------------------
# Fleet Construction Validation
# -------------------------------------------------------------------


def test_duplicate_battery_ids_are_rejected_during_creation():
    batteries = create_fabricated_batteries(2)

    batteries[1].battery_id = batteries[0].battery_id

    with pytest.raises(ValueError):
        Fleet(
            fleet_id="FLEET-001",
            batteries=batteries,
        )