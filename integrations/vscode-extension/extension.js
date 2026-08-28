const vscode = require("vscode");
const https = require("https");
const http = require("http");

function activate(context) {
  const config = vscode.workspace.getConfiguration("truthlens");
  let apiUrl = config.get("apiUrl", "http://localhost:8000");

  // Analyze selected text
  const analyzeCmd = vscode.commands.registerCommand(
    "truthlens.analyze",
    async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showWarningMessage("No active editor");
        return;
      }

      const selection = editor.document.getText(editor.selection);
      if (!selection) {
        vscode.window.showWarningMessage("Select text to analyze");
        return;
      }

      await analyzeText(selection);
    }
  );

  // Analyze entire file
  const analyzeFileCmd = vscode.commands.registerCommand(
    "truthlens.analyzeFile",
    async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) return;

      const text = editor.document.getText();
      if (text.length > 10000) {
        vscode.window.showWarningMessage("File too large, analyzing first 10,000 chars");
      }
      await analyzeText(text.substring(0, 10000));
    }
  );

  // Set API URL
  const setUrlCmd = vscode.commands.registerCommand(
    "truthlens.setApiUrl",
    async () => {
      const url = await vscode.window.showInputBox({
        prompt: "Enter TruthLens API URL",
        value: apiUrl,
        placeHolder: "http://localhost:8000",
      });
      if (url) {
        apiUrl = url;
        config.update("apiUrl", url);
        vscode.window.showInformationMessage(`TruthLens API set to ${url}`);
      }
    }
  );

  context.subscriptions.push(analyzeCmd, analyzeFileCmd, setUrlCmd);

  async function analyzeText(text) {
    const progress = vscode.window.withProgress(
      { location: vscode.ProgressLocation.Notification, title: "TruthLens Analyzing..." },
      async () => {
        try {
          const result = await postAnalysis(text);
          showResult(result, text);
        } catch (err) {
          vscode.window.showErrorMessage(`TruthLens: ${err.message}`);
        }
      }
    );
  }

  function postAnalysis(text) {
    return new Promise((resolve, reject) => {
      const url = new URL(`${apiUrl}/analyze`);
      const client = url.protocol === "https:" ? https : http;

      const postData = `text=${encodeURIComponent(text)}`;
      const req = client.request(
        {
          hostname: url.hostname,
          port: url.port,
          path: url.pathname,
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": Buffer.byteLength(postData),
          },
        },
        (res) => {
          let data = "";
          res.on("data", (chunk) => (data += chunk));
          res.on("end", () => {
            try {
              resolve(JSON.parse(data));
            } catch {
              reject(new Error("Invalid API response"));
            }
          });
        }
      );

      req.on("error", reject);
      req.write(postData);
      req.end();
    });
  }

  function showResult(result, originalText) {
    const score = result.threat_score;
    const verdict = result.verdict;

    let icon, color;
    if (verdict === "Low") {
      icon = "$(pass)";
      color = new vscode.ThemeColor("testing.iconPassed");
    } else if (verdict === "Review Needed") {
      icon = "$(warning)";
      color = new vscode.ThemeColor("editorWarning.foreground");
    } else {
      icon = "$(error)";
      color = new vscode.ThemeColor("editorError.foreground");
    }

    const channel = vscode.window.createOutputChannel("TruthLens");
    channel.clear();
    channel.appendLine("=== TruthLens Analysis ===");
    channel.appendLine(`Verdict:     ${verdict}`);
    channel.appendLine(`Score:       ${score}/100`);
    channel.appendLine(`Trace ID:    ${result.trace_id || "N/A"}`);
    channel.appendLine("");
    channel.appendLine("--- Breakdown ---");

    for (const [mod, detail] of Object.entries(result.breakdown || {})) {
      if (detail && detail.label) {
        channel.appendLine(`  ${mod.toUpperCase()}: ${detail.label} (${(detail.confidence * 100).toFixed(1)}%)`);
      }
    }

    channel.appendLine("");
    channel.appendLine("--- Original Text ---");
    channel.appendLine(originalText.substring(0, 200));
    channel.show();

    vscode.window.showInformationMessage(
      `${icon} TruthLens: ${verdict} (${score}/100)`
    );
  }
}

function deactivate() {}

module.exports = { activate, deactivate };
