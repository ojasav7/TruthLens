import type { CaseItem } from "../../data/casesData";
import { STATUS_COLORS, STATUS_LABELS, PRIORITY_COLORS, MODALITY_ICONS } from "../../data/casesData";

interface CaseCardProps {
  caseItem: CaseItem;
}

function getThreatColor(score: number): string {
  if (score >= 70) return "text-destructive";
  if (score >= 40) return "text-amber";
  return "text-primary";
}

export default function CaseCard({ caseItem }: Readonly<CaseCardProps>) {
  return (
    <article
      className={`bg-card border border-border border-l-4 ${PRIORITY_COLORS[caseItem.priority]} p-6 hover:border-primary/30 transition-colors cursor-pointer`}
      role="listitem"
    >
      {/* Header: ID + Status */}
      <div className="flex items-center justify-between mb-3">
        <span className="font-mono text-[10px] text-muted-foreground uppercase tracking-widest">
          {caseItem.id}
        </span>
        <span className="flex items-center gap-1.5 px-2 py-0.5 text-[10px] font-mono uppercase tracking-widest">
          <span className={`w-1.5 h-1.5 rounded-full ${STATUS_COLORS[caseItem.status]}`} />
          <span className={caseItem.status === "open" ? "text-primary" : caseItem.status === "in_review" ? "text-amber" : "text-muted-foreground"}>
            {STATUS_LABELS[caseItem.status]}
          </span>
        </span>
      </div>

      {/* Title */}
      <h3 className="text-lg font-bold mb-2">{caseItem.title}</h3>

      {/* Summary */}
      <p className="text-sm text-muted-foreground leading-relaxed mb-4 line-clamp-2">
        {caseItem.summary}
      </p>

      {/* Metadata Row */}
      <div className="flex items-center justify-between text-[10px] text-muted-foreground font-mono uppercase tracking-widest">
        <div className="flex items-center gap-3">
          {/* Modalities */}
          <div className="flex items-center gap-1">
            {caseItem.modalities.map((m) => (
              <span key={m} className="px-1.5 py-0.5 bg-secondary border border-border">
                {MODALITY_ICONS[m] || m}
              </span>
            ))}
          </div>

          {/* Evidence count */}
          <span>{caseItem.evidenceCount} evidence</span>
        </div>

        {/* Threat score */}
        <span className={`font-bold ${getThreatColor(caseItem.threatScore)}`}>
          {caseItem.threatScore}%
        </span>
      </div>

      {/* Footer: Timestamps + Analyst */}
      <div className="flex items-center justify-between mt-4 pt-4 border-t border-border text-[10px] text-muted-foreground font-mono uppercase tracking-widest">
        <span>Updated {caseItem.updated}</span>
        <div className="flex items-center gap-2">
          <span className="w-5 h-5 bg-primary rounded-full flex items-center justify-center text-primary-foreground text-[8px] font-bold">
            {caseItem.analyst}
          </span>
        </div>
      </div>
    </article>
  );
}
