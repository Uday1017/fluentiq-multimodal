// frontend/assets/js/charts.js
let overallLineChart = null;
let compareRadarChart = null;

function renderSummaryCards(summary) {
  const container = document.getElementById("summaryCards");
  container.innerHTML = "";

  const cards = [
    { label: "Avg Fluency", value: Math.round(summary.avg_fluency || 0) },
    { label: "Avg Grammar", value: Math.round(summary.avg_grammar || 0) },
    { label: "Avg Posture", value: Math.round(summary.avg_posture || 0) },
    { label: "Avg Overall", value: Math.round(summary.avg_overall || 0) },
  ];

  cards.forEach((c) => {
    const el = document.createElement("div");
    el.className = "card summary-card";
    el.innerHTML = `<div class="value">${c.value}</div><div class="label">${c.label}</div>`;
    container.appendChild(el);
  });
}

function renderOverallLine(allSessions) {
  const ctx = document.getElementById("overallLineChart").getContext("2d");
  const sessions = (allSessions || []).slice().reverse(); // oldest first for time chart
  const labels = sessions.map((s) => {
    const t = new Date(s.timestamp);
    return `${t.toLocaleDateString()} ${t.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    })}`;
  });
  const data = sessions.map((s) => s.overall || 0);

  if (overallLineChart) overallLineChart.destroy();

  overallLineChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Overall Score",
          data,
          fill: false,
          tension: 0.2,
          borderColor: "#2563eb",
          backgroundColor: "#60a5fa",
          pointRadius: 3,
        },
      ],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        y: { min: 0, max: 100 },
      },
    },
  });
}

