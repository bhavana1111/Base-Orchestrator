from dataclasses import dataclass
from enum import Enum


class TransferStatus(str, Enum):
    PLANNED = "planned"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True)
class EnergyTransfer:
    donor_battery_id: str
    recipient_battery_id: str
    energy_kwh: float
    power_kw: float
    duration_hours: float


@dataclass(frozen=True)
class EnergyTransferResult:
    donor_battery_id: str
    recipient_battery_id: str
    requested_energy_kwh: float
    transferred_energy_kwh: float
    status: TransferStatus
    reason: str | None = None
