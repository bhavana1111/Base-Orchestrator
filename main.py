from app.domain.battery import Battery
from app.domain.battery_specs import BatterySpecs
from app.domain.battery_state import BatteryState


def main() -> None:
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
        battery_id="BASE-001",
        specs=specs,
        state=state,
    )

    print("=== Battery ===")
    print(f"ID: {battery.battery_id}")
    print(f"Capacity: {battery.specs.capacity_kwh} kWh")
    print(f"SOC: {battery.soc:.0%}")
    print(f"Stored energy: {battery.energy_kwh:.2f} kWh")
    print(
        f"Available for charging: "
        f"{battery.available_charge_kwh:.2f} kWh"
    )
    print(
        f"Available for discharge: "
        f"{battery.available_discharge_kwh:.2f} kWh"
    )


if __name__ == "__main__":
    main()