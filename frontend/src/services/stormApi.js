const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000/api";

async function request(path, options = {}) {
  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    }
  );

  if (!response.ok) {
    let message = `Request failed: ${response.status}`;

    try {
      const body = await response.json();

      if (body.detail) {
        message = body.detail;
      }
    } catch {
      // Keep default error message.
    }

    throw new Error(message);
  }

  return response.json();
}


export function createStormPlan({
  storm_duration_hours,
  transfer_power_kw,
}) {
  return request("/storm/plan", {
    method: "POST",
    body: JSON.stringify({
      storm_duration_hours,
      transfer_power_kw,
    }),
  });
}


export function executeStormPlan({
  storm_duration_hours,
  transfer_power_kw,
}) {
  return request("/storm/execute", {
    method: "POST",
    body: JSON.stringify({
      storm_duration_hours,
      transfer_power_kw,
    }),
  });
}


export function replanStorm({
  storm_duration_hours,
  transfer_power_kw,
}) {
  return request("/storm/replan", {
    method: "POST",
    body: JSON.stringify({
      storm_duration_hours,
      transfer_power_kw,
    }),
  });
}