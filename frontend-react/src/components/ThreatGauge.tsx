interface ThreatGaugeProps {
  score: number;
  size?: number;
}

export default function ThreatGauge({ score, size = 200 }: ThreatGaugeProps) {
  const clamped = Math.max(0, Math.min(100, score));
  const angle = (clamped / 100) * 180;
  const r = size / 2 - 12;
  const cx = size / 2;
  const cy = size / 2 + 8;

  const startAngle = -180;
  const endAngle = startAngle + angle;
  const rad = (deg: number) => (deg * Math.PI) / 180;

  const arcPath = (
    sa: number,
    ea: number,
    radius: number
  ) => {
    const sx = cx + radius * Math.cos(rad(sa));
    const sy = cy + radius * Math.sin(rad(sa));
    const ex = cx + radius * Math.cos(rad(ea));
    const ey = cy + radius * Math.sin(rad(ea));
    const largeArc = Math.abs(ea - sa) > 180 ? 1 : 0;
    return `M ${sx} ${sy} A ${radius} ${radius} 0 ${largeArc} 1 ${ex} ${ey}`;
  };

  const needleEndX = cx + (r - 8) * Math.cos(rad(endAngle));
  const needleEndY = cy + (r - 8) * Math.sin(rad(endAngle));

  const getColor = (s: number) =>
    s > 70 ? "var(--color-destructive)" : s > 40 ? "var(--color-amber)" : "var(--color-primary)";

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size * 0.6} viewBox={`0 0 ${size} ${size * 0.6}`}>
        {/* Track */}
        <path
          d={arcPath(startAngle, 0, r)}
          fill="none"
          stroke="var(--color-border)"
          strokeWidth="8"
          strokeLinecap="butt"
        />
        {/* Active arc */}
        <path
          d={arcPath(startAngle, endAngle, r)}
          fill="none"
          stroke={getColor(clamped)}
          strokeWidth="8"
          strokeLinecap="butt"
        />
        {/* Needle */}
        <line
          x1={cx}
          y1={cy}
          x2={needleEndX}
          y2={needleEndY}
          stroke="var(--color-foreground)"
          strokeWidth="2"
          strokeLinecap="round"
        />
        <circle cx={cx} cy={cy} r="4" fill="var(--color-foreground)" />
        {/* Score text */}
        <text
          x={cx}
          y={cy + 28}
          textAnchor="middle"
          className="font-mono"
          fill="var(--color-foreground)"
          fontSize="11"
          fontFamily="var(--font-mono)"
          fontWeight="bold"
        >
          {clamped.toFixed(1)}%
        </text>
      </svg>
    </div>
  );
}
