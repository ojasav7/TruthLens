export default function ScanText() {
  const words = ["NASA", "confirms", "earth", "will", "be", "destroyed", "by", "asteroid", "in", "2026"];
  const flagged = [0, 6, 9]; // Indices of suspicious words

  return (
    <div className="scan-card">
      <div className="scan-card__header">
        <span className="scan-card__icon">T</span>
        <span className="scan-card__label">TEXT ANALYSIS</span>
        <span className="scan-card__status">SCANNING</span>
      </div>
      <div className="scan-card__body">
        <svg viewBox="0 0 400 200" className="scan-card__svg">
          {/* Text lines */}
          <text x="20" y="30" fill="#94a3b8" fontSize="11" fontFamily="Inter, sans-serif">
            {words.map((word, i) => (
              <tspan key={i} className="scan-text-word" style={{ animationDelay: `${i * 0.15}s` }}>
                <tspan fill={flagged.includes(i) ? "#ef4444" : "#f1f5f9"} fontWeight={flagged.includes(i) ? "700" : "400"}>{word}</tspan>
                {" "}
              </tspan>
            ))}
          </text>

          {/* NLP confidence bars */}
          <text x="20" y="60" fill="#64748b" fontSize="8" fontFamily="monospace">NLP CONFIDENCE</text>
          {[
            { label: "Fake News", pct: 87, color: "#ef4444" },
            { label: "Bias", pct: 62, color: "#f59e0b" },
            { label: "Sensational", pct: 94, color: "#ef4444" },
          ].map((bar, i) => (
            <g key={i} className="scan-text-bar" style={{ animationDelay: `${i * 0.2}s` }}>
              <text x="20" y={80 + i * 18} fill="#94a3b8" fontSize="8" fontFamily="monospace">{bar.label}</text>
              <rect x="100" y={74 + i * 18} width="180" height="6" fill="#1e293b" rx="3" />
              <rect x="100" y={74 + i * 18} width="0" height="6" fill={bar.color} rx="3" className="scan-text-bar-fill" style={{ animationDelay: `${i * 0.2 + 0.3}s` }} />
              <text x="290" y={80 + i * 18} fill={bar.color} fontSize="8" fontFamily="monospace">{bar.pct}%</text>
            </g>
          ))}

          {/* Highlighted suspicious words */}
          <text x="20" y="150" fill="#64748b" fontSize="8" fontFamily="monospace">FLAGGED TOKENS</text>
          {flagged.map((i, idx) => (
            <g key={idx} className="scan-text-flag" style={{ animationDelay: `${idx * 0.15}s` }}>
              <rect x={20 + idx * 80} y="158" width="70" height="20" fill="rgba(239, 68, 68, 0.1)" stroke="#ef4444" strokeWidth="1" rx="2" />
              <text x={55 + idx * 80} y="172" textAnchor="middle" fill="#ef4444" fontSize="9" fontFamily="monospace" fontWeight="600">{words[i]}</text>
            </g>
          ))}

          {/* Scan line */}
          <line x1="20" y1="0" x2="380" y2="0" stroke="#22c55e" strokeWidth="1" opacity="0.4" className="scan-text-scanline" />
        </svg>
      </div>
    </div>
  );
}
