// frontend/assets/js/upload.js
const BASE = "http://127.0.0.1:8000";
const fileInput = document.getElementById("fileInput");
const submitBtn = document.getElementById("submitBtn");
const resetBtn = document.getElementById("resetBtn");
const fileMeta = document.getElementById("fileMeta");
const fileNameEl = document.getElementById("fileName");
const previewVideo = document.getElementById("previewVideo");
const progressWrap = document.getElementById("progressWrap");
const progressBar = document.getElementById("progressBar");
const progressText = document.getElementById("progressText");
const statusMsg = document.getElementById("statusMsg");

let selectedFile = null;

fileInput.addEventListener("change", (e) => {
  const f = e.target.files[0];
  if (!f) return;
  selectedFile = f;
  fileMeta.style.display = "flex";
  fileNameEl.textContent = f.name;
  if (f.type.startsWith("video/")) {
    previewVideo.src = URL.createObjectURL(f);
    previewVideo.style.display = "block";
  } else {
    previewVideo.style.display = "none";
  }
  submitBtn.disabled = false;
  resetBtn.style.display = "inline-block";
});

resetBtn.addEventListener("click", () => {
  fileInput.value = "";
  selectedFile = null;
  fileMeta.style.display = "none";
  submitBtn.disabled = true;
  resetBtn.style.display = "none";
  progressWrap.style.display = "none";
  progressBar.style.width = "0%";
  statusMsg.innerText = "";
});

// upload and call backend
submitBtn.addEventListener("click", async () => {
  if (!selectedFile) return alert("Select a file first");
  submitBtn.disabled = true;
  progressWrap.style.display = "block";
  progressBar.style.width = "4%";
  progressText.innerText = "Preparing…";

  try {
    const form = new FormData();
    form.append("file", selectedFile, selectedFile.name);

    // Use fetch with XHR-like progress via XMLHttpRequest
    await uploadWithProgress(
      `${BASE}/analyze/audio`,
      form,
      (percent, state) => {
        progressBar.style.width = `${percent}%`;
        progressText.innerText = state;
      }
    )
      .then((resJson) => {
        // save to localStorage for results page
        localStorage.setItem("fluentiq_last_result", JSON.stringify(resJson));
        // navigate to results page
        window.location.href = "results.html";
      })
      .catch((err) => {
        console.error(err);
        statusMsg.innerText = "Analysis failed: " + (err.message || err);
        submitBtn.disabled = false;
      });
  } catch (err) {
    console.error(err);
    statusMsg.innerText = "Upload error: " + err.message;
    submitBtn.disabled = false;
  }
});

function uploadWithProgress(url, formData, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", url, true);

    xhr.onload = function () {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const data = JSON.parse(xhr.responseText);
          onProgress(100, "Processing finished");
          resolve(data);
        } catch (e) {
          reject(e);
        }
      } else {
        reject(new Error(`Server responded ${xhr.status}: ${xhr.statusText}`));
      }
    };

    xhr.onerror = function () {
      reject(new Error("Network error"));
    };

    xhr.upload.onprogress = function (e) {
      if (e.lengthComputable) {
        const percent = Math.round((e.loaded / e.total) * 80); // upload portion => 0-80
        onProgress(percent, `Uploading ${percent}%`);
      } else {
        onProgress(20, "Uploading…");
      }
    };

    // Poll server-side progress — optional: your backend currently doesn't emit progress,
    // so we'll simulate post-upload processing progress animation until server responds.
    let fake = 80;
    const interval = setInterval(() => {
      if (fake < 96) {
        fake += 3;
        onProgress(fake, "Analyzing…");
      }
    }, 700);

    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        clearInterval(interval);
      }
    };

    xhr.send(formData);
  });
}
