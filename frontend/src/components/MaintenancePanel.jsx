import { useEffect, useState } from "react";
import {
  AlertTriangle,
  BatteryWarning,
  CheckCircle2,
  ClipboardList,
  HardHat,
  Loader2,
  Play,
  RefreshCw,
  UserCheck,
  Wrench,
  XCircle,
} from "lucide-react";

import {
  getMaintenanceWorkers,
  getMaintenanceJobs,
  createMaintenanceJob,
  performMaintenanceAction,
} from "../services/maintenanceApi";

function MaintenancePanel() {
  const [workers, setWorkers] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busyJob, setBusyJob] = useState("");
  const [error, setError] = useState("");

  async function loadMaintenance() {
    try {
      setLoading(true);
      setError("");

      const [workerData, jobData] = await Promise.all([
        getMaintenanceWorkers(),
        getMaintenanceJobs(),
      ]);

      setWorkers(workerData);
      setJobs(jobData);
    } catch (err) {
      setError(err.message || "Unable to load maintenance data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadMaintenance();
  }, []);

  async function createRepairJob(batteryId = "BASE-030") {
    try {
      setBusyJob(`create-${batteryId}`);
      setError("");

      await createMaintenanceJob({
        battery_id: batteryId,
        reason: "Battery unavailable and requires maintenance.",
        priority: 1,
      });

      await loadMaintenance();
    } catch (err) {
      setError(err.message || "Unable to create repair job.");
    } finally {
      setBusyJob("");
    }
  }

  async function performJobAction(job, action) {
    try {
      setBusyJob(job.job_id);
      setError("");

      await performMaintenanceAction(job.job_id, action);

      await loadMaintenance();
    } catch (err) {
      setError(err.message || `Unable to ${action} maintenance job.`);
    } finally {
      setBusyJob("");
    }
  }

  const availableWorkers = workers.filter(
    (worker) => worker.status === "available"
  ).length;

  const activeJobs = jobs.filter(
    (job) =>
      job.status === "assigned" ||
      job.status === "in_progress"
  ).length;

  const completedJobs = jobs.filter(
    (job) => job.status === "completed"
  ).length;

  return (
    <div className="maintenance-page">
      <style>{`
        .maintenance-page {
          min-height: 100%;
          color: #e8f0f2;
          padding: 28px;
          background:
            radial-gradient(circle at 85% 5%, rgba(67,232,141,.08), transparent 28%),
            #071014;
        }

        .maintenance-shell {
          max-width: 1320px;
          margin: 0 auto;
        }

        .maintenance-hero {
          display: flex;
          justify-content: space-between;
          align-items: flex-end;
          gap: 24px;
          margin-bottom: 26px;
        }

        .maintenance-eyebrow {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #43e88d;
          font-size: 11px;
          font-weight: 800;
          letter-spacing: .14em;
          text-transform: uppercase;
        }

        .maintenance-title {
          margin: 7px 0 6px;
          font-size: 34px;
          line-height: 1.05;
          color: #f3f7f8;
        }

        .maintenance-subtitle {
          margin: 0;
          max-width: 680px;
          color: #8ea1a8;
          font-size: 14px;
        }

        .maintenance-refresh {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          border: 1px solid #294047;
          border-radius: 9px;
          padding: 10px 14px;
          background: #0d1a1f;
          color: #cbd8db;
          cursor: pointer;
        }

        .maintenance-refresh:hover {
          border-color: #43e88d;
          color: #43e88d;
        }

        .maintenance-error {
          display: flex;
          align-items: center;
          gap: 9px;
          margin-bottom: 18px;
          padding: 12px 14px;
          border: 1px solid rgba(248,113,113,.3);
          border-radius: 10px;
          background: rgba(127,29,29,.16);
          color: #fca5a5;
          font-size: 13px;
        }

        .maintenance-metrics {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 12px;
          margin-bottom: 20px;
        }

        .maintenance-metric {
          padding: 18px;
          border: 1px solid #1d3036;
          border-radius: 13px;
          background: linear-gradient(145deg,#101d21,#0b1519);
        }

        .maintenance-metric-label {
          color: #789097;
          font-size: 10px;
          font-weight: 800;
          letter-spacing: .1em;
          text-transform: uppercase;
        }

        .maintenance-metric-value {
          margin-top: 8px;
          font-size: 27px;
          font-weight: 800;
          color: #f1f6f7;
        }

        .maintenance-metric-value.green {
          color: #43e88d;
        }

        .maintenance-grid {
          display: grid;
          grid-template-columns: 1.45fr .8fr;
          gap: 18px;
        }

        .maintenance-card {
          overflow: hidden;
          border: 1px solid #1d3036;
          border-radius: 15px;
          background: #0b171b;
          box-shadow: 0 14px 35px rgba(0,0,0,.16);
        }

        .maintenance-card-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 17px 18px;
          border-bottom: 1px solid #1d3036;
        }

        .maintenance-card-title {
          display: flex;
          align-items: center;
          gap: 9px;
          font-size: 14px;
          font-weight: 800;
          color: #eef5f6;
        }

        .maintenance-count {
          color: #789097;
          font-size: 11px;
        }

        .maintenance-table-wrap {
          overflow-x: auto;
        }

        .maintenance-table {
          width: 100%;
          border-collapse: collapse;
          min-width: 700px;
        }

        .maintenance-table th {
          padding: 11px 14px;
          text-align: left;
          color: #687e86;
          font-size: 9px;
          letter-spacing: .08em;
          text-transform: uppercase;
          font-weight: 800;
        }

        .maintenance-table td {
          padding: 14px;
          border-top: 1px solid #17272c;
          color: #cbd8db;
          font-size: 12px;
        }

        .battery-id {
          color: #f0f5f6;
          font-weight: 800;
        }

        .status-pill {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          padding: 5px 8px;
          border-radius: 999px;
          font-size: 9px;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: .05em;
        }

        .status-created {
          color: #fbbf24;
          background: rgba(245,158,11,.1);
        }

        .status-assigned {
          color: #60a5fa;
          background: rgba(59,130,246,.1);
        }

        .status-progress {
          color: #a78bfa;
          background: rgba(139,92,246,.1);
        }

        .status-completed {
          color: #43e88d;
          background: rgba(67,232,141,.1);
        }

        .priority-high {
          color: #fb7185;
          font-weight: 800;
        }

        .job-action {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          border: 1px solid #294047;
          border-radius: 7px;
          padding: 7px 9px;
          background: #0d1a1f;
          color: #cbd8db;
          font-size: 10px;
          font-weight: 700;
          cursor: pointer;
        }

        .job-action:hover {
          border-color: #43e88d;
          color: #43e88d;
        }

        .job-action:disabled {
          opacity: .45;
          cursor: not-allowed;
        }

        .worker-list {
          padding: 8px 0;
        }

        .worker-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          padding: 14px 18px;
          border-bottom: 1px solid #17272c;
        }

        .worker-row:last-child {
          border-bottom: 0;
        }

        .worker-info {
          display: flex;
          align-items: center;
          gap: 11px;
        }

        .worker-icon {
          width: 34px;
          height: 34px;
          display: grid;
          place-items: center;
          border: 1px solid #294047;
          border-radius: 9px;
          background: #0d1a1f;
          color: #43e88d;
        }

        .worker-name {
          color: #e7eff1;
          font-size: 12px;
          font-weight: 750;
        }

        .worker-id {
          margin-top: 3px;
          color: #637981;
          font-size: 10px;
        }

        .worker-status {
          font-size: 9px;
          font-weight: 800;
          text-transform: uppercase;
          color: #43e88d;
        }

        .worker-status.busy {
          color: #60a5fa;
        }

        .worker-status.offline {
          color: #f87171;
        }

        .maintenance-empty {
          padding: 32px 18px;
          text-align: center;
          color: #71868e;
          font-size: 12px;
        }

        .maintenance-create {
          margin: 14px 18px 18px;
          width: calc(100% - 36px);
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 7px;
          padding: 10px 12px;
          border: 1px solid rgba(67,232,141,.35);
          border-radius: 8px;
          background: rgba(67,232,141,.08);
          color: #43e88d;
          font-size: 11px;
          font-weight: 800;
          cursor: pointer;
        }

        .maintenance-create:hover {
          background: rgba(67,232,141,.14);
          border-color: #43e88d;
        }

        .maintenance-loading {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 9px;
          min-height: 260px;
          color: #789097;
          font-size: 12px;
        }

        @media (max-width: 900px) {
          .maintenance-grid {
            grid-template-columns: 1fr;
          }

          .maintenance-metrics {
            grid-template-columns: repeat(2, 1fr);
          }

          .maintenance-hero {
            align-items: flex-start;
            flex-direction: column;
          }
        }

        @media (max-width: 560px) {
          .maintenance-page {
            padding: 18px;
          }

          .maintenance-metrics {
            grid-template-columns: 1fr;
          }

          .maintenance-title {
            font-size: 28px;
          }
        }
      `}</style>

      <div className="maintenance-shell">
        <div className="maintenance-hero">
          <div>
            <div className="maintenance-eyebrow">
              <Wrench size={14} />
              Fleet Maintenance
            </div>
            <h1 className="maintenance-title">
              Maintenance Operations
            </h1>
            <p className="maintenance-subtitle">
              Coordinate repair jobs and maintenance workers for unavailable
              batteries so the fleet can return to service.
            </p>
          </div>

          <button
            className="maintenance-refresh"
            onClick={loadMaintenance}
            disabled={loading}
          >
            <RefreshCw size={14} />
            Refresh
          </button>
        </div>

        {error && (
          <div className="maintenance-error">
            <AlertTriangle size={16} />
            {error}
          </div>
        )}

        {loading ? (
          <div className="maintenance-card">
            <div className="maintenance-loading">
              <Loader2 size={17} />
              Loading maintenance operations...
            </div>
          </div>
        ) : (
          <>
            <div className="maintenance-metrics">
              <div className="maintenance-metric">
                <div className="maintenance-metric-label">
                  Repair Jobs
                </div>
                <div className="maintenance-metric-value">
                  {jobs.length}
                </div>
              </div>

              <div className="maintenance-metric">
                <div className="maintenance-metric-label">
                  Active Jobs
                </div>
                <div className="maintenance-metric-value">
                  {activeJobs}
                </div>
              </div>

              <div className="maintenance-metric">
                <div className="maintenance-metric-label">
                  Workers Available
                </div>
                <div className="maintenance-metric-value green">
                  {availableWorkers}
                </div>
              </div>

              <div className="maintenance-metric">
                <div className="maintenance-metric-label">
                  Completed
                </div>
                <div className="maintenance-metric-value green">
                  {completedJobs}
                </div>
              </div>
            </div>

            <div className="maintenance-grid">
              <section className="maintenance-card">
                <div className="maintenance-card-header">
                  <div className="maintenance-card-title">
                    <ClipboardList size={16} />
                    Repair Queue
                  </div>
                  <span className="maintenance-count">
                    {jobs.length} jobs
                  </span>
                </div>

                {jobs.length === 0 ? (
                  <div className="maintenance-empty">
                    No maintenance jobs have been created yet.
                  </div>
                ) : (
                  <div className="maintenance-table-wrap">
                    <table className="maintenance-table">
                      <thead>
                        <tr>
                          <th>Battery</th>
                          <th>Reason</th>
                          <th>Priority</th>
                          <th>Worker</th>
                          <th>Status</th>
                          <th>Action</th>
                        </tr>
                      </thead>

                      <tbody>
                        {jobs.map((job) => (
                          <tr key={job.job_id}>
                            <td>
                              <div className="battery-id">
                                {job.battery_id}
                              </div>
                              <div style={{ color: "#536970", fontSize: 9 }}>
                                {job.job_id}
                              </div>
                            </td>

                            <td>{job.reason}</td>

                            <td>
                              <span className="priority-high">
                                P{job.priority}
                              </span>
                            </td>

                            <td>
                              {job.worker_id || "Unassigned"}
                            </td>

                            <td>
                              <span
                                className={`status-pill ${
                                  job.status === "completed"
                                    ? "status-completed"
                                    : job.status === "in_progress"
                                      ? "status-progress"
                                      : job.status === "assigned"
                                        ? "status-assigned"
                                        : "status-created"
                                }`}
                              >
                                {job.status === "in_progress" && (
                                  <Play size={9} />
                                )}
                                {job.status.replace("_", " ")}
                              </span>
                            </td>

                            <td>
                              {job.status === "created" && (
                                <button
                                  className="job-action"
                                  disabled={busyJob === job.job_id}
                                  onClick={() =>
                                    performJobAction(job, "assign")
                                  }
                                >
                                  <UserCheck size={11} />
                                  Assign
                                </button>
                              )}

                              {job.status === "assigned" && (
                                <button
                                  className="job-action"
                                  disabled={busyJob === job.job_id}
                                  onClick={() =>
                                    performJobAction(job, "start")
                                  }
                                >
                                  <Play size={11} />
                                  Start
                                </button>
                              )}

                              {job.status === "in_progress" && (
                                <button
                                  className="job-action"
                                  disabled={busyJob === job.job_id}
                                  onClick={() =>
                                    performJobAction(job, "complete")
                                  }
                                >
                                  <CheckCircle2 size={11} />
                                  Complete
                                </button>
                              )}

                              {job.status === "completed" && (
                                <span style={{ color: "#43e88d", fontSize: 10 }}>
                                  Done
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                <button
                  className="maintenance-create"
                  onClick={() => createRepairJob()}
                  disabled={busyJob.startsWith("create-")}
                >
                  <Wrench size={13} />
                  Create Repair Job
                </button>
              </section>

              <section className="maintenance-card">
                <div className="maintenance-card-header">
                  <div className="maintenance-card-title">
                    <HardHat size={16} />
                    Maintenance Workers
                  </div>
                  <span className="maintenance-count">
                    {workers.length} workers
                  </span>
                </div>

                <div className="worker-list">
                  {workers.length === 0 ? (
                    <div className="maintenance-empty">
                      No workers available.
                    </div>
                  ) : (
                    workers.map((worker) => (
                      <div
                        className="worker-row"
                        key={worker.worker_id}
                      >
                        <div className="worker-info">
                          <div className="worker-icon">
                            <HardHat size={16} />
                          </div>

                          <div>
                            <div className="worker-name">
                              {worker.name}
                            </div>
                            <div className="worker-id">
                              {worker.worker_id}
                            </div>
                          </div>
                        </div>

                        <div
                          className={`worker-status ${
                            worker.status === "assigned"
                              ? "busy"
                              : worker.status === "offline"
                                ? "offline"
                                : ""
                          }`}
                        >
                          {worker.status}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </section>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default MaintenancePanel;
