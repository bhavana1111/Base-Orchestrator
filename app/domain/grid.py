from dataclasses import dataclass

from .battery import Battery

EPSILON = 1e-9


@dataclass(frozen=True)
class GridConfig:
    """
    Configuration for the shared grid/charging-path simulation.

    transfer_efficiency represents the end-to-end energy retained when
    energy is collected from a battery into the shared grid pool.
    """

    transfer_efficiency: float = 1.0

    def __post_init__(self) -> None:
        if not 0 < self.transfer_efficiency <= 1:
            raise ValueError(
                "transfer_efficiency must be between 0 and 1."
            )


@dataclass(frozen=True)
class GridCollectionResult:
    battery_id: str
    requested_energy_kwh: float
    collected_energy_kwh: float
    status: str
    reason: str | None = None


@dataclass(frozen=True)
class GridDistributionResult:
    battery_id: str
    requested_energy_kwh: float
    delivered_energy_kwh: float
    status: str
    reason: str | None = None


class Grid:
    """
    Shared energy-pool abstraction.

    The storm orchestration model is:

        donor batteries
              |
              v
        +-----------+
        |   GRID    |
        | ENERGY    |
        |   POOL    |
        +-----------+
              |
              v
        recipient batteries

    The Grid intentionally does not pair a donor with a recipient.
    It only manages energy entering and leaving the shared pool.
    """

    def __init__(self, config: GridConfig | None = None) -> None:
        self.config = config or GridConfig()
        self._energy_pool_kwh = 0.0

    @property
    def available_energy_kwh(self) -> float:
        """Energy currently available in the shared grid pool."""
        return self._energy_pool_kwh

    def reset_pool(self) -> None:
        """Clear the simulated grid energy pool."""
        self._energy_pool_kwh = 0.0

    def collect_energy(
        self,
        donor: Battery,
        energy_kwh: float,
        power_kw: float,
    ) -> GridCollectionResult:
        """
        Collect safe energy from a battery into the shared grid pool.

        The donor is responsible for enforcing its own physical limits.
        The Grid only determines how much can actually be collected and
        applies the configured grid-path efficiency.
        """

        if not donor.is_available:
            return GridCollectionResult(
                battery_id=donor.battery_id,
                requested_energy_kwh=energy_kwh,
                collected_energy_kwh=0.0,
                status="failed",
                reason="Donor battery is unavailable.",
            )

        if energy_kwh <= 0:
            return GridCollectionResult(
                battery_id=donor.battery_id,
                requested_energy_kwh=energy_kwh,
                collected_energy_kwh=0.0,
                status="failed",
                reason="Collection energy must be greater than zero.",
            )

        if power_kw <= 0:
            return GridCollectionResult(
                battery_id=donor.battery_id,
                requested_energy_kwh=energy_kwh,
                collected_energy_kwh=0.0,
                status="failed",
                reason="Collection power must be greater than zero.",
            )

        max_power_kw = min(
            power_kw,
            donor.specs.max_discharge_kw,
        )

        if max_power_kw <= EPSILON:
            return GridCollectionResult(
                battery_id=donor.battery_id,
                requested_energy_kwh=energy_kwh,
                collected_energy_kwh=0.0,
                status="failed",
                reason="Donor has no available discharge power.",
            )

        max_collectable_energy = min(
            donor.available_discharge_kwh,
            energy_kwh,
        )

        if max_collectable_energy <= EPSILON:
            return GridCollectionResult(
                battery_id=donor.battery_id,
                requested_energy_kwh=energy_kwh,
                collected_energy_kwh=0.0,
                status="failed",
                reason="Donor has no safe energy available.",
            )

        duration_hours = (
            max_collectable_energy / max_power_kw
        )

        discharged_energy = donor.discharge(
            max_power_kw,
            duration_hours,
        )

        # Energy that survives the grid/charging-path efficiency
        # becomes available in the shared pool.
        grid_energy = (
            discharged_energy
            * self.config.transfer_efficiency
        )

        self._energy_pool_kwh += grid_energy

        status = (
            "completed"
            if discharged_energy + EPSILON >= energy_kwh
            else "partial"
        )

        return GridCollectionResult(
            battery_id=donor.battery_id,
            requested_energy_kwh=energy_kwh,
            collected_energy_kwh=grid_energy,
            status=status,
        )

    def distribute_energy(
        self,
        recipient: Battery,
        energy_kwh: float,
        power_kw: float,
    ) -> GridDistributionResult:
        """
        Deliver energy from the shared grid pool to a recipient.

        There is no donor reference here. The source is always the
        aggregated grid energy pool.
        """

        if not recipient.is_available:
            return GridDistributionResult(
                battery_id=recipient.battery_id,
                requested_energy_kwh=energy_kwh,
                delivered_energy_kwh=0.0,
                status="failed",
                reason="Recipient battery is unavailable.",
            )

        if energy_kwh <= 0:
            return GridDistributionResult(
                battery_id=recipient.battery_id,
                requested_energy_kwh=energy_kwh,
                delivered_energy_kwh=0.0,
                status="failed",
                reason="Distribution energy must be greater than zero.",
            )

        if power_kw <= 0:
            return GridDistributionResult(
                battery_id=recipient.battery_id,
                requested_energy_kwh=energy_kwh,
                delivered_energy_kwh=0.0,
                status="failed",
                reason="Distribution power must be greater than zero.",
            )

        max_power_kw = min(
            power_kw,
            recipient.specs.max_charge_kw,
        )

        if max_power_kw <= EPSILON:
            return GridDistributionResult(
                battery_id=recipient.battery_id,
                requested_energy_kwh=energy_kwh,
                delivered_energy_kwh=0.0,
                status="failed",
                reason="Recipient has no available charge power.",
            )

        max_deliverable_energy = min(
            self._energy_pool_kwh,
            recipient.available_charge_kwh,
            energy_kwh,
        )

        if max_deliverable_energy <= EPSILON:
            return GridDistributionResult(
                battery_id=recipient.battery_id,
                requested_energy_kwh=energy_kwh,
                delivered_energy_kwh=0.0,
                status="failed",
                reason="No grid energy or recipient charge capacity is available.",
            )

        duration_hours = (
            max_deliverable_energy / max_power_kw
        )

        actual_delivered_energy = recipient.charge(
            max_power_kw,
            duration_hours,
        )

        self._energy_pool_kwh = max(
            0.0,
            self._energy_pool_kwh
            - actual_delivered_energy,
        )

        status = (
            "completed"
            if actual_delivered_energy + EPSILON >= energy_kwh
            else "partial"
        )

        return GridDistributionResult(
            battery_id=recipient.battery_id,
            requested_energy_kwh=energy_kwh,
            delivered_energy_kwh=actual_delivered_energy,
            status=status,
        )
