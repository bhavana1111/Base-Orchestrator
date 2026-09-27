import { X } from "lucide-react";

function percent(value) {
  return `${(value * 100).toFixed(0)}%`;
}

function number(value) {
  return value.toFixed(2);
}

function DetailRow({ label, value }) {
  return (
    <div className="detail-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default function BatteryDetails({ battery, onClose }) {
  if (!battery) return null;

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="details-drawer" onClick={(event) => event.stopPropagation()}>
        <div className="drawer-header">
          <div>
            <span className="eyebrow">Battery Detail</span>
            <h2>{battery.battery_id}</h2>
          </div>
          <button className="icon-button" onClick={onClose} type="button">
            <X size={20} />
          </button>
        </div>

        <div className="detail-soc">
          <div className="detail-soc-heading">
            <span>State of Charge</span>
            <strong>{percent(battery.soc)}</strong>
          </div>
          <div className="soc-track large">
            <div
              className="soc-fill"
              style={{ width: `${battery.soc * 100}%` }}
            />
          </div>
        </div>

        <div className="detail-section">
          <h3>State</h3>
          <DetailRow label="Health" value={battery.health} />
          <DetailRow label="Status" value={battery.status} />
          <DetailRow label="Available" value={battery.is_available ? "Yes" : "No"} />
        </div>

        <div className="detail-section">
          <h3>Energy</h3>
          <DetailRow label="Capacity" value={`${number(battery.capacity_kwh)} kWh`} />
          <DetailRow label="Current Energy" value={`${number(battery.energy_kwh)} kWh`} />
          <DetailRow label="Charge Available" value={`${number(battery.available_charge_kwh)} kWh`} />
          <DetailRow label="Discharge Available" value={`${number(battery.available_discharge_kwh)} kWh`} />
        </div>

        <div className="detail-section">
          <h3>Power</h3>
          <DetailRow label="Max Charge" value={`${number(battery.max_charge_kw)} kW`} />
          <DetailRow label="Max Discharge" value={`${number(battery.max_discharge_kw)} kW`} />
        </div>

        <div className="detail-section">
          <h3>Home</h3>
          <DetailRow label="Home ID" value={battery.home_id} />
          <DetailRow label="Home Load" value={`${number(battery.home_load_kw)} kW`} />
          <DetailRow label="Backup Reserve" value={percent(battery.backup_reserve_pct)} />
        </div>
      </aside>
    </div>
  );
}
