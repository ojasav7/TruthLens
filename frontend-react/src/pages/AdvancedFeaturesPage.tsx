import { useState } from "react";
import { useNavigate } from "react-router-dom";

const FEATURES = [
  { id: "source", icon: "🔍", title: "Source Verification", desc: "Credibility, provenance chain, fact-check DB" },
  { id: "claims", icon: "📝", title: "Claim Extraction", desc: "Extract claims, match to evidence" },
  { id: "review", icon: "👥", title: "Review Workflow", desc: "Reviewer comments, verdict overrides, audit trail" },
  { id: "timeline", icon: "📅", title: "Timeline Investigation", desc: "Publication, edits, shares, propagation" },
  { id: "explain", icon: "💡", title: "Explainability", desc: "Human-friendly model explanations" },
  { id: "contradiction", icon: "⚡", title: "Contradiction Engine", desc: "Cross-modal contradiction detection" },
  { id: "calibration", icon: "📊", title: "Calibration Dashboard", desc: "Confidence tracking, per-modality metrics" },
  { id: "benchmark", icon: "🎯", title: "Benchmark Layer", desc: "Dataset evaluation, metrics reports" },
];

export default function AdvancedFeaturesPage() {
  const navigate = useNavigate();
  const [selected, setSelected] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const testFeature = async (id: string) => {
    setLoading(true);
    setResult(null);
    setSelected(id);
    try {
      const body: Record<string, any> = {
        source: { url: "https://reuters.com" },
        claims: { text: "Climate change is real according to NASA research" },
        review: { analysis_id: "test-123", reviewer_id: "analyst-1" },
        explain: { modality: "text", prediction: { label: "fake", confidence: 0.85, signals: {} } },
        contradiction: { analysis_results: { text: { label: "real", confidence: 0.9 }, image: { label: "fake", confidence: 0.8 } } },
      };
      const endpoint = `/advanced/${id === "source" ? "source-verify" : id}`;
      const resp = await fetch(`http://127.0.0.1:8000${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body[id] || {}),
      });
      setResult(await resp.json());
    } catch {
      setResult({ error: "Backend not running. Start with: python -m uvicorn backend.main:app --port 8000" });
    } finally {
      setLoading(false);
    }
  };

  const testGet = async (id: string) => {
    setLoading(true);
    setResult(null);
    setSelected(id);
    try {
      const endpoint = `/advanced/${id}`;
      const resp = await fetch(`http://127.0.0.1:8000${endpoint}`);
      setResult(await resp.json());
    } catch {
      setResult({ error: "Backend not running" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="border-b border-border p-6">
        <div className="max-w-7xl mx-auto">
          <button onClick={() => navigate("/dashboard")} className="text-muted-foreground hover:text-foreground mb-4 block">
            ← Back to Dashboard
          </button>
          <h1 className="text-4xl font-extrabold tracking-tighter uppercase mb-2">Advanced Features</h1>
          <p className="text-muted-foreground">8 capabilities for misinformation investigation</p>
        </div>
      </div>
      <div className="max-w-7xl mx-auto p-6 grid md:grid-cols-2 lg:grid-cols-4 gap-4">
        {FEATURES.map((f) => (
          <button
            key={f.id}
            onClick={() => ["calibration", "benchmark"].includes(f.id) ? testGet(f.id) : testFeature(f.id)}
            disabled={loading}
            className={`text-left p-4 border transition-all ${selected === f.id ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"} ${loading ? "opacity-50" : ""}`}
          >
            <div className="text-2xl mb-2">{f.icon}</div>
            <h3 className="font-bold text-sm mb-1">{f.title}</h3>
            <p className="text-xs text-muted-foreground">{f.desc}</p>
          </button>
        ))}
      </div>
      {result && (
        <div className="max-w-7xl mx-auto p-6">
          <div className="border border-border p-4">
            <div className="font-mono text-xs text-primary uppercase tracking-widest mb-3">Result</div>
            <pre className="text-xs text-foreground overflow-auto max-h-64 font-mono whitespace-pre-wrap">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