function renderSessionsTable(allSessions) {
  const tbody = document.querySelector("#sessionsTable tbody");
  tbody.innerHTML = "";
  (allSessions || []).forEach((s) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${s.id}</td>
      <td>${new Date(s.timestamp).toLocaleString()}</td>
      <td>${s.overall ?? "-"}</td>
      <td>${s.fluency ?? "-"}</td>
      <td>${s.grammar ?? "-"}</td>
      <td>${s.posture ?? "-"}</td>
      <td class="actions">
        <button onclick="showSessionDetail(${s.id})">View</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
  // store currently loaded sessions for detail lookup
  window._fiq_sessions = allSessions || [];
}

function populateCompareSelects(allSessions) {
  const a = document.getElementById("compareA");
  const b = document.getElementById("compareB");
  const exportSel = document.getElementById("sessionExportSelect");

  // Reset dropdowns
  a.innerHTML = `<option value="">Select A</option>`;
  b.innerHTML = `<option value="">Select B</option>`;
  if (exportSel) {
    exportSel.innerHTML = `<option value="">Select session to export JSON</option>`;
  }

  (allSessions || []).forEach((s) => {
    const label = `${s.id} — ${new Date(s.timestamp).toLocaleDateString()}`;

    // Compare dropdowns
    a.innerHTML += `<option value="${s.id}">${label}</option>`;
    b.innerHTML += `<option value="${s.id}">${label}</option>`;

    // Export JSON dropdown
    if (exportSel) {
      exportSel.innerHTML += `<option value="${s.id}">${label}</option>`;
    }
  });
}


function showSessionDetail(id) {
  const sessions = window._fiq_sessions || [];
  const s = sessions.find((x) => x.id === id);
  if (!s) {
    alert("Session not found");
    return;
  }
  const panel = document.getElementById("sessionDetail");
  const content = document.getElementById("detailContent");
  content.innerHTML = "";

  const blocks = [
    { k: "Overall", v: s.overall },
    { k: "Fluency", v: s.fluency },
    { k: "Grammar", v: s.grammar },
    { k: "Coherence", v: s.coherence },
    { k: "Readability", v: s.readability },
    { k: "Posture", v: s.posture },
    {
      k: "Gaze (%)",
      v: s.gaze !== null && s.gaze !== undefined ? s.gaze : "-",
    },
    { k: "Timestamp", v: new Date(s.timestamp).toLocaleString() },
  ];

  blocks.forEach((b) => {
    const d = document.createElement("div");
    d.className = "detail-block";
    d.innerHTML = `<strong>${b.k}</strong><div>${b.v}</div>`;
    content.appendChild(d);
  });

  // show transcript excerpt
  const tblock = document.createElement("div");
  tblock.className = "detail-block";
  tblock.style.gridColumn = "1 / -1";
  tblock.innerHTML = `<strong>Transcript</strong><div style="margin-top:6px; color:#333">${escapeHtml(
    (s.transcript || "").slice(0, 800)
  )}</div>`;
  content.appendChild(tblock);

  panel.style.display = "block";
  panel.scrollIntoView({ behavior: "smooth" });
}

function compareSessions(idA, idB) {
  const sessions = window._fiq_sessions || [];
  const A = sessions.find((s) => s.id === idA);
  const B = sessions.find((s) => s.id === idB);
  if (!A || !B) return alert("Session(s) not found for comparison.");

  const labels = [
    "Fluency",
    "Grammar",
    "Coherence",
    "Readability",
    "Posture",
    "Gaze",
    "Overall",
  ];
  const aValues = [
    A.fluency || 0,
    A.grammar || 0,
    A.coherence || 0,
    A.readability || 0,
    A.posture || 0,
    A.gaze || 0,
    A.overall || 0,
  ];
  const bValues = [
    B.fluency || 0,
    B.grammar || 0,
    B.coherence || 0,
    B.readability || 0,
    B.posture || 0,
    B.gaze || 0,
    B.overall || 0,
  ];

  const ctx = document.getElementById("compareRadarChart").getContext("2d");
  if (compareRadarChart) compareRadarChart.destroy();

  compareRadarChart = new Chart(ctx, {
    type: "radar",
    data: {
      labels,
      datasets: [
        {
          label: `Session ${A.id}`,
          data: aValues,
          fill: true,
          backgroundColor: "rgba(37,99,235,0.12)",
          borderColor: "rgba(37,99,235,0.9)",
        },
        {
          label: `Session ${B.id}`,
          data: bValues,
          fill: true,
          backgroundColor: "rgba(16,185,129,0.12)",
          borderColor: "rgba(16,185,129,0.9)",
        },
      ],
    },
    options: {
      scales: { r: { suggestedMin: 0, suggestedMax: 100 } },
      elements: { line: { borderWidth: 2 } },
    },
  });
}

function escapeHtml(str) {
  return str.replace(
    /[&<>"']/g,
    (m) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[
        m
      ])
  );
}

// ------------------- Export Utilities --------------------

function downloadBlob(filename, blob) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

// Export all sessions as CSV
function exportSessionsCSV() {
  const sessions = window._fiq_sessions || [];
  if (!sessions.length) return alert("No sessions to export.");

  // header
  const headers = [
    "id","timestamp","overall","fluency","grammar","coherence","readability",
    "posture","gaze","movement","word_count","sentence_count","avg_sentence_length","grammar_errors","transcript"
  ];

  const rows = sessions.map(s => [
    s.id,
    s.timestamp,
    s.overall ?? "",
    s.fluency ?? "",
    s.grammar ?? "",
    s.coherence ?? "",
    s.readability ?? "",
    s.posture ?? "",
    s.gaze ?? "",
    s.movement ?? "",
    s.word_count ?? "",
    s.sentence_count ?? "",
    s.avg_sentence_length ?? "",
    s.grammar_errors ?? "",
    `"${(s.transcript||"").replace(/"/g,'""')}"` // CSV-escape quotes
  ]);

  const csv = [headers.join(",")]
    .concat(rows.map(r => r.join(",")))
    .join("\n");

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  downloadBlob(`fluentiq_history_${new Date().toISOString().slice(0,19)}.csv`, blob);
}

// Export charts as PNG (two files: overall and radar if exists)
function exportChartsPNG() {
  // overall chart
  if (overallLineChart) {
    const url = document.getElementById("overallLineChart").toDataURL("image/png");
    // convert dataURL to blob
    fetch(url).then(res => res.blob()).then(blob => {
      downloadBlob(`overall_chart_${new Date().toISOString().slice(0,19)}.png`, blob);
    });
  } else {
    alert("Overall chart is not available.");
  }

  // radar chart (if exists)
  if (compareRadarChart) {
    const url2 = document.getElementById("compareRadarChart").toDataURL("image/png");
    fetch(url2).then(res => res.blob()).then(blob => {
      downloadBlob(`radar_chart_${new Date().toISOString().slice(0,19)}.png`, blob);
    });
  } else {
    // if no radar yet, still allow the user to create one (they can compare and then export)
    console.info("Radar chart not present; create a comparison then export PNG again.");
  }
}

// Export single session JSON
function exportSessionJSON() {
  const sel = document.getElementById("sessionExportSelect");
  const id = Number(sel.value);
  if (!id) return alert("Choose a session to export.");
  const sessions = window._fiq_sessions || [];
  const s = sessions.find(x => x.id === id);
  if (!s) return alert("Session not found.");

  const blob = new Blob([JSON.stringify(s, null, 2)], { type: "application/json" });
  downloadBlob(`session_${s.id}_${new Date().toISOString().slice(0,19)}.json`, blob);
}

// Hook export buttons after page init
(function attachExportHooks() {
  document.addEventListener("DOMContentLoaded", () => {
    const ecsv = document.getElementById("exportCsvBtn");
    const epng = document.getElementById("exportPngBtn");
    const exJson = document.getElementById("exportSessionJsonBtn");
    const sel = document.getElementById("sessionExportSelect");

    if (ecsv) ecsv.addEventListener("click", exportSessionsCSV);
    if (epng) epng.addEventListener("click", exportChartsPNG);
    if (exJson) exJson.addEventListener("click", exportSessionJSON);

    // populate session select with existing sessions (if available)
    // If sessions load after DOMContentLoaded, caller should re-run populateCompareSelects which also fills this select.
    if (window._fiq_sessions && sel) {
      sel.innerHTML = `<option value="">Select session to export JSON</option>`;
      window._fiq_sessions.forEach(s => {
        sel.innerHTML += `<option value="${s.id}">${s.id} — ${new Date(s.timestamp).toLocaleDateString()}</option>`;
      });
    }
  });
})();
