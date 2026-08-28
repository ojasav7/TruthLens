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

export default function ResultsPanel({ result }: ResultsPanelProps) {
  const breakdown = result.breakdown || {};
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
    <div className="space-y-8">
      {/* Score Header — matches landing page floating badge style */}
      <div className="bg-card border border-border p-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="font-mono text-[10px] text-primary uppercase tracking-widest mb-2">
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
            <div className="h-2 w-full bg-border rounded-full overflow-hidden mb-3">
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

      {/* Modality Breakdown */}
      {modalities.length > 0 && (
        <div>
          <div className="font-mono text-[10px] text-primary uppercase tracking-widest mb-4">
            Modality Breakdown
          </div>
          <div className="grid md:grid-cols-2 gap-px bg-border border border-border">
            {modalities.map((m) => (
              <ModalityCard key={m.type} {...m} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
