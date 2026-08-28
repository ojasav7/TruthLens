import { Type, Image as ImageIcon, Film, Mic } from "lucide-react";

interface ModalityCardProps {
  type: string;
  label: string;
  confidence: number;
  threatContribution: number;
}

const iconMap: Record<string, typeof Type> = {
  text: Type,
  image: ImageIcon,
  video: Film,
  audio: Mic,
};

const numMap: Record<string, string> = {
  text: "01",
  image: "02",
  video: "03",
  audio: "04",
};

export default function ModalityCard({
  type,
  label,
  confidence,
  threatContribution,
}: ModalityCardProps) {
  const Icon = iconMap[type] || Type;
  const num = numMap[type] || "00";
  const safeConf = Number.isFinite(confidence) ? confidence : 0;
  const safeThreat = Number.isFinite(threatContribution) ? threatContribution : 0;

  return (
    <div className="bg-background p-6 border border-border hover:border-primary/30 transition-colors" role="listitem">
      <div className="flex items-center gap-3 mb-4">
        <Icon className="size-4 text-primary" aria-hidden="true" />
        <span className="font-mono text-[10px] text-primary uppercase tracking-widest">
          {num} / {label}
        </span>
      </div>

      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-muted-foreground">Confidence</span>
        <span
          className="font-mono text-sm font-bold text-foreground"
          style={{ fontVariantNumeric: "tabular-nums" }}
        >
          {(safeConf * 100).toFixed(1)}%
        </span>
      </div>
      <div
        className="h-1.5 w-full bg-border rounded-full overflow-hidden mb-4"
        role="progressbar"
        aria-valuenow={Math.round(safeConf * 100)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${label} confidence: ${(safeConf * 100).toFixed(1)}%`}
      >
        <div
          className="h-full bg-primary rounded-full transition-all duration-500"
          style={{ width: `${safeConf * 100}%` }}
        />
      </div>

      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">Threat Contribution</span>
        <span
          className="font-mono text-sm font-bold text-foreground"
          style={{ fontVariantNumeric: "tabular-nums" }}
        >
          {safeThreat.toFixed(1)}%
        </span>
      </div>
      <div
        className="h-1.5 w-full bg-border rounded-full overflow-hidden"
        role="progressbar"
        aria-valuenow={Math.round(safeThreat)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${label} threat contribution: ${safeThreat.toFixed(1)}%`}
      >
        <div
          className="h-full bg-destructive rounded-full transition-all duration-500"
          style={{ width: `${safeThreat}%` }}
        />
      </div>
    </div>
  );
}
