from app.domain.battery import (
    Battery,
    BatteryHealth,
    BatterySpecs,
    BatteryState,
    BatteryStatus,
)
from app.domain.grid import Grid, GridConfig


def create_battery(battery_id, soc):
    return Battery(
        battery_id=battery_id,
        home_id=f"HOME-{battery_id}",
        specs=BatterySpecs(),
        state=BatteryState(
            soc=soc,
            health=BatteryHealth.HEALTHY,
            status=BatteryStatus.AVAILABLE,
            home_load_kw=2.0,
            backup_reserve_pct=0.30,
        ),
    )


def test_grid_collects_and_distributes_energy():
    donor = create_battery("BASE-001", 0.80)
    recipient = create_battery("BASE-002", 0.40)

    grid = Grid()

    collection = grid.collect_energy(
        donor=donor,
        energy_kwh=5.0,
        power_kw=5.0,
    )

    assert collection.status == "completed"
    assert collection.collected_energy_kwh == 5.0
    assert grid.available_energy_kwh == 5.0

    distribution = grid.distribute_energy(
        recipient=recipient,
        energy_kwh=5.0,
        power_kw=5.0,
    )

    assert distribution.status == "completed"
    assert distribution.delivered_energy_kwh == 5.0

    assert donor.energy_kwh < 39.2 * 0.80
    assert recipient.energy_kwh > 39.2 * 0.40
    assert grid.available_energy_kwh == 0.0


def test_grid_rejects_unavailable_donor():
    donor = create_battery("BASE-001", 0.80)
    donor.mark_offline()

    grid = Grid()

    result = grid.collect_energy(
        donor=donor,
        energy_kwh=5.0,
        power_kw=5.0,
    )

    assert result.status == "failed"
    assert result.collected_energy_kwh == 0.0
    assert grid.available_energy_kwh == 0.0


def test_grid_transfer_efficiency():
    donor = create_battery("BASE-001", 0.80)
    recipient = create_battery("BASE-002", 0.40)

    grid = Grid(
        GridConfig(
            transfer_efficiency=0.90,
        )
    )

    collection = grid.collect_energy(
        donor=donor,
        energy_kwh=10.0,
        power_kw=5.0,
    )

    assert collection.status == "completed"

    # 10 kWh collected from donor × 90% efficiency
    # = 9 kWh available in the shared grid pool.
    assert grid.available_energy_kwh == 9.0

    distribution = grid.distribute_energy(
        recipient=recipient,
        energy_kwh=9.0,
        power_kw=5.0,
    )

    assert distribution.status == "completed"
    assert distribution.delivered_energy_kwh == 9.0
    assert grid.available_energy_kwh == 0.0