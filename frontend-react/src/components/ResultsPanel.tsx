import { useState } from "react";
import ThreatGauge from "./ThreatGauge";
import VerdictBadge from "./VerdictBadge";
import ModalityCard from "./ModalityCard";
import { API_URL } from "../lib/utils";

interface AnalysisResult {
  id: string;
  threat_score: number;
  verdict: string;
  consistency: string;
  breakdown: Record<
    string,
    {
      label: string;
      confidence: number;
      threat_contribution: number;
      weight: number;
    } | null
  >;
  timestamp?: string;
  input_types?: string[];
}

interface ResultsPanelProps {
  result: AnalysisResult;
}

export default function ResultsPanel({ result }: ResultsPanelProps) {
  const [showExplain, setShowExplain] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<any>(null);
  const [loadingExplain, setLoadingExplain] = useState(false);

  const { threat_score, verdict, consistency, breakdown, id } = result;

  // Filter active modalities
  const modalities = Object.entries(breakdown)
    .filter(([, v]) => v && "label" in v)
    .map(([key, v]) => ({
      modality: key.toUpperCase(),
      label: (v as any).label,
      confidence: (v as any).confidence || 0,
      threat: (v as any).threat_contribution || 0,
    }));

  const handleExplain = async (modality: string) => {
    setShowExplain(modality);
    setLoadingExplain(true);
    setExplanation(null);
    try {
      const r = await fetch(`${API_URL}/predict/${modality}/explain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: "sample", top_k: 10 }),
      });
      if (r.ok) setExplanation(await r.json());
    } catch {
      // ignore
    } finally {
      setLoadingExplain(false);
    }
  };

  return (
    <div className="animate-fade-in-up space-y-6">
      {/* Threat Overview */}
      <div className="grid grid-cols-[2fr_1fr] gap-6">
        <div className="bg-bg-surface border border-border-default rounded-xl p-5">
          <ThreatGauge score={threat_score} />
        </div>
        <div className="flex flex-col items-center justify-center gap-4">
          <VerdictBadge verdict={verdict} score={threat_score} />
          <p className="text-sm text-text-secondary">
            Consistency: <span className="font-semibold">{consistency}</span>
          </p>
          {threat_score >= 30 && (
            <div className="w-full p-3 bg-amber/8 border border-amber/30 rounded-lg text-sm text-amber font-medium">
              ⚠️ Review recommended
            </div>
          )}
        </div>
      </div>

      {/* Modality Breakdown */}
      <div>
        <h3 className="text-sm font-bold uppercase tracking-wider text-text-primary mb-3">
          📊 Modality Breakdown
        </h3>
        <div className="space-y-3">
          {modalities.map((m) => (
            <ModalityCard key={m.modality} {...m} />
          ))}
        </div>
      </div>

      {/* Explanations */}
      <div>
        <h3 className="text-sm font-bold uppercase tracking-wider text-text-primary mb-3">
          🔍 Explanations
        </h3>
        <div className="flex gap-2 mb-3">
          {["text", "image", "video", "audio"].map((m) => (
            <button
              key={m}
              onClick={() => handleExplain(m)}
              className={`px-4 py-2 text-sm font-medium rounded-lg border transition-all ${
                showExplain === m
                  ? "bg-cyan-glow border-cyan text-cyan"
                  : "bg-bg-surface border-border-default text-text-secondary hover:border-border-active"
              }`}
            >
              {m === "text" && "📝 "}
              {m === "image" && "🖼️ "}
              {m === "video" && "🎬 "}
              {m === "audio" && "🔊 "}
              {m.charAt(0).toUpperCase() + m.slice(1)}
            </button>
          ))}
        </div>
        {loadingExplain && (
          <div className="p-4 bg-bg-surface border border-border-default rounded-lg text-sm text-text-secondary">
            Loading explanation…
          </div>
        )}
        {explanation && !loadingExplain && (
          <div className="p-4 bg-bg-surface border border-border-default rounded-lg">
            <pre className="text-xs text-text-secondary overflow-x-auto">
              {JSON.stringify(explanation, null, 2)}
            </pre>
          </div>
        )}
      </div>

      {/* Evidence Chain */}
      <div className="bg-bg-surface border border-border-default rounded-xl p-5">
        <h3 className="text-sm font-bold uppercase tracking-wider text-text-primary mb-3">
          🔗 Evidence Chain
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-text-tertiary mb-1">Analysis ID</p>
            <p className="text-sm font-mono text-text-primary break-all">{id}</p>
          </div>
          <div>
            <p className="text-xs text-text-tertiary mb-1">Modalities</p>
            <p className="text-sm text-text-primary">
              {Object.keys(breakdown).join(", ")}
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="text-center text-xs text-text-tertiary border-t border-border-default pt-4">
        AI-generated analysis — verify independently. TruthLens v2.0.0
      </div>
    </div>
  );
}
