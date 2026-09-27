const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

const MAINTENANCE_API = `${API_BASE}/maintenance`;

async function apiRequest(path, options = {}) {
  const response = await fetch(`${MAINTENANCE_API}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      data.detail || data.message || "Maintenance request failed."
    );
  }

  return data;
}

export async function getMaintenanceWorkers() {
  const data = await apiRequest("/workers");

  // Support either:
  // [ ...workers ]
  // { workers: [ ...workers ] }
  return Array.isArray(data)
    ? data
    : Array.isArray(data.workers)
      ? data.workers
      : [];
}

export async function getMaintenanceJobs() {
  const data = await apiRequest("/jobs");

  // Support either:
  // [ ...jobs ]
  // { jobs: [ ...jobs ] }
  return Array.isArray(data)
    ? data
    : Array.isArray(data.jobs)
      ? data.jobs
      : [];
}

export function createMaintenanceJob(payload) {
  return apiRequest("/jobs", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function performMaintenanceAction(jobId, action) {
  return apiRequest(`/jobs/${jobId}/${action}`, {
    method: "POST",
  });
}