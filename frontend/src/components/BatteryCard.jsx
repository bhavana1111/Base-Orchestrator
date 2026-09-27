import { BatteryCharging, BatteryFull, BatteryWarning, CircleOff } from "lucide-react";

function healthLabel(health) {
  return health.charAt(0).toUpperCase() + health.slice(1);
}

function statusClass(status) {
  return status === "available" ? "status-available" : "status-unavailable";
}

export default function BatteryCard({ battery, onClick }) {
  const unavailable = battery.status === "offline" || battery.health === "failed";

  return (
    <button
      className={`battery-card ${unavailable ? "battery-unavailable" : ""}`}
      onClick={onClick}
      type="button"
    >
      <div className="battery-card-top">
        <span className="battery-icon">
          {battery.health === "failed" ? (
            <CircleOff size={18} />
          ) : battery.health === "degraded" ? (
            <BatteryWarning size={18} />
          ) : (
            <BatteryFull size={18} />
          )}
        </span>
        <span className={`status-pill ${statusClass(battery.status)}`}>
          {battery.status}
        </span>
      </div>

      <div className="battery-id">{battery.battery_id}</div>

      <div className="soc-row">
        <span>SOC</span>
        <strong>{Math.round(battery.soc * 100)}%</strong>
      </div>

      <div className="soc-track">
        <div
          className="soc-fill"
          style={{ width: `${battery.soc * 100}%` }}
        />
      </div>

      <div className="battery-footer">
        <span>{healthLabel(battery.health)}</span>
        <span>{battery.home_load_kw.toFixed(1)} kW load</span>
      </div>
    </button>
  );
}
