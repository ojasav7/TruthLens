export default function ScanVideo() {
  return (
    <div className="scan-card">
      <div className="scan-card__header">
        <span className="scan-card__icon">&#127916;</span>
        <span className="scan-card__label">VIDEO ANALYSIS</span>
        <span className="scan-card__status">SCANNING</span>
      </div>
      <div className="scan-card__body">
        <svg viewBox="0 0 400 200" className="scan-card__svg">
          {/* Timeline bar */}
          <rect x="20" y="160" width="360" height="4" fill="#1e293b" rx="2" />
          <rect x="20" y="160" width="0" height="4" fill="#22c55e" rx="2" className="scan-video-progress" />

          {/* Frame indicators */}
          {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
            <g key={i} className="scan-video-frame" style={{ animationDelay: `${i * 0.2}s` }}>
              <rect x={30 + i * 44} y="20" width="36" height="60" fill="#111" stroke="#334155" strokeWidth="1" rx="2" />
              <rect x={30 + i * 44} y="20" width="36" height="60" fill="url(#videoGrad)" opacity="0" className="scan-video-flash" style={{ animationDelay: `${i * 0.2 + 0.1}s` }} />
              <text x={48 + i * 44} y="55" textAnchor="middle" fill="#64748b" fontSize="8" fontFamily="monospace">F{i}</text>
            </g>
          ))}

          {/* Analysis lines */}
          {[0, 1, 2].map((i) => (
            <line key={i} x1="20" y1={100 + i * 20} x2="380" y2={100 + i * 20} stroke="#22c55e" strokeWidth="0.5" opacity="0.2" className="scan-video-line" style={{ animationDelay: `${i * 0.3}s` }} />
          ))}

          {/* Playhead */}
          <circle cx="20" cy="162" r="4" fill="#22c55e" className="scan-video-playhead" />

          {/* Data readout */}
          <text x="20" y="190" fill="#64748b" fontSize="8" fontFamily="monospace">TEMPORAL CONSISTENCY: 87.3%</text>
          <text x="280" y="190" fill="#22c55e" fontSize="8" fontFamily="monospace">DEEPFAKE: 0.12</text>

          <defs>
            <linearGradient id="videoGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#22c55e" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#22c55e" stopOpacity="0" />
            </linearGradient>
          </defs>
        </svg>
      </div>
    </div>
  );
}
