// frontend/assets/js/api.js
const BASE = "http://127.0.0.1:8000";

async function fetchJSON(url, opts = {}) {
  const res = await fetch(url, opts);
  if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`);
  return res.json();
}

async function fetchHistoryAll() {
  return fetchJSON(`${BASE}/history/all`);
}

async function fetchHistorySummary() {
  return fetchJSON(`${BASE}/history/summary`);
}
