export default function ScanHeatmap() {
  return (
    <div className="scan-card">
      <div className="scan-card__header">
        <span className="scan-card__icon">&#128065;</span>
        <span className="scan-card__label">HEATMAP</span>
        <span className="scan-card__status">DEEPFAKE</span>
      </div>
      <div className="scan-card__body">
        <svg viewBox="0 0 400 200" className="scan-card__svg">
          {/* Face outline */}
          <ellipse cx="200" cy="90" rx="60" ry="75" fill="none" stroke="#334155" strokeWidth="1" />

          {/* Heatmap glow */}
          <ellipse cx="200" cy="90" rx="55" ry="70" fill="url(#heatmapGrad)" className="scan-heat-glow" />

          {/* Eye markers */}
          <circle cx="180" cy="75" r="8" fill="none" stroke="#06b6d4" strokeWidth="1.5" className="scan-heat-eye" style={{ animationDelay: "0.2s" }} />
          <circle cx="180" cy="75" r="2" fill="#06b6d4" />
          <circle cx="220" cy="75" r="8" fill="none" stroke="#06b6d4" strokeWidth="1.5" className="scan-heat-eye" style={{ animationDelay: "0.4s" }} />
          <circle cx="220" cy="75" r="2" fill="#06b6d4" />

          {/* Nose/mouth indicators */}
          <line x1="200" y1="85" x2="200" y2="105" stroke="#06b6d4" strokeWidth="0.5" opacity="0.4" />
          <ellipse cx="200" cy="115" rx="15" ry="5" fill="none" stroke="#06b6d4" strokeWidth="0.5" opacity="0.3" />

          {/* Scan lines */}
          {[0, 1, 2, 3, 4].map((i) => (
            <line key={i} x1="140" y1={30 + i * 30} x2="260" y2={30 + i * 30} stroke="#06b6d4" strokeWidth="0.3" opacity="0.2" className="scan-heat-line" style={{ animationDelay: `${i * 0.15}s` }} />
          ))}

          {/* Confidence badge */}
          <rect x="20" y="160" width="80" height="24" fill="rgba(239, 68, 68, 0.15)" stroke="#ef4444" strokeWidth="1" rx="3" className="scan-heat-badge" />
          <text x="60" y="176" textAnchor="middle" fill="#ef4444" fontSize="10" fontFamily="monospace" fontWeight="700">88.5%</text>

          {/* Labels */}
          <text x="110" y="175" fill="#64748b" fontSize="8" fontFamily="monospace">GAN ARTIFACTS</text>
          <text x="110" y="190" fill="#ef4444" fontSize="8" fontFamily="monospace">FACE SWAP DETECTED</text>

          <text x="280" y="175" fill="#64748b" fontSize="8" fontFamily="monospace">SCORE</text>
          <text x="280" y="190" fill="#ef4444" fontSize="8" fontFamily="monospace">HIGH RISK</text>

          {/* Scanning animation */}
          <line x1="140" y1="0" x2="260" y2="0" stroke="#06b6d4" strokeWidth="1.5" opacity="0.5" className="scan-heat-scanline" />

          <defs>
            <radialGradient id="heatmapGrad" cx="50%" cy="50%">
              <stop offset="0%" stopColor="#ef4444" stopOpacity="0.5" />
              <stop offset="40%" stopColor="#f59e0b" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#000" stopOpacity="0" />
            </radialGradient>
          </defs>
        </svg>
      </div>
    </div>
  );
}
