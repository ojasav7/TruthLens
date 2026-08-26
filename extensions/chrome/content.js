// TruthLens content script — shows a floating analyze button on selected text

let btn = null;

document.addEventListener('mouseup', (e) => {
  const selection = window.getSelection().toString().trim();
  if (selection.length < 20) {
    if (btn) { btn.remove(); btn = null; }
    return;
  }

  if (!btn) {
    btn = document.createElement('div');
    btn.id = 'truthlens-fab';
    btn.textContent = '🔍 Analyze';
    btn.style.cssText = `
      position: fixed; z-index: 999999; top: ${e.clientY + 10}px; left: ${e.clientX + 10}px;
      background: #2563eb; color: white; padding: 6px 12px; border-radius: 6px;
      font-size: 12px; font-family: sans-serif; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    `;
    btn.addEventListener('click', async () => {
      const apiUrl = await new Promise(r => chrome.storage.local.get('apiUrl', r)).then(d => d.apiUrl || 'http://localhost:8000');
      try {
        const resp = await fetch(`${apiUrl}/predict/text`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: selection }),
        });
        const data = await resp.json();
        btn.textContent = `${data.label === 'fake' ? '🔴' : '🟢'} ${data.label} (${(data.confidence * 100).toFixed(0)}%)`;
        setTimeout(() => { if (btn) { btn.remove(); btn = null; } }, 3000);
      } catch (e) {
        btn.textContent = '❌ Error';
        setTimeout(() => { if (btn) { btn.remove(); btn = null; } }, 2000);
      }
    });
    document.body.appendChild(btn);
  } else {
    btn.style.top = `${e.clientY + 10}px`;
    btn.style.left = `${e.clientX + 10}px`;
    btn.textContent = '🔍 Analyze';
  }
});

document.addEventListener('mousedown', (e) => {
  if (btn && !btn.contains(e.target)) {
    btn.remove();
    btn = null;
  }
});
