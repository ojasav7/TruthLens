interface VerdictBadgeProps {
  verdict: string;
}

export default function VerdictBadge({ verdict }: VerdictBadgeProps) {
  const v = verdict.toLowerCase();
  let bg = "var(--color-primary)";
  let text = "var(--color-primary-foreground)";
  let label = verdict;

  if (v.includes("high") || v.includes("fake")) {
    bg = "var(--color-destructive)";
    text = "var(--color-destructive-foreground)";
    label = "HIGH RISK";
  } else if (v.includes("medium") || v.includes("review")) {
    bg = "var(--color-amber)";
    text = "var(--color-background)";
    label = "REVIEW NEEDED";
  } else if (v.includes("low") || v.includes("real") || v.includes("clean")) {
    bg = "var(--color-emerald)";
    text = "var(--color-background)";
    label = "LOW RISK";
  }

  return (
    <span
      className="inline-flex items-center px-4 py-1.5 font-mono text-[10px] font-bold uppercase tracking-widest"
      style={{ backgroundColor: bg, color: text }}
    >
      {label}
    </span>
  );
}
