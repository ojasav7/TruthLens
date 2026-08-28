interface ModalityCardProps {
  modality: string;
  label: string;
  confidence: number;
  threat: number;
}

const icons: Record<string, string> = {
  TEXT: "📝",
  IMAGE: "🖼️",
  VIDEO: "🎬",
  AUDIO: "🔊",
};

export default function ModalityCard({
  modality,
  label,
  confidence,
  threat,
}: ModalityCardProps) {
  const confPct = (confidence || 0) * 100;
  const threatPct = (threat || 0) * 100;
  const isFake = label === "fake" || label === "cloned";
  const color = isFake ? "var(--color-crimson)" : "var(--color-emerald)";
  const chipClass = isFake
    ? "bg-crimson/12 text-crimson border-crimson/30"
    : "bg-emerald/12 text-emerald border-emerald/30";

  return (
    <div className="flex items-center gap-4 p-4 bg-bg-surface border border-border-default rounded-xl transition-all hover:border-border-active hover:shadow-md animate-fade-in-up">
      <span className="text-2xl shrink-0">{icons[modality] || "📄"}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1.5">
          <span className="font-semibold text-text-primary">{modality}</span>
          <span
            className={`px-2.5 py-0.5 text-xs font-semibold uppercase rounded-full border ${chipClass}`}
          >
            {label}
          </span>
        </div>
        <div className="w-full h-1.5 bg-bg-primary rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700 ease-out"
            style={{ width: `${confPct}%`, background: color }}
          />
        </div>
        <div className="flex justify-between mt-1">
          <span
            className="text-xs text-text-tertiary"
            style={{ fontVariantNumeric: "tabular-nums" }}
          >
            Confidence: {confPct.toFixed(0)}%
          </span>
          <span
            className="text-xs text-text-tertiary"
            style={{ fontVariantNumeric: "tabular-nums" }}
          >
            Threat: {threatPct.toFixed(0)}%
          </span>
        </div>
      </div>
    </div>
  );
}
