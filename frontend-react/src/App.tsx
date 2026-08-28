import { useState, useCallback } from "react";
import Header from "./components/Header";
import InputPanel from "./components/InputPanel";
import EmptyState from "./components/EmptyState";
import ResultsPanel from "./components/ResultsPanel";
import { API_URL } from "./lib/utils";

interface AnalysisResult {
  id: string;
  threat_score: number;
  verdict: string;
  consistency: string;
  breakdown: Record<string, any>;
  timestamp?: string;
  input_types?: string[];
}

export default function App() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = useCallback(
    async (data: { text?: string; image?: File; video?: File; audio?: File }) => {
      setLoading(true);
      setError(null);
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

  return (
    <div className="flex flex-col h-screen bg-bg-primary">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <InputPanel onAnalyze={handleAnalyze} disabled={loading} />

        <main className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="flex flex-col items-center justify-center h-full gap-4 animate-fade-in-up">
              <div className="w-10 h-10 border-3 border-cyan border-t-transparent rounded-full animate-spin" />
              <p className="text-sm text-text-secondary">Analyzing across modalities…</p>
            </div>
          )}

          {error && (
            <div className="flex items-center gap-3 p-4 bg-crimson/10 border border-crimson/30 rounded-lg text-crimson text-sm animate-fade-in-up">
              ⚠️ {error}
            </div>
          )}

          {!loading && !error && !result && <EmptyState />}

          {!loading && result && <ResultsPanel result={result} />}
        </main>
      </div>
    </div>
  );
}
