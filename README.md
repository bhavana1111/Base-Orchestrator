# Base Fleet Orchestrator

A fleet-level resilience and orchestration platform for coordinating distributed
battery energy resources during storm conditions.

The system separates **battery state and safety constraints**, **fleet
management**, **storm-readiness decision making**, **shared grid energy
movement**, **load management**, and **maintenance operations**.

---

## Architecture

```text
                         ┌─────────────────────────┐
                         │       React UI           │
                         │                         │
                         │  Fleet Monitoring       │
                         │  Storm Readiness        │
                         │  Maintenance Operations │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │      FastAPI API        │
                         │                         │
                         │ Fleet API               │
                         │ Storm API               │
                         │ Maintenance API         │
                         └────────────┬────────────┘
                                      │
                 ┌────────────────────┼────────────────────┐
                 │                    │                    │
                 ▼                    ▼                    ▼
        ┌────────────────┐   ┌──────────────────┐   ┌──────────────────┐
        │     Fleet      │   │ Storm Orchestrator│   │    Maintenance   │
        │                │   │                  │   │                  │
        │ Battery        │   │ Assess readiness │   │ Repair jobs      │
        │ collection     │   │ Find recipients  │   │ Worker assignment│
        │ Aggregate state│   │ Select donors    │   │ Repair lifecycle │
        └───────┬────────┘   │ Build plan       │   └──────────────────┘
                │             └────────┬─────────┘
                │                      │
                ▼                      ▼
        ┌────────────────┐     ┌──────────────────┐
        │    Battery     │     │       Grid       │
        │                │     │                  │
        │ State          │     │ Shared energy    │
        │ SOC            │     │ aggregation pool │
        │ Health         │     │ Distribution     │
        │ Load           │     │ Efficiency       │
        │ Charge/Discharge│    └──────────────────┘
        └────────────────┘
```

## Core Components

### Battery

The Battery represents the physical capabilities and state of an individual
energy storage unit.

Responsibilities:

- Track state of charge (SOC)
- Track battery health
- Track availability/status
- Track home load
- Track backup reserve
- Calculate available charge/discharge energy
- Enforce charge and discharge limits
- Prevent unsafe operations

The Battery does **not** decide where energy should go.

### Fleet

The Fleet manages a collection of batteries and provides fleet-level state.

Responsibilities:

- Add and remove batteries
- Retrieve batteries by ID
- Identify available/unavailable batteries
- Calculate total fleet capacity
- Calculate total fleet energy
- Calculate average SOC
- Calculate aggregate charge/discharge capability
- Execute fleet-level charging/discharging

The Fleet intentionally does not contain orchestration strategy.

### Storm Readiness Service

The Storm Readiness Service evaluates whether individual batteries can survive
a requested storm duration.

For each battery it considers:

```text
Current Energy
      +
Home Load
      +
Protected Reserve
      ↓
Required Storm Energy
```

The assessment identifies:

- Required energy
- Energy deficit
- Safe surplus
- Participation eligibility
- Sustainable load
- Load-management capability

This creates the information required by the orchestrator.

### Storm Readiness Orchestrator

The Storm Readiness Orchestrator is the decision-making layer.

Its responsibility is to determine how the fleet should prepare for a storm.

The orchestration flow is:

```text
Storm Duration
      │
      ▼
Assess Every Battery
      │
      ▼
Identify Recipients
(Batteries that cannot survive)
      │
      ▼
Remove Recipients
from Donor Candidates
      │
      ▼
Identify Healthy Donors
      │
      ▼
Calculate Safe Contributions
      │
      ▼
Aggregate Energy
into Grid Pool
      │
      ▼
Distribute Grid Energy
to Recipients
      │
      ▼
Generate Load Recommendations
      │
      ▼
Re-assess Fleet Readiness
```

A critical design decision is that the orchestrator does **not** directly
connect one battery to another.

Instead:

```text
Donor Battery
      │
      ▼
   GRID POOL
      │
      ▼
Recipient Battery
```

This keeps energy movement separate from orchestration decisions and makes the
system easier to extend to larger fleets.

### Grid

The Grid acts as the shared energy aggregation and distribution layer.

It maintains a temporary energy pool during orchestration.

```text
             DONOR 1 ─────┐
                          │
             DONOR 2 ─────┤
                          ▼
                    ┌───────────┐
                    │ GRID POOL │
                    └─────┬─────┘
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
        RECIPIENT 1  RECIPIENT 2  RECIPIENT 3
```

Responsibilities:

- Collect energy from eligible batteries
- Enforce donor discharge limits
- Apply transfer efficiency
- Maintain the shared energy pool
- Distribute energy to recipients
- Enforce recipient charge limits
- Report full/partial/failed operations

The Grid does not decide which batteries should participate.
That decision belongs to the orchestrator.

### Load Management

Energy transfer is not the only mechanism used to improve resilience.

The orchestrator also calculates load-management recommendations for batteries
that can improve their storm survival by reducing consumption.

Example:

```text
Current Load       6.0 kW
       │
       ▼
Storm Assessment
       │
       ▼
Recommended Load  4.5 kW
       │
       ▼
Additional Backup Duration
```

This allows the system to combine:

- Energy redistribution
- Load reduction
- Battery reserves

rather than relying exclusively on additional energy.

### Maintenance Operations

Maintenance is implemented as a separate operational workflow.

Unavailable or failed batteries can be routed into a maintenance lifecycle:

```text
Unavailable Battery
        │
        ▼
   Repair Job
        │
        ▼
 Worker Assignment
        │
        ▼
   Repair Started
        │
        ▼
  Repair Completed
        │
        ▼
 Return to Service
```

The maintenance layer manages:

- Maintenance workers
- Worker availability
- Repair jobs
- Job priority
- Worker assignment
- Repair status
- Job completion

