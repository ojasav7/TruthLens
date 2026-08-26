// TruthLens background service worker — handles context menu

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'truthlens-analyze',
    title: '🔍 Analyze with TruthLens',
    contexts: ['selection'],
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'truthlens-analyze' && info.selectionText) {
    // Store selected text and open popup
    chrome.storage.local.set({ selectedText: info.selectionText });
    chrome.action.openPopup();
  }
});
