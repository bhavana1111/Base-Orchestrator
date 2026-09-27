from dataclasses import dataclass

from .battery import Battery
from .energy_transfer import (
    EnergyTransfer,
    EnergyTransferResult,
    TransferStatus,
)


@dataclass(frozen=True)
class GridConfig:
    transfer_efficiency: float = 1.0

    def __post_init__(self) -> None:
        if not 0 < self.transfer_efficiency <= 1:
            raise ValueError("transfer_efficiency must be between 0 and 1.")


class Grid:
    """
    Simulation abstraction for energy moving through the grid/charging path.

    This MVP does not model ERCOT topology or real hardware.
    """

    def __init__(self, config: GridConfig | None = None) -> None:
        self.config = config or GridConfig()

    def execute_transfer(
        self,
        donor: Battery,
        recipient: Battery,
        transfer: EnergyTransfer,
    ) -> EnergyTransferResult:

        def failed(reason: str) -> EnergyTransferResult:
            return EnergyTransferResult(
                donor_battery_id=donor.battery_id,
                recipient_battery_id=recipient.battery_id,
                requested_energy_kwh=transfer.energy_kwh,
                transferred_energy_kwh=0.0,
                status=TransferStatus.FAILED,
                reason=reason,
            )

        if donor.battery_id == recipient.battery_id:
            return failed("Donor and recipient cannot be the same battery.")
        if not donor.is_available:
            return failed("Donor battery is unavailable.")
        if not recipient.is_available:
            return failed("Recipient battery is unavailable.")
        if transfer.energy_kwh <= 0:
            return failed("Transfer energy must be greater than zero.")
        if transfer.power_kw <= 0:
            return failed("Transfer power must be greater than zero.")
        if transfer.duration_hours <= 0:
            return failed("Transfer duration must be greater than zero.")

        max_transfer_energy = min(
            donor.available_discharge_kwh,
            recipient.available_charge_kwh,
            transfer.power_kw * transfer.duration_hours,
            donor.specs.max_discharge_kw * transfer.duration_hours,
            recipient.specs.max_charge_kw * transfer.duration_hours,
        )

        if max_transfer_energy <= 1e-9:
            return failed("No transferable energy is currently available.")

        requested_energy = min(
            transfer.energy_kwh,
            max_transfer_energy,
        )

        actual_power_kw = min(
            transfer.power_kw,
            donor.specs.max_discharge_kw,
            recipient.specs.max_charge_kw,
        )

        actual_duration_hours = requested_energy / actual_power_kw

        donor_energy = donor.discharge(
            actual_power_kw,
            actual_duration_hours,
        )

        recipient_energy_requested = (
            donor_energy * self.config.transfer_efficiency
        )

        actual_recipient_energy = recipient.charge(
            actual_power_kw,
            recipient_energy_requested / actual_power_kw,
        )

        if actual_recipient_energy <= 1e-9:
            return failed("Transfer produced no delivered energy.")

        status = (
            TransferStatus.COMPLETED
            if actual_recipient_energy + 1e-9 >= transfer.energy_kwh
            else TransferStatus.PARTIAL
        )

        return EnergyTransferResult(
            donor_battery_id=donor.battery_id,
            recipient_battery_id=recipient.battery_id,
            requested_energy_kwh=transfer.energy_kwh,
            transferred_energy_kwh=actual_recipient_energy,
            status=status,
        )