The maintenance workflow is intentionally separated from the storm
orchestration logic.

---

## Storm Resilience Decision Model

The system follows a fleet-level decision model:

```text
                 ┌─────────────────────┐
                 │   Storm Duration    │
                 └──────────┬──────────┘
                            ▼
                 ┌─────────────────────┐
                 │ Assess Fleet State  │
                 └──────────┬──────────┘
                            ▼
              ┌───────────────────────────┐
              │ Who cannot survive storm? │
              └─────────────┬─────────────┘
                            │
                      RECIPIENTS
                            │
              ┌─────────────▼─────────────┐
              │ Exclude from donor pool   │
              └─────────────┬─────────────┘
                            ▼
                ┌────────────────────────┐
                │ Healthy donor batteries│
                └────────────┬───────────┘
                             ▼
                   Safe energy surplus
                             │
                             ▼
                    ┌────────────────┐
                    │   GRID POOL    │
                    └───────┬────────┘
                            ▼
                   Recipient batteries
                            │
                            ▼
                    Load recommendations
                            │
                            ▼
                   Final readiness state
```

## Separation of Responsibilities

A key architectural principle is that each layer has a single primary
responsibility:

| Component | Responsibility |
|---|---|
| Battery | Physical state and safety constraints |
| Fleet | Manage the battery collection |
| Readiness Service | Assess storm survival |
| Orchestrator | Make fleet-level decisions |
| Grid | Move and aggregate energy |
| Maintenance | Coordinate repair operations |
| FastAPI | Expose system capabilities |
| React | Visualize and operate the system |

This separation keeps business decisions out of the physical battery model and
keeps the Fleet from becoming a large orchestration class.

---

## Failure-Aware Design

The system is designed around the assumption that individual batteries,
energy operations, and maintenance resources can fail.

The orchestrator therefore works with:

- Battery health
- Battery availability
- Safe energy limits
- Partial grid operations
- Failed grid operations
- Unfulfilled energy deficits
- Maintenance availability

Instead of assuming that every battery can participate, the system continuously
works with the currently available fleet state.



## Project Structure

```text
base-orchestrator/
│
├── app/
│   ├── api/
│   │   ├── fleet.py
│   │   ├── storm.py
│   │   └── maintenance.py
│   │
│   └── domain/
│       ├── battery.py
│       ├── fleet.py
│       ├── grid.py
│       ├── storm_readiness.py
│       ├── storm_orchestrator.py
│       └── maintenance.py
│
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── FleetOverview.jsx
│       │   ├── BatteryGrid.jsx
│       │   ├── BatteryDetails.jsx
│       │   ├── StormDashboard.jsx
│       │   └── MaintenancePanel.jsx
│       │
│       ├── services/
│       │   ├── fleetApi.js
│       │   └── stormApi.js
│       │
│       └── App.jsx
│
├── tests/
│
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Resilience Workflow

The resulting system provides an end-to-end resilience workflow:

```text
                STORM INPUT
                     │
                     ▼
             ┌───────────────┐
             │ Fleet Assess  │
             └───────┬───────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
    ENERGY RECIPIENTS      HEALTHY DONORS
          │                     │
          │               SAFE SURPLUS
          │                     │
          │                     ▼
          │              ┌─────────────┐
          └─────────────►│ GRID POOL   │
                         └──────┬──────┘
                                │
                                ▼
                         ENERGY DISTRIBUTION
                                │
                                ▼
                       LOAD RECOMMENDATIONS
                                │
                                ▼
                       STORM READINESS
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
              READY FLEET             UNAVAILABLE
                                            │
                                            ▼
                                    MAINTENANCE JOB
                                            │
                                            ▼
                                     WORKER ASSIGNED
                                            │
                                            ▼
                                        REPAIRED
                                            │
                                            ▼
                                      RETURN TO FLEET
```

The architecture is designed so that additional orchestration strategies can
be added later without changing the core Battery model.

# Storm Readiness — Judge Testing Guide

## What the judges should test

### Test 1 — Normal Storm
1. Open **Storm Readiness**.
2. Enter **12 hours** storm duration and **5 kW** transfer power.
3. Click **Analyze Storm**.
4. Check the **Readiness, Energy Needed, Safe Surplus, Grid Energy, and Coverage** metrics.
5. Review the **Recipients** and **Donors** sections.
6. Confirm recipients are batteries with an energy deficit.
7. Confirm recipients are **not also listed as donors**.
8. Check that donor energy appears in the **Grid Energy Pool**.
9. Click **Execute Plan** and verify collected/distributed energy.
10. Click **Replan** and verify the fleet is reassessed using its new state.

### Test 2 — Short Storm
1. Enter **4 hours**.
2. Click **Analyze Storm**.
3. Compare the donor/recipient breakdown with the 12-hour scenario.
4. Check whether more batteries can satisfy their own requirements.
5. Verify safe surplus is recalculated.

### Test 3 — Long Storm
1. Enter **24 or 48 hours**.
2. Click **Analyze Storm**.
3. Look for increased energy requirements/deficits.
4. Check **Unfulfilled Deficit**.
5. Verify the system does **not claim full readiness when available energy is insufficient**.

### Test 4 — Load Management
1. Analyze a longer storm.
2. Find a battery that cannot sustain its current load.
3. Open its assessment.
4. Check **Current Load** vs **Sustainable Load**.
5. Verify a load-management recommendation is provided.

### Test 5 — Failure / Availability
1. Review batteries marked **offline/failed**.
2. Run Storm Analysis.
3. Verify unavailable batteries are not selected as donors.
4. Verify the orchestrator continues planning with the remaining available fleet.
5. Check whether the resulting deficit/coverage reflects the unavailable resources.

