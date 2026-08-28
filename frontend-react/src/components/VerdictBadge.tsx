import { getVerdictColor, getVerdictIcon } from "../lib/utils";

interface VerdictBadgeProps {
  verdict: string;
  score: number;
}

export default function VerdictBadge({ verdict, score }: VerdictBadgeProps) {
  const color = getVerdictColor(verdict);
  const icon = getVerdictIcon(verdict);

  const colorClasses: Record<string, string> = {
    emerald:
      "bg-emerald/12 text-emerald border-emerald shadow-[0_0_16px_rgba(34,197,94,0.15)]",
    amber:
      "bg-amber/12 text-amber border-amber shadow-[0_0_16px_rgba(245,158,11,0.15)]",
    crimson:
      "bg-crimson/12 text-crimson border-crimson shadow-[0_0_20px_rgba(239,68,68,0.3)] animate-pulse-glow",
  };

  return (
    <div className="flex flex-col items-center gap-4 animate-fade-in-up">
      <div
        className={`inline-flex items-center gap-2 px-7 py-2.5 rounded-full text-xl font-bold uppercase tracking-wider border-2 ${colorClasses[color]}`}
      >
        {icon} {verdict}
      </div>
      <div className="text-center">
        <div
          className="text-3xl font-bold font-mono text-text-primary"
          style={{ fontVariantNumeric: "tabular-nums" }}
        >
          {score}
          <span className="text-lg text-text-tertiary">/100</span>
        </div>
      </div>
    </div>
  );
}
