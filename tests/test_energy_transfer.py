from app.domain.energy_transfer import EnergyTransfer, TransferStatus


def test_energy_transfer_contains_execution_parameters():
    transfer = EnergyTransfer("BASE-001", "BASE-002", 10.0, 5.0, 2.0)
    assert transfer.energy_kwh == 10.0
    assert transfer.power_kw == 5.0
    assert transfer.duration_hours == 2.0


def test_transfer_status_values():
    assert TransferStatus.PLANNED.value == "planned"
    assert TransferStatus.COMPLETED.value == "completed"
    assert TransferStatus.PARTIAL.value == "partial"
    assert TransferStatus.FAILED.value == "failed"
