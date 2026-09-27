# Fleet

## Purpose

A Fleet represents a group of batteries that can be coordinated and controlled as a single energy resource.

The Fleet provides an aggregate view of the batteries and allows higher-level components to request charging or discharging without managing each battery individually.

The Fleet is responsible for coordination and aggregation, not deciding why or when the batteries should operate.

---

## Properties

### Fleet ID

A unique identifier for the fleet.

Example: `FLEET-001`

### Battery Count

The number of batteries currently belonging to the fleet.

### Batteries

The collection of batteries managed by the fleet.

Individual batteries can be accessed when necessary for coordination or inspection.

### Available Batteries

Batteries that are currently capable of participating in fleet operations.

A battery is unavailable when it is failed or offline.

A degraded battery may still participate if it remains available.

### Unavailable Batteries

Batteries that cannot currently participate in fleet operations.

Unavailable batteries remain part of the fleet unless they are explicitly removed.

### Total Capacity

The combined energy capacity of all batteries in the fleet.

Example: `100 × 39.2 kWh = 3,920 kWh`

### Total Stored Energy

The amount of energy currently stored across all batteries in the fleet.

This represents the physical energy stored in the fleet, including batteries that may currently be unavailable.

### Average SOC

The average state of charge across the batteries in the fleet.

### Available Charge Power

The combined rated charging power of batteries that are currently available.

Example: `94 × 11 kW = 1,034 kW`

This represents rated power capability. Actual achievable charging depends on SOC and requested duration.

### Available Discharge Power

The combined rated discharging power of batteries that are currently available.

Example: `94 × 11 kW = 1,034 kW`

This represents rated power capability. Actual achievable discharging depends on SOC and requested duration.

---

## Operations

### Add Battery

Adds a battery to the fleet. Battery IDs must be unique within the fleet.

### Remove Battery

Removes a battery from the fleet. Removing a battery changes fleet membership; it does not represent a battery failure.

### Get Battery

Retrieves a specific battery using its battery ID.

### Charge

Requests the fleet to charge at a specified power for a specified duration.

The Fleet coordinates the operation across available batteries and respects individual battery limits.

The operation returns the actual power achieved. The requested power is not guaranteed to be fully achieved.

### Discharge

Requests the fleet to discharge at a specified power for a specified duration.

The Fleet coordinates the operation across available batteries and respects individual battery limits.

The operation returns the actual power achieved. The requested power is not guaranteed to be fully achieved.

---

## Responsibilities

The Fleet is responsible for:

- Managing fleet membership
- Providing aggregate fleet information
- Identifying available and unavailable batteries
- Calculating aggregate capacity and stored energy
- Calculating aggregate rated charge/discharge capability
- Coordinating charging across available batteries
- Coordinating discharging across available batteries
- Respecting individual battery constraints
- Reporting the actual result of fleet operations

---

## What Fleet Does Not Decide

The Fleet does not decide:

- When the fleet should charge
- When the fleet should discharge
- How much energy should be reserved
- Whether the grid requires charging or discharging
- Whether electricity prices justify an operation
- How ERCOT signals should be interpreted
- Whether an operation is economically beneficial
- How to recover from failures
- How to prioritize competing objectives

These decisions belong to higher-level orchestration and integration components.

---

## Availability

A battery is available when it can safely participate in a fleet operation.

A battery is unavailable when:

- Its health is `FAILED`
- Its status is `OFFLINE`

A degraded battery may still participate while it remains available.

Unavailable batteries are excluded from fleet charge and discharge operations.

---

## Power vs Energy

Power describes how quickly energy can be transferred. Example: `11 kW`.

Energy describes how much energy is stored or transferred. Example: `39.2 kWh`.

The Fleet's rated available power does not guarantee that the fleet can sustain that power for an arbitrary duration.

Actual achievable power depends on:

- Battery SOC
- Battery energy limits
- Battery power limits
- Requested duration
- Battery availability

The Fleet reports the actual result rather than assuming the requested target was achieved.

---

## Design Boundary

The Fleet is the coordination and aggregation layer between individual batteries and the higher-level orchestrator.

```text
             Orchestrator
                  |
                  |  "Discharge 500 kW"
                  v
                Fleet
          +-------+-------+
          |       |       |
          v       v       v
       Battery Battery Battery
          |       |       |
          v       v       v
       Physical battery behavior
```

The Orchestrator decides **what the fleet should do**.

The Fleet coordinates **how available batteries execute the request**.

Each Battery enforces **what it can physically do**.

---

## Future Extensions

The Fleet may later expose additional aggregate information required by orchestration, such as:

- Total household load
- Total available energy
- Fleet backup reserve
- Health distribution
- Degraded battery count
- Battery-level dispatch results
- Fleet ramp capability
- Fleet operating constraints

These should be added only when required by the orchestration design.