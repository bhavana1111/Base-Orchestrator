# Battery Domain

The Battery domain represents one Base battery and describes **what the battery is and what it can do**.

## Properties

- **Battery ID** — identifies the battery.
- **Home ID** — identifies the home associated with it.
- **Capacity** — how much energy it can store (`39.2 kWh` in our model).
- **Maximum Charge Power** — maximum charging rate (`11 kW`).
- **Maximum Discharge Power** — maximum delivery rate (`11 kW`).
- **Minimum / Maximum SOC** — safe operating range.
- **Current SOC** — how full the battery is.
- **Health** — `HEALTHY`, `DEGRADED`, or `FAILED`.
- **Status** — `AVAILABLE`, `CHARGING`, `DISCHARGING`, or `OFFLINE`.
- **Home Load** — current power consumed by the home.
- **Backup Reserve** — energy that should be preserved for backup.

## Methods

### `charge()`

Charges the battery while respecting its power and SOC limits.

### `discharge()`

Provides energy while respecting its power and SOC limits.

### `energy_kwh`

Returns the energy currently stored.

### `available_charge_kwh`

Returns how much more energy can be stored.

### `available_discharge_kwh`

Returns how much energy can be provided before reaching the minimum SOC.

### Health and status methods

The battery can be marked healthy, degraded, failed, available, or offline.

A failed or offline battery cannot be operated.

### Home information

The battery can update its current home load and backup reserve. These values will later help the Orchestrator make fleet-level decisions.

## What the Battery Does Not Decide

The Battery does not decide:

- When to charge or discharge.
- Whether electricity is cheap or expensive.
- What ERCOT is doing.
- Which battery should be selected.
- How the fleet should coordinate.

In simple terms:

```text
Battery       = What can I physically do?
Fleet         = How do all batteries work together?
Orchestrator  = What should the fleet do?
```
