from .battery import Battery
from .battery_health import BatteryHealth
from .battery_specs import BatterySpecs
from .battery_state import BatteryState
from .battery_status import BatteryStatus


def create_fabricated_batteries(count: int = 100) -> list[Battery]:
    """
    Create a deterministic set of fabricated batteries.

    The same count always produces the same battery fleet.
    """

    if count <= 0:
        raise ValueError("count must be greater than 0.")

    batteries: list[Battery] = []

    specs = BatterySpecs(
        capacity_kwh=39.2,
        max_charge_kw=11.0,
        max_discharge_kw=11.0,
        min_soc=0.20,
        max_soc=0.95,
    )

    for index in range(1, count + 1):
        # Deterministic SOC pattern: 40%, 45%, ..., 85%
        soc = 0.40 + ((index - 1) % 10) * 0.05

        # Deterministic home load pattern: 2.0 - 6.5 kW
        home_load_kw = 2.0 + ((index - 1) % 10) * 0.5

        # Deterministic backup reserve pattern: 30%, 35%, ..., 55%
        backup_reserve_pct = (
            0.30 + ((index - 1) % 6) * 0.05
        )

        health = BatteryHealth.HEALTHY
        status = BatteryStatus.AVAILABLE

        # A few deterministic degraded batteries.
        if index in {20, 40, 60, 80}:
            health = BatteryHealth.DEGRADED

        # A few deterministic unavailable batteries.
        if index in {25, 50, 75, 100}:
            status = BatteryStatus.OFFLINE

        # A failed battery is also offline.
        if index in {30, 90}:
            health = BatteryHealth.FAILED
            status = BatteryStatus.OFFLINE

        state = BatteryState(
            soc=soc,
            health=health,
            status=status,
            home_load_kw=home_load_kw,
            backup_reserve_pct=backup_reserve_pct,
        )

        battery = Battery(
            battery_id=f"BASE-{index:03d}",
            home_id=f"HOME-{index:03d}",
            specs=specs,
            state=state,
        )

        batteries.append(battery)

    return batteries