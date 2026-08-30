import { useState, useCallback, useEffect } from "react";
import type { KeyboardEvent } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Header from "./components/Header";
import InputPanel from "./components/InputPanel";
import EmptyState from "./components/EmptyState";
import ResultsPanel from "./components/ResultsPanel";
import ScanLoader from "./components/ScanLoader";
import LandingPage from "./pages/LandingPage";
import SettingsPage from "./pages/SettingsPage";
import { API_URL } from "./lib/utils";

interface AnalysisResult {
  id: string;
  threat_score: number;
  verdict: string;
  consistency: string;
  breakdown: Record<string, any>;
  trace_id?: string;
  input_types?: string[];
}

function Dashboard() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [inputText, setInputText] = useState<string | undefined>();
  const [error, setError] = useState<string | null>(null);
  const [backendStatus, setBackendStatus] = useState<"live" | "down" | "checking">("checking");

  useEffect(() => {
    // Retry with backoff to handle race condition on first load
    let cancelled = false;
    const check = (attempt: number) => {
      if (cancelled) return;
      fetch(`${API_URL}/health`, { signal: AbortSignal.timeout(5000) })
        .then((r) => {
          if (!cancelled) setBackendStatus(r.ok ? "live" : "down");
        })
        .catch(() => {
          if (!cancelled && attempt < 3) {
            setTimeout(() => check(attempt + 1), 1500 * (attempt + 1));
          } else if (!cancelled) {
            setBackendStatus("down");
          }
        });
    };
    check(0);
    // Also poll every 30s to auto-recover
    const interval = setInterval(() => check(0), 30000);
    return () => { cancelled = true; clearInterval(interval); };
  }, []);

  const handleAnalyze = useCallback(
    async (data: { text?: string; image?: File; video?: File; audio?: File }) => {
      setLoading(true);
      setError(null);
      setInputText(data.text);
      try {
        const formData = new FormData();
        if (data.text) formData.append("text", data.text);
        if (data.image) formData.append("image", data.image);
        if (data.video) formData.append("video", data.video);
        if (data.audio) formData.append("audio", data.audio);

        const resp = await fetch(`${API_URL}/analyze`, {
          method: "POST",
          body: formData,
        });

        if (!resp.ok) {
          const err = await resp.json().catch(() => ({ detail: resp.statusText }));
          throw new Error(err.detail || "Analysis failed");
        }

        const json = await resp.json();
        setResult(json);
      } catch (e: any) {
        setError(e.message || "Failed to connect to backend");
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.ctrlKey && e.key === "Enter" && !loading) {
      // Trigger via InputPanel's own handler
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground" onKeyDown={handleKeyDown}>
      <Header backendStatus={backendStatus} />
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid lg:grid-cols-[320px_1fr] gap-8">
          {/* Sidebar */}
          <aside>
            <InputPanel onAnalyze={handleAnalyze} loading={loading} />
          </aside>

          {/* Main */}
          <main>
            {error && (
              <div className="bg-destructive/10 border border-destructive/30 p-4 mb-6 text-sm text-destructive-foreground font-mono">
                {error}
              </div>
            )}
            {result ? (
              <ResultsPanel result={result} inputText={inputText} />
            ) : (
              !loading && <EmptyState />
            )}
            {loading && <ScanLoader text="Analyzing" />}
          </main>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </BrowserRouter>
  );
}
