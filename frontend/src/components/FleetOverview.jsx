function formatPercent(value) {
  return `${(value * 100).toFixed(1)}%`;
}

function formatNumber(value) {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 1,
  }).format(value);
}

function MetricCard({ label, value, detail }) {
  return (
    <div className="metric-card">
      <span className="metric-label">{label}</span>
      <strong className="metric-value">{value}</strong>
      {detail && <span className="metric-detail">{detail}</span>}
    </div>
  );
}

export default function FleetOverview({ fleet }) {
  if (!fleet) return null;

  return (
    <section className="overview">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Fleet Overview</span>
          <h2>{fleet.fleet_id}</h2>
        </div>
        <span className="live-badge">
          <span className="live-dot" />
          LIVE STATE
        </span>
      </div>

      <div className="metrics-grid">
        <MetricCard
          label="Batteries"
          value={fleet.battery_count}
          detail={`${fleet.available_batteries} available`}
        />
        <MetricCard
          label="Unavailable"
          value={fleet.unavailable_batteries}
          detail="offline or failed"
        />
        <MetricCard
          label="Fleet SOC"
          value={formatPercent(fleet.average_soc)}
          detail="average state of charge"
        />
        <MetricCard
          label="Stored Energy"
          value={`${formatNumber(fleet.total_energy_kwh)} kWh`}
          detail={`of ${formatNumber(fleet.total_capacity_kwh)} kWh`}
        />
        <MetricCard
          label="Charge Power"
          value={`${formatNumber(fleet.available_charge_kw)} kW`}
          detail="rated available"
        />
        <MetricCard
          label="Discharge Power"
          value={`${formatNumber(fleet.available_discharge_kw)} kW`}
          detail="rated available"
        />
      </div>
    </section>
  );
}
