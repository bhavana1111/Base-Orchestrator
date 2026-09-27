const API_BASE_URL = "http://127.0.0.1:8000/api";

async function request(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }

  return response.json();
}

export function getFleet() {
  return request("/fleet");
}

export function getBatteries() {
  return request("/fleet/batteries");
}

export function getBattery(batteryId) {
  return request(`/fleet/batteries/${encodeURIComponent(batteryId)}`);
}
