import { useEffect, useState } from "react";
import { RefreshCw, ShieldCheck, Zap } from "lucide-react";
import FleetOverview from "./components/FleetOverview";
import BatteryGrid from "./components/BatteryGrid";
import BatteryDetails from "./components/BatteryDetails";
import { getBattery, getBatteries, getFleet } from "./services/fleetApi";

function App() {
  const [fleet, setFleet] = useState(null);
  const [batteries, setBatteries] = useState([]);
  const [selectedBattery, setSelectedBattery] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadFleet() {
    try {
      setLoading(true);
      setError("");

      const [fleetData, batteryData] = await Promise.all([
        getFleet(),
        getBatteries(),
      ]);

      setFleet(fleetData);
      setBatteries(batteryData);
    } catch (err) {
      setError(
        "Could not connect to the Fleet API. Make sure FastAPI is running on port 8000."
      );
    } finally {
      setLoading(false);
    }
  }

  async function selectBattery(batteryId) {
    try {
      setError("");
      const battery = await getBattery(batteryId);
      setSelectedBattery(battery);
    } catch (err) {
      setError(`Could not load ${batteryId}.`);
    }
  }

  useEffect(() => {
    loadFleet();
  }, []);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">
            <Zap size={21} />
          </div>
          <div>
            <strong>BASE</strong>
            <span>Fleet Command Center</span>
          </div>
        </div>

        <div className="topbar-actions">
          <span className="system-state">
            <ShieldCheck size={17} />
            Fleet Monitoring
          </span>
          <button className="refresh-button" onClick={loadFleet} type="button">
            <RefreshCw size={16} />
            Refresh
          </button>
        </div>
      </header>

      <main className="main-content">
        <div className="page-intro">
          <div>
            <span className="eyebrow">ENERGY OPERATIONS</span>
            <h1>Fleet Command Center</h1>
            <p>
              Monitor the current state and energy capability of the battery fleet.
            </p>
          </div>
        </div>

        {error && <div className="error-banner">{error}</div>}

        {loading ? (
          <div className="loading-state">Loading fleet...</div>
        ) : (
          <>
            <FleetOverview fleet={fleet} />
            <BatteryGrid
              batteries={batteries}
              onSelect={selectBattery}
            />
          </>
        )}
      </main>

      <BatteryDetails
        battery={selectedBattery}
        onClose={() => setSelectedBattery(null)}
      />
    </div>
  );
}

export default App;
