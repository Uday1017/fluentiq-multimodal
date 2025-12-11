// frontend/assets/js/results.js
document.addEventListener("DOMContentLoaded", () => {
  const raw = localStorage.getItem("fluentiq_last_result");
  if (!raw) {
    alert("No result found in localStorage. Run an analysis first.");
    window.location.href = "index.html";
    return;
  }
  const data = JSON.parse(raw);

  // Show video if available (we didn't store file, but if backend served video url you'd show it)
  const videoWrap = document.getElementById("videoWrap");
  if (
    data &&
    data.audio &&
    data.audio.stats &&
    data.audio.stats.duration_seconds
  ) {
    videoWrap.innerHTML = `<div style="font-size:13px;color:#6b7280">Duration: ${data.audio.stats.duration_seconds}s</div>`;
  }

  // Summary cards
  const summaryCards = document.getElementById("summaryCards");
  const fused = data.fused || {};
  const items = [
    { label: "Overall", value: fused.overall ?? "-" },
    { label: "Fluency", value: fused.fluency ?? "-" },
    { label: "Grammar", value: fused.grammar ?? "-" },
    { label: "Posture", value: fused.video ? fused.video.posture : "-" },
    { label: "Gaze", value: fused.video ? fused.video.gaze : "-" },
  ];
  summaryCards.innerHTML = "";
  items.forEach((i) => {
    const el = document.createElement("div");
    el.className = "summary-card";
    el.innerHTML = `<div class="value">${i.value}</div><div class="label">${i.label}</div>`;
    summaryCards.appendChild(el);
  });

  // Transcript
  document.getElementById("transcript").innerText =
    data.transcript || data.text?.transcript || "";

  // Radar chart: build labels & values
  const radarCtx = document.getElementById("radarChart").getContext("2d");
  const radarLabels = [
    "Fluency",
    "Grammar",
    "Coherence",
    "Readability",
    "Posture",
    "Gaze",
    "Overall",
  ];
  const radarValues = [
    fused.fluency || 0,
    fused.grammar || 0,
    fused.coherence || 0,
    Math.round(fused.readability || 0),
    fused.video ? fused.video.posture || 0 : 0,
    fused.video ? fused.video.gaze || 0 : 0,
    fused.overall || 0,
  ];
  window._radar = new Chart(radarCtx, {
    type: "radar",
    data: {
      labels: radarLabels,
      datasets: [
        {
          label: "Session",
          data: radarValues,
          fill: true,
          backgroundColor: "rgba(37,99,235,0.12)",
          borderColor: "#2563eb",
        },
      ],
    },
    options: { scales: { r: { suggestedMin: 0, suggestedMax: 100 } } },
  });

  // Bar chart for components
  const barCtx = document.getElementById("barChart").getContext("2d");
  const barLabels = ["Fluency", "Grammar", "Coherence", "Readability"];
  const barData = [
    fused.fluency || 0,
    fused.grammar || 0,
    fused.coherence || 0,
    Math.round(fused.readability || 0),
  ];
  window._bar = new Chart(barCtx, {
    type: "bar",
    data: {
      labels: barLabels,
      datasets: [
        {
          label: "Scores",
          data: barData,
          backgroundColor: ["#60a5fa", "#60a5fa", "#93c5fd", "#a5b4fc"],
        },
      ],
    },
    options: {
      indexAxis: "y",
      scales: { x: { min: 0, max: 100 } },
      plugins: { legend: { display: false } },
    },
  });

  // Feedback area (show text feedback from text.analysis if available)
  const fb = document.getElementById("feedbackArea");
  fb.innerHTML = "";

  if (data.text && data.text.highlights) {
    const h = data.text.highlights;
    const section = document.createElement("div");
    section.innerHTML = `<strong>Highlights</strong>`;
    const ul = document.createElement("ul");
    Object.keys(h).forEach((k) => {
      const li = document.createElement("li");
      li.textContent = h[k];
      ul.appendChild(li);
    });
    section.appendChild(ul);
    fb.appendChild(section);
  }

  // Add suggested plan (we can craft a simple plan based on scores)
  const plan = document.createElement("div");
  plan.innerHTML = `<h4>Suggested Practice Plan</h4>
    <ol>
      <li>Week 1: Focus on fluency — record 1-minute speeches and remove fillers.</li>
      <li>Week 2: Grammar & phrasing — revise scripts and practice slowed articulation.</li>
      <li>Week 3: Non-verbal — practice posture & eye-contact with webcam recording.</li>
      <li>Week 4: Combine and rehearse complete talk; use peer feedback.</li>
    </ol>`;
  fb.appendChild(plan);

  // Export / navigation hooks
  document.getElementById("exportJsonBtn").addEventListener("click", () => {
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `fluentiq_session_${new Date()
      .toISOString()
      .slice(0, 19)}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  });

  document.getElementById("exportPngBtn").addEventListener("click", () => {
    // export radar chart and bar chart sequentially
    const radarCanvas = document.getElementById("radarChart");
    const barCanvas = document.getElementById("barChart");
    [radarCanvas, barCanvas].forEach((c, idx) => {
      const url = c.toDataURL("image/png");
      fetch(url)
        .then((res) => res.blob())
        .then((blob) => {
          const a = document.createElement("a");
          a.href = URL.createObjectURL(blob);
          a.download = `fluentiq_chart_${idx}_${new Date()
            .toISOString()
            .slice(0, 19)}.png`;
          document.body.appendChild(a);
          a.click();
          a.remove();
        });
    });
  });

  document.getElementById("openHistoryBtn").addEventListener("click", () => {
    window.location.href = "history.html";
  });
});
