import { useState } from "react";
import { useNavigate } from "react-router-dom";

const API = "http://127.0.0.1:8000";

const FEATURES = [
  { id: "source", icon: "🔍", title: "Source Verification", desc: "Credibility, provenance chain, fact-check DB", method: "POST" as const, endpoint: "/advanced/source-verify" },
  { id: "claims", icon: "📝", title: "Claim Extraction", desc: "NLP claim extraction (bart-large-mnli)", method: "POST" as const, endpoint: "/advanced/claims/extract" },
  { id: "review", icon: "👥", title: "Review Workflow", desc: "Assign reviewers, override verdicts, audit trail", method: "POST" as const, endpoint: "/advanced/review/assign" },
  { id: "timeline", icon: "📅", title: "Timeline", desc: "Publication, edits, shares, propagation", method: "POST" as const, endpoint: "/advanced/timeline/event" },
  { id: "explain", icon: "💡", title: "Explainability", desc: "Human-friendly model explanations", method: "POST" as const, endpoint: "/advanced/explain" },
  { id: "contradiction", icon: "⚡", title: "Contradictions", desc: "Cross-modal contradiction detection", method: "POST" as const, endpoint: "/advanced/contradictions" },
  { id: "calibration", icon: "📊", title: "Calibration", desc: "Confidence tracking, per-modality metrics", method: "GET" as const, endpoint: "/advanced/calibration/dashboard" },
  { id: "benchmark", icon: "🎯", title: "Benchmark", desc: "Dataset evaluation, metrics reports", method: "GET" as const, endpoint: "/advanced/benchmark/summary" },
];

const SAMPLE_BODIES: Record<string, any> = {
  source: { url: "https://reuters.com" },
  claims: { text: "Climate change is real according to NASA research shows. The earth is flat according to conspiracy theorists." },
  review: { analysis_id: `case-${Date.now()}`, reviewer_id: "analyst-1" },
  timeline: { content_id: `content-${Date.now()}`, event_type: "publication", source: "Reuters" },
  explain: { modality: "text", prediction: { label: "fake", confidence: 0.85, signals: { emotional_appeal: 0.7, fact_check_score: 0.2 } } },
  contradiction: { analysis_results: { text: { label: "real", confidence: 0.9 }, image: { label: "fake", confidence: 0.8 } } },
};

export default function AdvancedFeaturesPage() {
  const navigate = useNavigate();
  const [selected, setSelected] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const testFeature = async (id: string) => {
    setLoading(true);
    setResult(null);
    setError(null);
    setSelected(id);
    const feature = FEATURES.find(f => f.id === id)!;
    try {
      if (feature.method === "GET") {
        const r = await fetch(`${API}${feature.endpoint}`);
        if (!r.ok) throw new Error(`${r.status}`);
        setResult(await r.json());
      } else {
        const body = SAMPLE_BODIES[id] || {};
        const r = await fetch(`${API}${feature.endpoint}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        if (!r.ok) throw new Error(`${r.status}`);
        setResult(await r.json());
      }
    } catch (e: any) {
      setError(e.message === "Failed to fetch" ? "Backend not running — start with: python -m uvicorn backend.main:app --port 8000" : `Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="border-b border-border p-6">
        <div className="max-w-7xl mx-auto">
          <button onClick={() => navigate("/dashboard")} className="text-muted-foreground hover:text-foreground mb-4 block text-sm">
            ← Back to Dashboard
          </button>
          <h1 className="text-4xl font-extrabold tracking-tighter uppercase mb-2">Advanced Features</h1>
          <p className="text-muted-foreground text-sm">8 production capabilities for misinformation investigation</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6 grid lg:grid-cols-[320px_1fr] gap-8">
        {/* Sidebar */}
        <div className="space-y-2">
          {FEATURES.map(f => (
            <button
              key={f.id}
              onClick={() => testFeature(f.id)}
              disabled={loading}
              className={`w-full text-left p-4 border transition-all ${
                selected === f.id ? "border-primary bg-primary/5" : "border-border hover:border-primary/30"
              } ${loading ? "opacity-50" : ""}`}
            >
              <div className="flex items-center gap-3">
                <span className="text-xl">{f.icon}</span>
                <div>
                  <div className="font-bold text-sm">{f.title}</div>
                  <div className="text-xs text-muted-foreground">{f.desc}</div>
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* Main */}
        <div>
          {error && (
            <div className="bg-destructive/10 border border-destructive/30 p-4 mb-6 text-sm text-destructive-foreground font-mono">
              {error}
            </div>
          )}
          {result && (
            <div className="border border-border p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="font-mono text-xs text-primary uppercase tracking-widest">
                  {FEATURES.find(f => f.id === selected)?.title} — Result
                </div>
                <span className="text-xs font-mono px-2 py-1 bg-primary/10 text-primary">200 OK</span>
              </div>
              <pre className="text-xs text-foreground overflow-auto max-h-[500px] font-mono whitespace-pre-wrap bg-muted/30 p-4">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
          {!result && !error && !loading && (
            <div className="border border-border p-12 text-center">
              <div className="text-4xl mb-4">🎯</div>
              <h3 className="text-xl font-bold mb-2">Select a Feature</h3>
              <p className="text-muted-foreground text-sm">Click any feature in the sidebar to test it</p>
            </div>
          )}
          {loading && (
            <div className="border border-border p-12 text-center">
              <div className="text-4xl mb-4 animate-pulse">⏳</div>
              <p className="text-muted-foreground text-sm">Testing...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
