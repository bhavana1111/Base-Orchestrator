from app.domain.battery import (
    Battery,
    BatteryHealth,
    BatterySpecs,
    BatteryState,
    BatteryStatus,
)
from app.domain.energy_transfer import EnergyTransfer, TransferStatus
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


def test_grid_transfers_energy():
    donor = create_battery("BASE-001", 0.80)
    recipient = create_battery("BASE-002", 0.40)

    result = Grid().execute_transfer(
        donor,
        recipient,
        EnergyTransfer("BASE-001", "BASE-002", 5.0, 5.0, 1.0),
    )

    assert result.status == TransferStatus.COMPLETED
    assert result.transferred_energy_kwh == 5.0
    assert donor.energy_kwh < 39.2 * 0.80
    assert recipient.energy_kwh > 39.2 * 0.40


def test_grid_rejects_unavailable_donor():
    donor = create_battery("BASE-001", 0.80)
    recipient = create_battery("BASE-002", 0.40)
    donor.mark_offline()

    result = Grid().execute_transfer(
        donor, recipient, EnergyTransfer("BASE-001", "BASE-002", 5.0, 5.0, 1.0)
    )

    assert result.status == TransferStatus.FAILED
    assert result.transferred_energy_kwh == 0.0


def test_grid_transfer_efficiency():
    donor = create_battery("BASE-001", 0.80)
    recipient = create_battery("BASE-002", 0.40)

    result = Grid(GridConfig(transfer_efficiency=0.90)).execute_transfer(
        donor,
        recipient,
        EnergyTransfer("BASE-001", "BASE-002", 10.0, 5.0, 2.0),
    )

    assert result.transferred_energy_kwh == 9.0
