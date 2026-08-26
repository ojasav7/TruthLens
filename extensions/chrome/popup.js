// TruthLens Browser Extension — popup.js

const textEl = document.getElementById('text');
const analyzeBtn = document.getElementById('analyzeBtn');
const pageBtn = document.getElementById('pageBtn');
const resultEl = document.getElementById('result');
const apiUrlEl = document.getElementById('apiUrl');
const statusEl = document.getElementById('status');

// Load saved API URL
chrome.storage.local.get('apiUrl', (data) => {
  apiUrlEl.value = data.apiUrl || 'http://localhost:8000';
});

apiUrlEl.addEventListener('change', () => {
  chrome.storage.local.set({ apiUrl: apiUrlEl.value });
});

analyzeBtn.addEventListener('click', async () => {
  const text = textEl.value.trim();
  if (!text) return;

  analyzeBtn.disabled = true;
  statusEl.textContent = 'Analyzing...';
  resultEl.innerHTML = '';

  try {
    const resp = await fetch(`${apiUrlEl.value}/predict/text`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    const data = await resp.json();
    const cls = data.label === 'fake' ? 'fake' : 'real';
    resultEl.innerHTML = `
      <div class="result ${cls}">
        <div class="label">${data.label === 'fake' ? '🔴' : '🟢'} ${data.label.toUpperCase()}</div>
        <div class="confidence">${(data.confidence * 100).toFixed(1)}% confidence</div>
      </div>`;
    statusEl.textContent = '';
  } catch (e) {
    statusEl.textContent = `Error: ${e.message}`;
  }
  analyzeBtn.disabled = false;
});

pageBtn.addEventListener('click', async () => {
  // Get active tab and extract text
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return;

  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => document.body.innerText.substring(0, 3000),
    });
    const pageText = results[0]?.result || '';
    textEl.value = pageText;
    analyzeBtn.click();
  } catch (e) {
    statusEl.textContent = `Error reading page: ${e.message}`;
  }
});
