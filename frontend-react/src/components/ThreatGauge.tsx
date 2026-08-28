interface ThreatGaugeProps {
  score: number;
  size?: number;
}

export default function ThreatGauge({ score, size = 280 }: ThreatGaugeProps) {
  const radius = 100;
  const cx = size / 2;
  const cy = size / 2 + 20;
  const startAngle = -210;
  const endAngle = 30;
  const totalAngle = endAngle - startAngle;
  const scoreAngle = startAngle + (score / 100) * totalAngle;

  // Arc path helper
  function arcPath(
    cx: number,
    cy: number,
    r: number,
    startDeg: number,
    endDeg: number
  ) {
    const rad = (deg: number) => (deg * Math.PI) / 180;
    const x1 = cx + r * Math.cos(rad(startDeg));
    const y1 = cy + r * Math.sin(rad(startDeg));
    const x2 = cx + r * Math.cos(rad(endDeg));
    const y2 = cy + r * Math.sin(rad(endDeg));
    const largeArc = endDeg - startDeg > 180 ? 1 : 0;
    return `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`;
  }

  // Color based on score
  const getColor = (s: number) => {
    if (s < 30) return "#22c55e";
    if (s < 70) return "#f59e0b";
    return "#ef4444";
  };

  // Needle endpoint
  const needleRad = (scoreAngle * Math.PI) / 180;
  const needleLen = 75;
  const nx = cx + needleLen * Math.cos(needleRad);
  const ny = cy + needleLen * Math.sin(needleRad);

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size * 0.75} viewBox={`0 0 ${size} ${size * 0.75}`}>
        {/* Background arcs */}
        <path
          d={arcPath(cx, cy, radius, startAngle, startAngle + totalAngle * 0.3)}
          fill="none"
          stroke="rgba(34, 197, 94, 0.2)"
          strokeWidth={12}
          strokeLinecap="round"
        />
        <path
          d={arcPath(
            cx,
            cy,
            radius,
            startAngle + totalAngle * 0.3,
            startAngle + totalAngle * 0.7
          )}
          fill="none"
          stroke="rgba(245, 158, 11, 0.2)"
          strokeWidth={12}
          strokeLinecap="round"
        />
        <path
          d={arcPath(
            cx,
            cy,
            radius,
            startAngle + totalAngle * 0.7,
            endAngle
          )}
          fill="none"
          stroke="rgba(239, 68, 68, 0.2)"
          strokeWidth={12}
          strokeLinecap="round"
        />

        {/* Score arc */}
        <path
          d={arcPath(cx, cy, radius, startAngle, scoreAngle)}
          fill="none"
          stroke={getColor(score)}
          strokeWidth={12}
          strokeLinecap="round"
          className="transition-all duration-700 ease-out"
        />

        {/* Needle */}
        <line
          x1={cx}
          y1={cy}
          x2={nx}
          y2={ny}
          stroke={getColor(score)}
          strokeWidth={3}
          strokeLinecap="round"
          className="transition-all duration-700 ease-out"
        />
        <circle cx={cx} cy={cy} r={6} fill={getColor(score)} />

        {/* Score text */}
        <text
          x={cx}
          y={cy + 40}
          textAnchor="middle"
          className="fill-text-primary font-mono text-3xl font-bold"
          style={{ fontVariantNumeric: "tabular-nums" }}
        >
          {score}
        </text>
        <text
          x={cx}
          y={cy + 56}
          textAnchor="middle"
          className="fill-text-tertiary text-xs"
        >
          /100
        </text>
      </svg>
    </div>
  );
}
