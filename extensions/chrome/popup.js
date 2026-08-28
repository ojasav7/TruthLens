/**
 * TruthLens Browser Extension — Popup
 */

const API_URL = "http://localhost:8000";
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const historyEl = document.getElementById("history");

// Check backend status
async function checkStatus() {
  try {
    const resp = await fetch(`${API_URL}/health`, { signal: AbortSignal.timeout(3000) });
    if (resp.ok) {
      statusEl.innerHTML = '<span style="color:#22c55e">● Connected</span>';
    } else {
      statusEl.innerHTML = '<span style="color:#ef4444">● Error</span>';
    }
  } catch {
    statusEl.innerHTML = '<span style="color:#ef4444">● Disconnected</span>';
  }
}

// Analyze text
document.getElementById("analyze-text")?.addEventListener("click", async () => {
  const text = document.getElementById("text-input").value.trim();
  if (!text) return;
  
  resultEl.innerHTML = '<div style="color:#94a3b8">Analyzing...</div>';
  
  try {
    const resp = await fetch(`${API_URL}/predict/text`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    
    if (resp.ok) {
      const data = await resp.json();
      const label = data.label || "unknown";
      const conf = data.confidence || 0;
      const color = label === "fake" ? "#ef4444" : "#22c55e";
      
      resultEl.innerHTML = `
        <div style="padding:12px; border-radius:8px; background:#0f172a; border:1px solid #334155;">
          <div style="font-size:18px; font-weight:700; color:${color};">${label.toUpperCase()}</div>
          <div style="color:#94a3b8; margin-top:4px;">Confidence: ${(conf * 100).toFixed(0)}%</div>
        </div>
      `;
      saveToHistory({ text: text.substring(0, 50), label, confidence: conf });
    }
  } catch (err) {
    resultEl.innerHTML = `<div style="color:#ef4444">Error: ${err.message}</div>`;
  }
});

// Analyze file upload
document.getElementById("file-input")?.addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  
  resultEl.innerHTML = '<div style="color:#94a3b8">Analyzing file...</div>';
  
  const formData = new FormData();
  formData.append("file", file);
  
  const isImage = file.type.startsWith("image/");
  const isVideo = file.type.startsWith("video/");
  const isAudio = file.type.startsWith("audio/");
  const endpoint = isImage ? "/predict/image" : isVideo ? "/predict/video" : isAudio ? "/predict/audio" : null;
  
  if (!endpoint) {
    resultEl.innerHTML = '<div style="color:#ef4444">Unsupported file type</div>';
    return;
  }
  
  try {
    const resp = await fetch(`${API_URL}${endpoint}`, { method: "POST", body: formData });
    if (resp.ok) {
      const data = await resp.json();
      const label = data.label || "unknown";
      const conf = data.confidence || 0;
      const color = label === "fake" || label === "cloned" ? "#ef4444" : "#22c55e";
      
      resultEl.innerHTML = `
        <div style="padding:12px; border-radius:8px; background:#0f172a; border:1px solid #334155;">
          <div style="font-size:18px; font-weight:700; color:${color};">${label.toUpperCase()}</div>
          <div style="color:#94a3b8; margin-top:4px;">Confidence: ${(conf * 100).toFixed(0)}%</div>
          <div style="color:#64748b; margin-top:2px; font-size:11px;">File: ${file.name}</div>
        </div>
      `;
      saveToHistory({ file: file.name, label, confidence: conf });
    }
  } catch (err) {
    resultEl.innerHTML = `<div style="color:#ef4444">Error: ${err.message}</div>`;
  }
});

// History
function saveToHistory(entry) {
  entry.timestamp = new Date().toISOString();
  chrome.storage?.local?.get("truthlens_history", (data) => {
    const history = data.truthlens_history || [];
    history.unshift(entry);
    chrome.storage.local.set({ truthlens_history: history.slice(0, 50) });
    renderHistory(history.slice(0, 10));
  });
}

function renderHistory(items) {
  if (!historyEl || !items?.length) return;
  historyEl.innerHTML = items.map(h => {
    const color = h.label === "fake" ? "#ef4444" : "#22c55e";
    return `<div style="padding:4px 0; border-bottom:1px solid #1e293b; font-size:11px;">
      <span style="color:${color};">${h.label}</span> — ${h.text || h.file || "media"}
    </div>`;
  }).join("");
}

// Load history
chrome.storage?.local?.get("truthlens_history", (data) => {
  renderHistory((data.truthlens_history || []).slice(0, 10));
});

// Init
checkStatus();
