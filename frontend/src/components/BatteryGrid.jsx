import BatteryCard from "./BatteryCard";

export default function BatteryGrid({ batteries, onSelect }) {
  return (
    <section className="battery-section">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Fleet Assets</span>
          <h2>Battery Fleet</h2>
        </div>
        <span className="asset-count">{batteries.length} assets</span>
      </div>

      <div className="battery-grid">
        {batteries.map((battery) => (
          <BatteryCard
            key={battery.battery_id}
            battery={battery}
            onClick={() => onSelect(battery.battery_id)}
          />
        ))}
      </div>
    </section>
  );
}
