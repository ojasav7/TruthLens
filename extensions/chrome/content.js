/**
 * TruthLens Browser Extension — Content Script
 * 
 * Adds a "🔍 Analyze" button on hover for images/videos on any webpage.
 * Sends media to TruthLens API for analysis.
 */

const API_URL = "http://localhost:8000";
let tooltip = null;

// Create floating analyze button
function createAnalyzeButton(element) {
  const btn = document.createElement("div");
  btn.className = "truthlens-btn";
  btn.innerHTML = "🔍 Analyze";
  btn.style.cssText = `
    position: absolute;
    top: 8px;
    right: 8px;
    background: rgba(6, 182, 212, 0.9);
    color: white;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    z-index: 10000;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    transition: all 0.2s;
  `;
  btn.onmouseenter = () => btn.style.background = "rgba(6, 182, 212, 1)";
  btn.onmouseleave = () => btn.style.background = "rgba(6, 182, 212, 0.9)";
  btn.onclick = (e) => {
    e.stopPropagation();
    analyzeElement(element);
  };
  return btn;
}

// Show analysis result tooltip
function showResult(element, result) {
  removeTooltip();
  const verdict = result.verdict || result.label || "unknown";
  const score = result.threat_score || result.confidence || 0;
  const color = verdict === "High Risk" || verdict === "fake" ? "#ef4444" 
    : verdict === "Review Needed" ? "#f59e0b" : "#22c55e";
  
  tooltip = document.createElement("div");
  tooltip.className = "truthlens-tooltip";
  tooltip.style.cssText = `
    position: absolute;
    top: 40px;
    right: 8px;
    background: #1e293b;
    color: #f1f5f9;
    padding: 12px 16px;
    border-radius: 8px;
    font-size: 13px;
    z-index: 10001;
    min-width: 200px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.4);
    border: 1px solid #334155;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  `;
  tooltip.innerHTML = `
    <div style="font-weight:700; color:${color}; font-size:15px; margin-bottom:6px;">
      ${verdict.toUpperCase()}
    </div>
    <div style="color:#94a3b8; font-size:12px;">
      Threat: ${typeof score === 'number' ? score.toFixed(0) : score}/100
    </div>
    <div style="margin-top:8px; font-size:11px; color:#64748b;">
      Powered by TruthLens
    </div>
  `;
  
  const container = element.closest("[style*='position']") || element.parentElement;
  container.style.position = "relative";
  container.appendChild(tooltip);
}

function removeTooltip() {
  if (tooltip) {
    tooltip.remove();
    tooltip = null;
  }
}

// Analyze an element (image or video)
async function analyzeElement(element) {
  const isImage = element.tagName === "IMG";
  const isVideo = element.tagName === "VIDEO";
  
  if (!isImage && !isVideo) return;
  
  try {
    let blob;
    if (isImage) {
      const response = await fetch(element.src);
      blob = await response.blob();
    } else {
      // For video, use first frame
      const canvas = document.createElement("canvas");
      canvas.width = element.videoWidth || 320;
      canvas.height = element.videoHeight || 240;
      canvas.getContext("2d").drawImage(element, 0, 0);
      blob = await new Promise(r => canvas.toBlob(r, "image/jpeg"));
    }

    const formData = new FormData();
    const ext = isImage ? "jpg" : "jpg";
    formData.append("file", blob, `truthlens_scan.${ext}`);

    const endpoint = isImage ? "/predict/image" : "/predict/video";
    const resp = await fetch(`${API_URL}${endpoint}`, { method: "POST", body: formData });
    
    if (resp.ok) {
      const result = await resp.json();
      showResult(element, result);
    } else {
      showResult(element, { verdict: "Error", confidence: 0 });
    }
  } catch (err) {
    showResult(element, { verdict: "API Unreachable", confidence: 0 });
  }
}

// Observe images/videos on page
function observeMedia() {
  const observer = new MutationObserver((mutations) => {
    mutations.forEach(m => {
      m.addedNodes.forEach(node => {
        if (node.nodeType !== 1) return;
        if (node.tagName === "IMG" || node.tagName === "VIDEO") addHover(node);
        node.querySelectorAll?.("img, video").forEach(addHover);
      });
    });
  });
  observer.observe(document.body, { childList: true, subtree: true });
}

function addHover(element) {
  if (element._truthlens) return;
  element._truthlens = true;
  element.style.position = "relative";
  
  element.addEventListener("mouseenter", () => {
    removeTooltip();
    const btn = createAnalyzeButton(element);
    element.parentElement.style.position = "relative";
    element.parentElement.appendChild(btn);
    btn.addEventListener("mouseleave", (e) => {
      setTimeout(() => { if (!tooltip) btn.remove(); }, 200);
    });
  });
}

// Init
document.querySelectorAll("img, video").forEach(addHover);
observeMedia();

// Listen for popup analysis requests
chrome.runtime.onMessage?.addListener((msg, sender, sendResponse) => {
  if (msg.action === "analyze_url") {
    fetch(msg.url).then(r => r.blob()).then(async blob => {
      const formData = new FormData();
      formData.append("file", blob, "upload.jpg");
      const resp = await fetch(`${API_URL}/predict/image`, { method: "POST", body: formData });
      sendResponse(await resp.json());
    }).catch(e => sendResponse({ error: e.message }));
    return true;
  }
});
