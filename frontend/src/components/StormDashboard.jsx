import { useState } from "react";
import {
  AlertTriangle,
  ArrowDown,
  ArrowRight,
  Battery,
  CheckCircle2,
  CloudLightning,
  RefreshCw,
  ShieldCheck,
  Zap,
} from "lucide-react";

import {
  createStormPlan,
  executeStormPlan,
  replanStorm,
} from "../services/stormApi";

function StormDashboard() {
  const [stormDuration, setStormDuration] = useState(6);
  const [transferPower, setTransferPower] = useState(5);

  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState("");
  const [executionResult, setExecutionResult] = useState(null);

  async function analyzeStorm() {
    try {
      setLoading(true);
      setError("");
      setExecutionResult(null);

      const result = await createStormPlan({
        storm_duration_hours: Number(stormDuration),
        transfer_power_kw: Number(transferPower),
      });

      setPlan(result);
    } catch (err) {
      setError(err.message || "Unable to analyze storm readiness.");
    } finally {
      setLoading(false);
    }
  }

  async function executePlan() {
    try {
      setExecuting(true);
      setError("");

      const result = await executeStormPlan({
        storm_duration_hours: Number(stormDuration),
        transfer_power_kw: Number(transferPower),
      });

      setExecutionResult(result);

      // Recalculate current readiness after execution.
      const updatedPlan = await replanStorm({
        storm_duration_hours: Number(stormDuration),
        transfer_power_kw: Number(transferPower),
      });

      setPlan(updatedPlan);
    } catch (err) {
      setError(err.message || "Unable to execute storm plan.");
    } finally {
      setExecuting(false);
    }
  }

  async function handleReplan() {
    try {
      setLoading(true);
      setError("");

      const result = await replanStorm({
        storm_duration_hours: Number(stormDuration),
        transfer_power_kw: Number(transferPower),
      });

      setPlan(result);
      setExecutionResult(null);
    } catch (err) {
      setError(err.message || "Unable to replan storm readiness.");
    } finally {
      setLoading(false);
    }
  }

  const readinessClass =
    plan?.ready
      ? "ready"
      : plan?.coverage_pct >= 75
        ? "warning"
        : "danger";

  return (
    <div className="storm-dashboard">
      <style>{`
        .storm-dashboard {
          color: #e8f0f2;
          display: flex;
          flex-direction: column;
          gap: 24px;
        }

        .storm-hero {
          display: flex;
          justify-content: space-between;
          align-items: flex-end;
          gap: 24px;
        }

        .storm-eyebrow {
          display: flex;
          align-items: center;
          gap: 7px;
          color: #43e88d;
          font-size: 11px;
          font-weight: 800;
          letter-spacing: 0.14em;
          text-transform: uppercase;
        }

        .storm-title {
          margin: 6px 0 0;
          font-size: 32px;
          line-height: 1.1;
          color: #f2f7f8;
        }

        .storm-description {
          margin: 9px 0 0;
          color: #8ea1a8;
          font-size: 14px;
        }

        .storm-controls {
          display: flex;
          align-items: flex-end;
          gap: 12px;
          padding: 16px;
          border: 1px solid #203137;
          border-radius: 14px;
          background: linear-gradient(
            145deg,
            #101d21,
            #0b1519
          );
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.18);
        }

        .storm-field {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .storm-field label {
          color: #789097;
          font-size: 10px;
          font-weight: 700;
          letter-spacing: 0.08em;
          text-transform: uppercase;
        }

        .storm-field-row {
          display: flex;
          align-items: center;
          gap: 7px;
        }

        .storm-input {
          width: 82px;
          padding: 9px 10px;
          border: 1px solid #2b3d43;
          border-radius: 8px;
          background: #071014;
          color: #f1f6f7;
          outline: none;
        }

        .storm-input:focus {
          border-color: #43e88d;
          box-shadow: 0 0 0 2px rgba(67, 232, 141, 0.1);
        }

        .storm-unit {
          color: #71868e;
          font-size: 12px;
        }

        .storm-button {
          height: 38px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 7px;
          padding: 0 15px;
          border-radius: 8px;
          border: 1px solid #2c4047;
          background: #142227;
          color: #dfeaec;
          font-weight: 700;
          font-size: 12px;
          cursor: pointer;
          transition: 0.15s ease;
        }

        .storm-button:hover {
          background: #1a2d33;
          border-color: #3a525a;
        }

        .storm-button.primary {
          border-color: #43e88d;
          background: #43e88d;
          color: #06110b;
        }

        .storm-button.primary:hover {
          background: #5cf19e;
        }

        .storm-button.danger-action {
          border-color: #7a3f3f;
          background: #281719;
          color: #ff9b9b;
        }

        .storm-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .storm-error {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 13px 16px;
          border: 1px solid #673b3b;
          border-radius: 10px;
          background: #241517;
          color: #ffaaaa;
          font-size: 13px;
        }

        .storm-status {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 18px 20px;
          border-radius: 14px;
          border: 1px solid #203137;
          background: #0c171b;
        }

        .storm-status-left {
          display: flex;
          align-items: center;
          gap: 13px;
        }

        .storm-status-icon {
          width: 42px;
          height: 42px;
          display: grid;
          place-items: center;
          border-radius: 10px;
        }

        .storm-status-icon.ready {
          color: #43e88d;
          background: rgba(67, 232, 141, 0.1);
        }

        .storm-status-icon.warning {
          color: #ffc46b;
          background: rgba(255, 196, 107, 0.1);
        }

        .storm-status-icon.danger {
          color: #ff7777;
          background: rgba(255, 119, 119, 0.1);
        }

        .storm-status-title {
          font-size: 15px;
          font-weight: 800;
        }

        .storm-status-subtitle {
          margin-top: 3px;
          color: #789097;
          font-size: 12px;
        }

        .storm-status-badge {
          padding: 7px 11px;
          border-radius: 999px;
          font-size: 11px;
          font-weight: 800;
          letter-spacing: 0.05em;
          text-transform: uppercase;
        }

        .storm-status-badge.ready {
          color: #43e88d;
          background: rgba(67, 232, 141, 0.1);
        }

        .storm-status-badge.warning {
          color: #ffc46b;
          background: rgba(255, 196, 107, 0.1);
        }

        .storm-status-badge.danger {
          color: #ff7777;
          background: rgba(255, 119, 119, 0.1);
        }

        .storm-metrics {
          display: grid;
          grid-template-columns: repeat(5, minmax(0, 1fr));
          gap: 12px;
        }

        .storm-metric {
          min-height: 105px;
          padding: 17px;
          border: 1px solid #1e3036;
          border-radius: 13px;
          background: #0c171b;
        }

        .storm-metric-label {
          color: #71868e;
          font-size: 10px;
          font-weight: 700;
          letter-spacing: 0.07em;
          text-transform: uppercase;
        }

        .storm-metric-value {
          margin-top: 10px;
          font-size: 23px;
          font-weight: 800;
          color: #edf4f5;
        }

        .storm-metric-value.green {
          color: #43e88d;
        }

        .storm-metric-value.yellow {
          color: #ffc46b;
        }

        .storm-metric-value.red {
          color: #ff7777;
        }

        .storm-section-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 18px;
        }

        .storm-panel {
          overflow: hidden;
          border: 1px solid #1e3036;
          border-radius: 14px;
          background: #0c171b;
        }

        .storm-panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 18px;
          border-bottom: 1px solid #1b2b30;
        }

        .storm-panel-title {
          display: flex;
          align-items: center;
          gap: 9px;
          font-size: 15px;
          font-weight: 800;
        }

        .storm-panel-title svg {
          color: #43e88d;
        }

        .storm-panel-count {
          color: #71868e;
          font-size: 11px;
        }

        .storm-panel-body {
          padding: 18px;
        }

        .orchestration-flow {
          display: grid;
          grid-template-columns: 1fr 54px 1.05fr 54px 1fr;
          align-items: stretch;
          gap: 10px;
        }

        .flow-column {
          min-width: 0;
          overflow: hidden;
          border: 1px solid #1e3036;
          border-radius: 14px;
          background: #0c171b;
        }

        .flow-column.donor {
          border-color: #28513d;
        }

        .flow-column.recipient {
          border-color: #543737;
        }

        .flow-header {
          padding: 15px 16px;
          border-bottom: 1px solid #1b2b30;
        }

        .flow-header-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 10px;
        }

        .flow-title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 13px;
          font-weight: 850;
          text-transform: uppercase;
          letter-spacing: .06em;
        }

        .flow-column.donor .flow-title {
          color: #43e88d;
        }

        .flow-column.recipient .flow-title {
          color: #ff9999;
        }

        .flow-subtitle {
          margin-top: 5px;
          color: #71868e;
          font-size: 11px;
          line-height: 1.4;
        }

        .flow-count {
          padding: 4px 8px;
          border-radius: 999px;
          background: #17272c;
          color: #9fb0b5;
          font-size: 10px;
          font-weight: 800;
        }

        .flow-list {
          max-height: 310px;
          overflow-y: auto;
        }

        .flow-battery {
          padding: 12px 15px;
          border-bottom: 1px solid #17262b;
        }

        .flow-battery:last-child {
          border-bottom: 0;
        }

        .flow-battery-top {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 10px;
        }

        .flow-battery-id {
          color: #dfe9eb;
          font-size: 12px;
          font-weight: 800;
        }

        .flow-battery-energy {
          font-size: 12px;
          font-weight: 800;
          white-space: nowrap;
        }

        .donor-energy {
          color: #43e88d;
        }

        .recipient-energy {
          color: #ff9b9b;
        }

        .flow-battery-meta {
          display: flex;
          justify-content: space-between;
          gap: 8px;
          margin-top: 5px;
          color: #70848b;
          font-size: 10px;
        }

        .flow-progress {
          height: 4px;
          margin-top: 8px;
          overflow: hidden;
          border-radius: 99px;
          background: #1b2b30;
        }

        .flow-progress-fill {
          height: 100%;
          border-radius: inherit;
        }

        .donor-fill {
          background: #43e88d;
        }

        .recipient-fill {
          background: #ff7777;
        }

        .flow-connector {
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .flow-arrow {
          width: 42px;
          height: 42px;
          display: grid;
          place-items: center;
          border: 1px solid #2b4147;
          border-radius: 50%;
          background: #0c171b;
          color: #43e88d;
        }

        .grid-pool {
          display: flex;
          flex-direction: column;
          min-height: 100%;
          border: 1px solid #38525a;
          border-radius: 14px;
          background:
            radial-gradient(circle at 50% 15%, rgba(67,232,141,.10), transparent 45%),
            #0c171b;
        }

        .grid-pool-header {
          padding: 15px 16px;
          border-bottom: 1px solid #1b2b30;
        }

        .grid-pool-title {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #dce8ea;
          font-size: 13px;
          font-weight: 850;
          text-transform: uppercase;
          letter-spacing: .06em;
        }

        .grid-pool-title svg {
          color: #43e88d;
        }

        .grid-pool-subtitle {
          margin-top: 5px;
          color: #71868e;
          font-size: 10px;
        }

        .pool-value {
          padding: 25px 16px 18px;
          text-align: center;
        }

        .pool-value-number {
          color: #43e88d;
          font-size: 32px;
          font-weight: 900;
        }

        .pool-value-label {
          margin-top: 3px;
          color: #71868e;
          font-size: 10px;
          text-transform: uppercase;
          letter-spacing: .08em;
        }

        .pool-stat {
          display: flex;
          justify-content: space-between;
          gap: 10px;
          padding: 9px 16px;
          border-top: 1px solid #17262b;
          color: #84989f;
          font-size: 10px;
        }

        .pool-stat strong {
          color: #dce6e8;
        }

        .pool-flow {
          margin-top: auto;
          padding: 14px 16px;
          color: #62777e;
          font-size: 10px;
          text-align: center;
          line-height: 1.5;
        }

        .distribution-list {
          padding: 0 16px 14px;
        }

        .distribution-row {
          display: flex;
          justify-content: space-between;
          gap: 10px;
          padding: 8px 0;
          border-bottom: 1px solid #17262b;
          color: #8da1a7;
          font-size: 10px;
        }

        .distribution-row strong {
          color: #dce6e8;
        }

        .transfer-row {
          display: grid;
          grid-template-columns: 1fr 38px 1fr auto;
          align-items: center;
          gap: 10px;
          padding: 13px 0;
          border-bottom: 1px solid #18272c;
        }

        .transfer-row:last-child {
          border-bottom: 0;
        }

        .battery-name {
          font-weight: 750;
          font-size: 13px;
        }

        .battery-role {
          margin-top: 3px;
          color: #70848b;
          font-size: 10px;
          text-transform: uppercase;
        }

        .transfer-arrow {
          width: 32px;
          height: 32px;
          display: grid;
          place-items: center;
          border-radius: 50%;
          color: #43e88d;
          background: rgba(67, 232, 141, 0.08);
        }

        .transfer-energy {
          color: #dce7e9;
          font-weight: 800;
          font-size: 12px;
          white-space: nowrap;
        }

        .empty-state {
          padding: 25px 10px;
          text-align: center;
          color: #70848b;
          font-size: 13px;
        }

        .recommendation-row {
          display: grid;
          grid-template-columns: 1fr auto auto auto;
          gap: 18px;
          align-items: center;
          padding: 12px 0;
          border-bottom: 1px solid #18272c;
        }

        .recommendation-row:last-child {
          border-bottom: 0;
        }

        .recommendation-label {
          color: #dbe5e7;
          font-weight: 700;
          font-size: 12px;
        }

        .recommendation-value {
          color: #81959c;
          font-size: 11px;
          white-space: nowrap;
        }

        .recommendation-reduce {
          color: #ffc46b;
          font-size: 11px;
          font-weight: 800;
          white-space: nowrap;
        }

        .assessment-panel {
          grid-column: 1 / -1;
        }

        .table-scroll {
          overflow-x: auto;
        }

        .storm-table {
          width: 100%;
          border-collapse: collapse;
        }

        .storm-table th {
          padding: 11px 14px;
          color: #6e838a;
          border-bottom: 1px solid #203137;
          font-size: 9px;
          font-weight: 800;
          letter-spacing: 0.07em;
          text-align: left;
          text-transform: uppercase;
          white-space: nowrap;
        }

        .storm-table td {
          padding: 11px 14px;
          border-bottom: 1px solid #17262b;
          color: #cbd8db;
          font-size: 11px;
          white-space: nowrap;
        }

        .storm-table tr:last-child td {
          border-bottom: 0;
        }

        .soc-bar {
          width: 70px;
          height: 5px;
          overflow: hidden;
          border-radius: 99px;
          background: #1b2b30;
        }

        .soc-fill {
          height: 100%;
          border-radius: inherit;
          background: #43e88d;
        }

        .table-status {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          font-weight: 750;
        }

        .table-status.ready {
          color: #43e88d;
        }

        .table-status.risk {
          color: #ffc46b;
        }

        .table-status.failed {
          color: #ff7777;
        }

        .execution-result {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          padding: 14px 16px;
          border: 1px solid #234536;
          border-radius: 11px;
          background: rgba(67, 232, 141, 0.06);
        }

        .execution-result-title {
          color: #43e88d;
          font-size: 12px;
          font-weight: 800;
        }

        .execution-result-detail {
          margin-top: 3px;
          color: #82979e;
          font-size: 11px;
        }

        .storm-actions {
          display: flex;
          gap: 8px;
        }

        @media (max-width: 1200px) {
          .storm-metrics {
            grid-template-columns: repeat(3, 1fr);
          }

          .orchestration-flow {
            grid-template-columns: 1fr;
          }

          .flow-connector {
            height: 28px;
          }

          .flow-arrow {
            transform: rotate(90deg);
          }
        }

        @media (max-width: 900px) {
          .storm-hero {
            flex-direction: column;
            align-items: stretch;
          }

          .storm-controls {
            flex-wrap: wrap;
          }

          .storm-section-grid {
            grid-template-columns: 1fr;
          }

          .assessment-panel {
            grid-column: auto;
          }
        }

        @media (max-width: 650px) {
          .storm-metrics {
            grid-template-columns: 1fr 1fr;
          }

          .storm-controls {
            align-items: stretch;
            flex-direction: column;
          }

          .storm-field {
            width: 100%;
          }

          .storm-input {
            width: 100%;
          }

          .storm-button {
            width: 100%;
          }

          .orchestration-flow {
          display: grid;
          grid-template-columns: 1fr 54px 1.05fr 54px 1fr;
          align-items: stretch;
          gap: 10px;
        }

        .flow-column {
          min-width: 0;
          overflow: hidden;
          border: 1px solid #1e3036;
          border-radius: 14px;
          background: #0c171b;
        }

        .flow-column.donor {
          border-color: #28513d;
        }

        .flow-column.recipient {
          border-color: #543737;
        }

        .flow-header {
          padding: 15px 16px;
          border-bottom: 1px solid #1b2b30;
        }

        .flow-header-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 10px;
        }

        .flow-title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 13px;
          font-weight: 850;
          text-transform: uppercase;
          letter-spacing: .06em;
        }

        .flow-column.donor .flow-title {
          color: #43e88d;
        }

        .flow-column.recipient .flow-title {
          color: #ff9999;
        }

        .flow-subtitle {
          margin-top: 5px;
          color: #71868e;
          font-size: 11px;
          line-height: 1.4;
        }

        .flow-count {
          padding: 4px 8px;
          border-radius: 999px;
          background: #17272c;
          color: #9fb0b5;
          font-size: 10px;
          font-weight: 800;
        }

        .flow-list {
          max-height: 310px;
          overflow-y: auto;
        }

        .flow-battery {
          padding: 12px 15px;
          border-bottom: 1px solid #17262b;
        }

        .flow-battery:last-child {
          border-bottom: 0;
        }

        .flow-battery-top {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 10px;
        }

        .flow-battery-id {
          color: #dfe9eb;
          font-size: 12px;
          font-weight: 800;
        }

        .flow-battery-energy {
          font-size: 12px;
          font-weight: 800;
          white-space: nowrap;
        }

        .donor-energy {
          color: #43e88d;
        }

        .recipient-energy {
          color: #ff9b9b;
        }

        .flow-battery-meta {
          display: flex;
          justify-content: space-between;
          gap: 8px;
          margin-top: 5px;
          color: #70848b;
          font-size: 10px;
        }

        .flow-progress {
          height: 4px;
          margin-top: 8px;
          overflow: hidden;
          border-radius: 99px;
          background: #1b2b30;
        }

        .flow-progress-fill {
          height: 100%;
          border-radius: inherit;
        }

        .donor-fill {
          background: #43e88d;
        }

        .recipient-fill {
          background: #ff7777;
        }

        .flow-connector {
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .flow-arrow {
          width: 42px;
          height: 42px;
          display: grid;
          place-items: center;
          border: 1px solid #2b4147;
          border-radius: 50%;
          background: #0c171b;
          color: #43e88d;
        }

        .grid-pool {
          display: flex;
          flex-direction: column;
          min-height: 100%;
          border: 1px solid #38525a;
          border-radius: 14px;
          background:
            radial-gradient(circle at 50% 15%, rgba(67,232,141,.10), transparent 45%),
            #0c171b;
        }

        .grid-pool-header {
          padding: 15px 16px;
          border-bottom: 1px solid #1b2b30;
        }

        .grid-pool-title {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #dce8ea;
          font-size: 13px;
          font-weight: 850;
          text-transform: uppercase;
          letter-spacing: .06em;
        }

        .grid-pool-title svg {
          color: #43e88d;
        }

        .grid-pool-subtitle {
          margin-top: 5px;
          color: #71868e;
          font-size: 10px;
        }

        .pool-value {
          padding: 25px 16px 18px;
          text-align: center;
        }

        .pool-value-number {
          color: #43e88d;
          font-size: 32px;
          font-weight: 900;
        }

        .pool-value-label {
          margin-top: 3px;
          color: #71868e;
          font-size: 10px;
          text-transform: uppercase;
          letter-spacing: .08em;
        }

        .pool-stat {
          display: flex;
          justify-content: space-between;
          gap: 10px;
          padding: 9px 16px;
          border-top: 1px solid #17262b;
          color: #84989f;
          font-size: 10px;
        }

        .pool-stat strong {
          color: #dce6e8;
        }

        .pool-flow {
          margin-top: auto;
          padding: 14px 16px;
          color: #62777e;
          font-size: 10px;
          text-align: center;
          line-height: 1.5;
        }

        .distribution-list {
          padding: 0 16px 14px;
        }

        .distribution-row {
          display: flex;
          justify-content: space-between;
          gap: 10px;
          padding: 8px 0;
          border-bottom: 1px solid #17262b;
          color: #8da1a7;
          font-size: 10px;
        }

        .distribution-row strong {
          color: #dce6e8;
        }

        .transfer-row {
            grid-template-columns: 1fr auto;
          }

          .transfer-arrow {
            display: none;
          }

          .recommendation-row {
            grid-template-columns: 1fr 1fr;
          }
        }
      `}</style>

      {/* HEADER */}
      <div className="storm-hero">
        <div>
          <div className="storm-eyebrow">
            <CloudLightning size={14} />
            Fleet Resilience
          </div>

          <h1 className="storm-title">Storm Readiness</h1>

          <p className="storm-description">
            Assess the fleet, identify safe energy donors and recipients, and
            orchestrate energy through a shared grid pool.
          </p>
        </div>

        <div className="storm-controls">
          <div className="storm-field">
            <label>Storm Duration</label>
            <div className="storm-field-row">
              <input
                className="storm-input"
                type="number"
                min="1"
                step="1"
                value={stormDuration}
                onChange={(e) => setStormDuration(e.target.value)}
              />
              <span className="storm-unit">hrs</span>
            </div>
          </div>

          <div className="storm-field">
            <label>Transfer Power</label>
            <div className="storm-field-row">
              <input
                className="storm-input"
                type="number"
                min="0.1"
                step="0.5"
                value={transferPower}
                onChange={(e) => setTransferPower(e.target.value)}
              />
              <span className="storm-unit">kW</span>
            </div>
          </div>

          <button
            className="storm-button primary"
            onClick={analyzeStorm}
            disabled={loading}
          >
            <CloudLightning size={15} />
            {loading ? "Analyzing..." : "Analyze Storm"}
          </button>
        </div>
      </div>

      {error && (
        <div className="storm-error">
          <AlertTriangle size={17} />
          {error}
        </div>
      )}

      {!plan && !loading && (
        <div className="storm-panel">
          <div className="storm-panel-body">
            <div className="empty-state">
              Configure the storm conditions above and analyze the fleet.
            </div>
          </div>
        </div>
      )}

      {plan && (
        <>
          {/* READINESS */}
          <div className="storm-status">
            <div className="storm-status-left">
              <div className={`storm-status-icon ${readinessClass}`}>
                {plan.ready ? (
                  <CheckCircle2 size={23} />
                ) : (
                  <AlertTriangle size={23} />
                )}
              </div>

              <div>
                <div className="storm-status-title">
                  {plan.ready
                    ? "Fleet is Storm Ready"
                    : "Fleet Requires Preparation"}
                </div>

                <div className="storm-status-subtitle">
                  {plan.ready
                    ? "Current fleet energy is sufficient for the requested storm duration."
                    : "The orchestrator identified energy deficits that require action."}
                </div>
              </div>
            </div>

            <span className={`storm-status-badge ${readinessClass}`}>
              {plan.ready ? "READY" : "AT RISK"}
            </span>
          </div>

          {/* METRICS */}
          <div className="storm-metrics">
            <Metric
              label="Coverage"
              value={`${Number(plan.coverage_pct || 0).toFixed(1)}%`}
              tone={plan.coverage_pct >= 100 ? "green" : "yellow"}
            />

            <Metric
              label="Energy Required"
              value={`${Number(plan.total_energy_needed_kwh ?? plan.total_energy_required_kwh ?? 0).toFixed(1)} kWh`}
            />

            <Metric
              label="Safe Surplus"
              value={`${Number(plan.total_safe_surplus_kwh || 0).toFixed(1)} kWh`}
              tone="green"
            />

            <Metric
              label="Grid Pool"
              value={`${Number(plan.total_grid_energy_kwh || 0).toFixed(1)} kWh`}
              tone="green"
            />

            <Metric
              label="Distributed"
              value={`${Number(plan.total_distributed_energy_kwh || 0).toFixed(1)} kWh`}
            />

            <Metric
              label="Unfulfilled"
              value={`${Number(plan.unfulfilled_deficit_kwh ?? plan.total_unfulfilled_deficit_kwh ?? 0).toFixed(1)} kWh`}
              tone={
                Number(plan.unfulfilled_deficit_kwh ?? plan.total_unfulfilled_deficit_kwh ?? 0) === 0
                  ? "green"
                  : "red"
              }
            />
          </div>

          {/* ACTIONS */}
          <div className="storm-actions">
            <button
              className="storm-button primary"
              onClick={executePlan}
              disabled={
                executing ||
                !(plan.grid_contributions?.length > 0) ||
                !(plan.grid_distributions?.length > 0)
              }
            >
              <Zap size={15} />
              {executing ? "Executing..." : "Execute Plan"}
            </button>

            <button
              className="storm-button"
              onClick={handleReplan}
              disabled={loading || executing}
            >
              <RefreshCw size={15} />
              Replan
            </button>
          </div>

          {/* EXECUTION RESULT */}
          {executionResult && (
            <div className="execution-result">
              <div>
                <div className="execution-result-title">
                  Energy Plan Executed
                </div>

                <div className="execution-result-detail">
                  Collected{" "}
                  {Number(
                    executionResult.execution?.collected_energy_kwh || 0
                  ).toFixed(1)}{" "}
                  kWh and distributed{" "}
                  {Number(
                    executionResult.execution?.distributed_energy_kwh || 0
                  ).toFixed(1)}{" "}
                  kWh through the shared grid pool.
                </div>
              </div>

              <CheckCircle2 size={20} color="#43e88d" />
            </div>
          )}

          <div className="storm-section-grid">
            {/* CORE ORCHESTRATION FLOW */}
          <div className="orchestration-flow">
            <FlowDonors
              donors={plan.donors || []}
              contributions={plan.grid_contributions || []}
            />

            <div className="flow-connector">
              <div className="flow-arrow">
                <ArrowRight size={17} />
              </div>
            </div>

            <GridPool
              gridEnergy={Number(plan.total_grid_energy_kwh || 0)}
              distributed={Number(plan.total_distributed_energy_kwh || 0)}
              contributions={plan.grid_contributions || []}
              distributions={plan.grid_distributions || []}
            />

            <div className="flow-connector">
              <div className="flow-arrow">
                <ArrowRight size={17} />
              </div>
            </div>

            <FlowRecipients
              recipients={plan.recipients || []}
              distributions={plan.grid_distributions || []}
            />
          </div>

            {/* LOAD MANAGEMENT */}
            <div className="storm-panel">
              <div className="storm-panel-header">
                <div className="storm-panel-title">
                  <ShieldCheck size={17} />
                  Load Management
                </div>

                <span className="storm-panel-count">
                  {plan.load_recommendations?.length || 0} actions
                </span>
              </div>

              <div className="storm-panel-body">
                {!plan.load_recommendations ||
                plan.load_recommendations.length === 0 ? (
                  <div className="empty-state">
                    No load reductions recommended.
                  </div>
                ) : (
                  plan.load_recommendations
                    .slice(0, 20)
                    .map((recommendation) => (
                      <div
                        className="recommendation-row"
                        key={recommendation.battery_id}
                      >
                        <div className="recommendation-label">
                          {recommendation.battery_id}
                        </div>

                        <div className="recommendation-value">
                          Current{" "}
                          {Number(
                            recommendation.current_home_load_kw || 0
                          ).toFixed(1)}{" "}
                          kW
                        </div>

                        <div className="recommendation-value">
                          Recommended{" "}
                          {Number(
                            recommendation.recommended_average_load_kw || 0
                          ).toFixed(1)}{" "}
                          kW
                        </div>

                        <div className="recommendation-reduce">
                          Reduce{" "}
                          {Number(
                            recommendation.reduction_kw || 0
                          ).toFixed(1)}{" "}
                          kW
                        </div>
                      </div>
                    ))
                )}

                {plan.load_recommendations?.length > 20 && (
                  <div className="empty-state">
                    Showing first 20 recommendations.
                  </div>
                )}
              </div>
            </div>

            {/* BATTERY ASSESSMENT */}
            <div className="storm-panel assessment-panel">
              <div className="storm-panel-header">
                <div className="storm-panel-title">
                  <Battery size={17} />
                  Battery Storm Assessment
                </div>

                <span className="storm-panel-count">
                  {plan.assessments?.length || 0} batteries
                </span>
              </div>

              <div className="table-scroll">
                <table className="storm-table">
                  <thead>
                    <tr>
                      <th>Battery</th>
                      <th>SOC</th>
                      <th>Current Energy</th>
                      <th>Required</th>
                      <th>Deficit</th>
                      <th>Safe Surplus</th>
                      <th>Status</th>
                    </tr>
                  </thead>

                  <tbody>
                    {plan.assessments?.map((assessment) => {
                      const current =
                        Number(assessment.current_energy_kwh || 0);

                      const required =
                        Number(assessment.required_energy_kwh || 0);

                      const capacity =
                        Math.max(required, current, 1);

                      const socPercent = Math.min(
                        100,
                        Math.max(
                          0,
                          (current / capacity) * 100
                        )
                      );

                      const isReady =
                        !assessment.needs_energy &&
                        assessment.participation_eligible;

                      const isUnavailable =
                        !assessment.participation_eligible;

                      return (
                        <tr key={assessment.battery_id}>
                          <td>
                            <strong>
                              {assessment.battery_id}
                            </strong>
                          </td>

                          <td>
                            <div
                              style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "8px",
                              }}
                            >
                              <div className="soc-bar">
                                <div
                                  className="soc-fill"
                                  style={{
                                    width: `${socPercent}%`,
                                  }}
                                />
                              </div>

                              {socPercent.toFixed(0)}%
                            </div>
                          </td>

                          <td>
                            {current.toFixed(1)} kWh
                          </td>

                          <td>
                            {required.toFixed(1)} kWh
                          </td>

                          <td>
                            {Number(
                              assessment.deficit_kwh || 0
                            ).toFixed(1)}{" "}
                            kWh
                          </td>

                          <td>
                            {Number(
                              assessment.safe_surplus_kwh || 0
                            ).toFixed(1)}{" "}
                            kWh
                          </td>

                          <td>
                            <span
                              className={`table-status ${
                                isUnavailable
                                  ? "failed"
                                  : isReady
                                    ? "ready"
                                    : "risk"
                              }`}
                            >
                              {isUnavailable
                                ? "Unavailable"
                                : isReady
                                  ? "Ready"
                                  : "Needs Energy"}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function FlowDonors({ donors, contributions }) {
  const contributionMap = new Map(
    contributions.map((item) => [item.battery_id, item])
  );

  return (
    <div className="flow-column donor">
      <div className="flow-header">
        <div className="flow-header-row">
          <div className="flow-title">
            <Battery size={16} />
            Donor Pool
          </div>

          <span className="flow-count">{donors.length}</span>
        </div>

        <div className="flow-subtitle">
          Batteries with safe energy available after protecting their own
          storm requirement.
        </div>
      </div>

      <div className="flow-list">
        {donors.length === 0 ? (
          <div className="empty-state">No safe donors identified.</div>
        ) : (
          donors.map((donor) => {
            const contribution = contributionMap.get(donor.battery_id);
            const surplus = Number(donor.safe_surplus_kwh || 0);
            const contributed = Number(contribution?.energy_kwh || 0);
            const pct =
              surplus > 0 ? Math.min(100, (contributed / surplus) * 100) : 0;

            return (
              <div className="flow-battery" key={donor.battery_id}>
                <div className="flow-battery-top">
                  <span className="flow-battery-id">
                    {donor.battery_id}
                  </span>

                  <span className="flow-battery-energy donor-energy">
                    +{surplus.toFixed(1)} kWh
                  </span>
                </div>

                <div className="flow-battery-meta">
                  <span>Safe surplus</span>
                  <span>
                    Planned contribution {contributed.toFixed(1)} kWh
                  </span>
                </div>

                <div className="flow-progress">
                  <div
                    className="flow-progress-fill donor-fill"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

function GridPool({
  gridEnergy,
  distributed,
  contributions,
  distributions,
}) {
  const remaining = Math.max(0, gridEnergy - distributed);

  return (
    <div className="grid-pool">
      <div className="grid-pool-header">
        <div className="grid-pool-title">
          <Zap size={16} />
          Grid Energy Pool
        </div>

        <div className="grid-pool-subtitle">
          Shared energy aggregation and distribution layer
        </div>
      </div>

      <div className="pool-value">
        <div className="pool-value-number">
          {gridEnergy.toFixed(1)}
        </div>

        <div className="pool-value-label">
          kWh collected
        </div>
      </div>

      <div className="pool-stat">
        <span>Contributors</span>
        <strong>{contributions.length}</strong>
      </div>

      <div className="pool-stat">
        <span>Recipient plans</span>
        <strong>{distributions.length}</strong>
      </div>

      <div className="pool-stat">
        <span>Distributed</span>
        <strong>{distributed.toFixed(1)} kWh</strong>
      </div>

      <div className="pool-stat">
        <span>Remaining</span>
        <strong>{remaining.toFixed(1)} kWh</strong>
      </div>

      <div className="pool-flow">
        Donors contribute into one shared pool.
        <br />
        The pool is then distributed to recipients.
      </div>
    </div>
  );
}

function FlowRecipients({ recipients, distributions }) {
  const distributionMap = new Map(
    distributions.map((item) => [item.battery_id, item])
  );

  return (
    <div className="flow-column recipient">
      <div className="flow-header">
        <div className="flow-header-row">
          <div className="flow-title">
            <ArrowDown size={16} />
            Recipient Pool
          </div>

          <span className="flow-count">{recipients.length}</span>
        </div>

        <div className="flow-subtitle">
          Batteries whose current energy does not cover the storm requirement.
        </div>
      </div>

      <div className="flow-list">
        {recipients.length === 0 ? (
          <div className="empty-state">
            No batteries require additional energy.
          </div>
        ) : (
          recipients.map((recipient) => {
            const distribution = distributionMap.get(recipient.battery_id);
            const deficit = Number(recipient.deficit_kwh || 0);
            const delivered = Number(distribution?.energy_kwh || 0);
            const pct =
              deficit > 0
                ? Math.min(100, (delivered / deficit) * 100)
                : 100;

            return (
              <div className="flow-battery" key={recipient.battery_id}>
                <div className="flow-battery-top">
                  <span className="flow-battery-id">
                    {recipient.battery_id}
                  </span>

                  <span className="flow-battery-energy recipient-energy">
                    -{deficit.toFixed(1)} kWh
                  </span>
                </div>

                <div className="flow-battery-meta">
                  <span>Storm deficit</span>
                  <span>
                    Planned delivery {delivered.toFixed(1)} kWh
                  </span>
                </div>

                <div className="flow-progress">
                  <div
                    className="flow-progress-fill recipient-fill"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

function Metric({ label, value, tone }) {
  return (
    <div className="storm-metric">
      <div className="storm-metric-label">{label}</div>
      <div className={`storm-metric-value ${tone || ""}`}>
        {value}
      </div>
    </div>
  );
}

export default StormDashboard;