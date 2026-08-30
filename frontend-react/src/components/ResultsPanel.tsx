import ThreatGauge from "./ThreatGauge";
import VerdictBadge from "./VerdictBadge";
import ModalityCard from "./ModalityCard";

interface ResultsPanelProps {
  result: {
    id: string;
    threat_score: number;
    verdict: string;
    consistency: string;
    breakdown: Record<string, any>;
    trace_id?: string;
    input_types?: string[];
  };
}

function generateSummary(result: ResultsPanelProps["result"]): { icon: string; color: string; title: string; body: string; tip: string } {
  const score = result.threat_score;
  const verdict = result.verdict.toLowerCase();
  const breakdown = result.breakdown || {};
  const modalities = Object.keys(breakdown).filter((k) => breakdown[k] !== null);
  const modalityList = modalities.map((m) => m.charAt(0).toUpperCase() + m.slice(1)).join(" and ");

  if (verdict.includes("high risk") || score > 70) {
    const textLabel = breakdown.text?.label;
    const imageLabel = breakdown.image?.label;
    const reasons: string[] = [];
    if (textLabel === "fake") reasons.push("the text contains patterns commonly found in fake news or misinformation");
    if (imageLabel === "fake") reasons.push("the image shows signs of digital manipulation or AI generation");
    if (breakdown.audio?.label === "cloned" || breakdown.audio?.label === "fake") reasons.push("the audio has artifacts consistent with AI-generated or cloned voice");
    const reasonStr = reasons.length > 0 ? ` Specifically, ${reasons.join("; ")}.` : "";
    return {
      icon: "\u26A0\uFE0F",
      color: "destructive",
      title: "This content is likely fake or manipulated",
      body: `Our analysis found strong signs that this ${modalityList || "content"} is not authentic. The system is ${Math.round(score)}% confident this is a threat.${reasonStr}`,
      tip: "We recommend verifying this content through official sources before sharing it.",
    };
  }

  if (verdict.includes("low risk") || verdict.includes("review") || (score > 30 && score <= 70)) {
    return {
      icon: "\uD83D\uDD0D",
      color: "amber",
      title: "This content looks suspicious but we're not sure",
      body: `Our analysis found some unusual patterns in this ${modalityList || "content"}, but we can't say for certain whether it's real or fake. The system is ${Math.round(score)}% uncertain.`,
      tip: "Double-check the source. If it's from a trusted outlet, it's probably fine. If it's from social media, look for corroboration.",
    };
  }

  return {
    icon: "\u2705",
    color: "primary",
    title: "This content appears to be authentic",
    body: `Our analysis found no significant signs of manipulation in this ${modalityList || "content"}. The system is ${Math.round(100 - score)}% confident this is genuine.`,
    tip: "No tool is 100% certain. If this content makes an extraordinary claim, it's still worth checking a second source.",
  };
}

export default function ResultsPanel({ result }: ResultsPanelProps) {
  const breakdown = result.breakdown || {};
  const summary = generateSummary(result);
  const modalities = Object.entries(breakdown)
    .filter(([_, v]) => v !== null && v !== undefined)
    .map(([type, data]: [string, any]) => ({
      type,
      label: type.charAt(0).toUpperCase() + type.slice(1),
      confidence: data?.confidence ?? 0,
      threatContribution:
        result.threat_score > 0
          ? ((data?.confidence ?? 0) * result.threat_score) / Object.keys(breakdown).length
          : 0,
    }));

  return (
    <div className="space-y-8" role="region" aria-label="Analysis results">
      {/* Score Header */}
      <div className="bg-card border border-border p-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="font-mono text-[10px] text-primary uppercase tracking-widest mb-2" aria-hidden="true">
              Scan Complete
            </div>
            <h2 className="text-3xl font-extrabold tracking-tighter uppercase">
              Threat Assessment
            </h2>
          </div>
          <VerdictBadge verdict={result.verdict} />
        </div>

        <div className="flex flex-col md:flex-row items-center gap-8">
          <ThreatGauge score={result.threat_score} size={200} />
          <div className="flex-1 w-full">
            <div
              className="h-2 w-full bg-border rounded-full overflow-hidden mb-3"
              role="progressbar"
              aria-valuenow={Math.round(result.threat_score)}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`Threat score: ${result.threat_score.toFixed(1)} percent`}
            >
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{
                  width: `${result.threat_score}%`,
                  backgroundColor:
                    result.threat_score > 70
                      ? "var(--color-destructive)"
                      : result.threat_score > 40
                      ? "var(--color-amber)"
                      : "var(--color-primary)",
                }}
              />
            </div>
            <div className="flex justify-between text-xs text-muted-foreground">
              <span className="font-mono uppercase tracking-widest">0%</span>
              <span className="font-mono uppercase tracking-widest">Threat Score</span>
              <span className="font-mono uppercase tracking-widest">100%</span>
            </div>
            <div className="mt-4 flex items-center gap-4 font-mono text-[10px] text-muted-foreground uppercase tracking-widest">
              {result.trace_id && <span>Trace: {result.trace_id}</span>}
              {result.input_types && (
                <span>Modalities: {result.input_types.join(", ")}</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Plain English Summary */}
      <div className="border border-border p-6">
        <div className="font-mono text-[10px] text-primary uppercase tracking-widest mb-4">
          Plain English Summary
        </div>
        <div className="flex gap-4">
          <span className="text-3xl" role="img" aria-hidden="true">
            {summary.icon}
          </span>
          <div className="space-y-2">
            <h3 className="text-lg font-bold" style={{ color: `var(--color-${summary.color})` }}>
              {summary.title}
            </h3>
            <p className="text-sm text-foreground leading-relaxed">
              {summary.body}
            </p>
            <p className="text-xs text-muted-foreground leading-relaxed mt-2 italic">
              {summary.tip}
            </p>
          </div>
        </div>
      </div>

      {/* Modality Breakdown */}
      {modalities.length > 0 && (
        <section aria-labelledby="breakdown-heading">
          <div className="font-mono text-[10px] text-primary uppercase tracking-widest mb-4" id="breakdown-heading">
            Modality Breakdown
          </div>
          <div className="grid md:grid-cols-2 gap-px bg-border border border-border" role="list">
            {modalities.map((m) => (
              <ModalityCard key={m.type} {...m} />
            ))}
          </div>
        </section>
      )}

      {/* Screen reader announcement (accessibility skill) */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        Analysis complete. Verdict: {result.verdict}. Threat score: {result.threat_score.toFixed(1)} percent.
        {result.input_types && ` Analyzed modalities: ${result.input_types.join(", ")}.`}
      </div>
    </div>
  );
}
