from app.domain.battery import (
    Battery,
    BatteryHealth,
    BatterySpecs,
    BatteryState,
    BatteryStatus,
)
from app.domain.fleet import Fleet
from app.domain.grid import Grid
from app.domain.storm_orchestrator import StormReadinessOrchestrator


def create_battery(battery_id, soc, home_load_kw=2.0):
    return Battery(
        battery_id=battery_id,
        home_id=f"HOME-{battery_id}",
        specs=BatterySpecs(),
        state=BatteryState(
            soc=soc,
            health=BatteryHealth.HEALTHY,
            status=BatteryStatus.AVAILABLE,
            home_load_kw=home_load_kw,
            backup_reserve_pct=0.30,
        ),
    )


def test_orchestrator_creates_grid_pool_plan():
    donor = create_battery("BASE-001", 0.90)
    recipient = create_battery("BASE-002", 0.40)

    plan = StormReadinessOrchestrator().create_plan(
        [donor, recipient], 4
    )

    # The donor contributes to the shared grid pool.
    assert len(plan.grid_contributions) > 0
    assert plan.grid_contributions[0].battery_id == "BASE-001"

    # The recipient receives energy from the grid pool.
    assert len(plan.grid_distributions) > 0
    assert plan.grid_distributions[0].battery_id == "BASE-002"

    # There is no donor -> recipient transfer object anymore.
    assert plan.total_grid_energy_kwh > 0
    assert plan.total_distributed_energy_kwh > 0


def test_degraded_battery_is_not_selected_as_donor():
    donor = create_battery("BASE-001", 0.90)
    donor.mark_degraded()
    recipient = create_battery("BASE-002", 0.40)

    plan = StormReadinessOrchestrator().create_plan(
        [donor, recipient], 4
    )

    assert all(
        contribution.battery_id != "BASE-001"
        for contribution in plan.grid_contributions
    )


def test_unavailable_battery_is_not_recipient():
    donor = create_battery("BASE-001", 0.90)
    recipient = create_battery("BASE-002", 0.40)
    recipient.mark_offline()

    plan = StormReadinessOrchestrator().create_plan(
        [donor, recipient], 4
    )

    assert all(
        distribution.battery_id != "BASE-002"
        for distribution in plan.grid_distributions
    )


def test_execute_plan_moves_energy_through_grid_pool():
    donor = create_battery("BASE-001", 0.90)
    recipient = create_battery("BASE-002", 0.40)

    fleet = Fleet("FLEET-001", [donor, recipient])
    orchestrator = StormReadinessOrchestrator()

    plan = orchestrator.create_plan(fleet.batteries, 4)

    donor_before = donor.energy_kwh
    recipient_before = recipient.energy_kwh

    report = orchestrator.execute_plan(fleet, Grid(), plan)

    assert report.collected_energy_kwh > 0
    assert report.distributed_energy_kwh > 0
    assert donor.energy_kwh < donor_before
    assert recipient.energy_kwh > recipient_before


def test_replan_after_donor_failure():
    donor_1 = create_battery("BASE-001", 0.90)
    donor_2 = create_battery("BASE-002", 0.85)
    recipient = create_battery("BASE-003", 0.40)

    fleet = Fleet(
        "FLEET-001",
        [donor_1, donor_2, recipient],
    )
    orchestrator = StormReadinessOrchestrator()

    donor_1.mark_failed()

    plan = orchestrator.replan(fleet, 4)

    assert all(
        contribution.battery_id != "BASE-001"
        for contribution in plan.grid_contributions
    )
    assert any(
        contribution.battery_id == "BASE-002"
        for contribution in plan.grid_contributions
    )
