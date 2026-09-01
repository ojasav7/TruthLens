import { useState } from "react";
import { useNavigate } from "react-router-dom";

interface Feature {
  id: string;
  title: string;
  description: string;
  icon: string;
  status: "active" | "beta" | "coming_soon";
  endpoint: string;
}

const FEATURES: Feature[] = [
  {
    id: "source-verify",
    title: "Source Verification",
    description: "Article source history, publication metadata, fact-check database lookup, reverse image search",
    icon: "🔍",
    status: "active",
    endpoint: "/source-verify/verify",
  },
  {
    id: "claim-extraction",
    title: "Claim Extraction",
    description: "Extract claims from text, match to known sources, compare media captions with actual content",
    icon: "📝",
    status: "active",
    endpoint: "/claims/extract",
  },
  {
    id: "review-workflow",
    title: "Review Workflow",
    description: "Reviewer comments, verdict reasons, confidence override, final case disposition, audit trail",
    icon: "👥",
    status: "active",
    endpoint: "/review/assign",
  },
  {
    id: "timeline",
    title: "Timeline Investigation",
    description: "Visual timeline of publication, edits, reposts, source propagation patterns",
    icon: "📅",
    status: "active",
    endpoint: "/timeline/create",
  },
  {
    id: "explainability",
    title: "Explainability",
    description: "Human-friendly explanations, SHAP-like feature importance, Grad-CAM attention maps",
    icon: "💡",
    status: "active",
    endpoint: "/explain",
  },
  {
    id: "contradiction-engine",
    title: "Contradiction Engine",
    description: "Cross-modal contradiction detection: text vs image, voice vs face, metadata vs content",
    icon: "⚡",
    status: "active",
    endpoint: "/contradictions/analyze",
  },
  {
    id: "calibration",
    title: "Calibration Dashboard",
    description: "Calibration curves, confidence distribution, false positive/negative tracking, per-modality performance",
    icon: "📊",
    status: "active",
    endpoint: "/calibration/dashboard",
  },
  {
    id: "benchmark",
    title: "Benchmark Layer",
    description: "Curated benchmark datasets, synthetic + real samples, edge-case categories, metrics reports",
    icon: "🎯",
    status: "active",
    endpoint: "/benchmark/evaluate",
  },
];

export default function AdvancedFeaturesPage() {
  const navigate = useNavigate();
  const [selectedFeature, setSelectedFeature] = useState<Feature | null>(null);
  const [testInput, setTestInput] = useState("");
  const [testResult, setTestResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const testFeature = async (feature: Feature) => {
    setLoading(true);
    setTestResult(null);

    try {
      let body: any = {};

      if (feature.id === "source-verify") {
        body = { url: testInput || "https://reuters.com" };
      } else if (feature.id === "claim-extraction") {
        body = { text: testInput || "Climate change is real according to NASA research" };
      } else if (feature.id === "review-workflow") {
        body = { analysis_id: testInput || "test-123", reviewer_id: "analyst-1" };
      } else if (feature.id === "timeline") {
        body = { content_id: testInput || "content-456" };
      } else if (feature.id === "explainability") {
        body = {
          modality: "text",
          prediction: { label: "fake", confidence: 0.85, signals: {} },
        };
      } else if (feature.id === "contradiction-engine") {
        body = {
          analysis_results: {
            text: { label: "real", confidence: 0.9 },
            image: { label: "fake", confidence: 0.8 },
          },
        };
      }

      const response = await fetch(`http://127.0.0.1:8000${feature.endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      const data = await response.json();
      setTestResult(data);
    } catch (error) {
      setTestResult({ error: "Failed to connect to backend. Make sure the server is running." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <div className="border-b border-border p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-4 mb-4">
            <button
              onClick={() => navigate("/dashboard")}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              ← Back to Dashboard
            </button>
          </div>
          <h1 className="text-4xl font-extrabold tracking-tighter uppercase mb-2">
            Advanced Features
          </h1>
          <p className="text-muted-foreground">
            8 cutting-edge capabilities for comprehensive misinformation investigation
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Features List */}
          <div className="lg:col-span-1 space-y-3">
            {FEATURES.map((feature) => (
              <button
                key={feature.id}
                onClick={() => setSelectedFeature(feature)}
                className={`w-full text-left p-4 border transition-all ${
                  selectedFeature?.id === feature.id
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-primary/50"
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{feature.icon}</span>
                  <div>
                    <div className="font-bold text-sm">{feature.title}</div>
                    <div className="text-xs text-muted-foreground line-clamp-1">
                      {feature.description}
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>

          {/* Feature Details */}
          <div className="lg:col-span-2">
            {selectedFeature ? (
              <div className="border border-border p-6">
                <div className="flex items-center gap-3 mb-6">
                  <span className="text-3xl">{selectedFeature.icon}</span>
                  <div>
                    <h2 className="text-2xl font-extrabold uppercase">
                      {selectedFeature.title}
                    </h2>
                    <p className="text-muted-foreground text-sm">
                      {selectedFeature.description}
                    </p>
                  </div>
                </div>

                {/* Test Input */}
                <div className="mb-6">
                  <label className="block text-xs font-mono text-primary uppercase tracking-widest mb-2">
                    Test Input
                  </label>
                  <input
                    type="text"
                    value={testInput}
                    onChange={(e) => setTestInput(e.target.value)}
                    placeholder="Enter test data (URL, text, or ID)"
                    className="w-full bg-muted border border-border p-3 font-mono text-sm focus:outline-none focus:border-primary"
                  />
                </div>

                {/* Test Button */}
                <button
                  onClick={() => testFeature(selectedFeature)}
                  disabled={loading}
                  className="px-6 py-3 bg-primary text-primary-foreground font-bold uppercase tracking-widest text-sm hover:brightness-110 transition-all disabled:opacity-50"
                >
                  {loading ? "Testing..." : "Test Feature"}
                </button>

                {/* Results */}
                {testResult && (
                  <div className="mt-6 border border-border p-4">
                    <div className="font-mono text-xs text-primary uppercase tracking-widest mb-3">
                      Result
                    </div>
                    <pre className="text-xs text-foreground overflow-auto max-h-96 font-mono whitespace-pre-wrap">
                      {JSON.stringify(testResult, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <div className="border border-border p-12 text-center">
                <div className="text-4xl mb-4">🎯</div>
                <h3 className="text-xl font-bold mb-2">Select a Feature</h3>
                <p className="text-muted-foreground text-sm">
                  Choose a feature from the list to test it
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Feature Grid */}
        <div className="mt-12 grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          {FEATURES.map((feature) => (
            <div
              key={feature.id}
              className="border border-border p-4 hover:border-primary/50 transition-colors"
            >
              <div className="text-2xl mb-2">{feature.icon}</div>
              <h3 className="font-bold text-sm mb-1">{feature.title}</h3>
              <p className="text-xs text-muted-foreground line-clamp-2">
                {feature.description}
              </p>
              <div className="mt-3">
                <span className="text-[10px] font-mono px-2 py-1 bg-primary/10 text-primary uppercase">
                  {feature.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
