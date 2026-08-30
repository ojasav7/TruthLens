export default function ScanAudio() {
  return (
    <div className="scan-card">
      <div className="scan-card__header">
        <span className="scan-card__icon">&#128266;</span>
        <span className="scan-card__label">AUDIO ANALYSIS</span>
        <span className="scan-card__status">SCANNING</span>
      </div>
      <div className="scan-card__body">
        <svg viewBox="0 0 400 200" className="scan-card__svg">
          {/* Waveform */}
          {Array.from({ length: 60 }, (_, i) => {
            const h = Math.abs(Math.sin(i * 0.3)) * 30 + Math.abs(Math.sin(i * 0.7)) * 20 + 10;
            return (
              <rect
                key={i}
                x={20 + i * 6}
                y={90 - h / 2}
                width="4"
                height={h}
                fill="#22c55e"
                opacity={0.3 + Math.abs(Math.sin(i * 0.2)) * 0.3}
                className="scan-audio-bar"
                style={{ animationDelay: `${i * 0.03}s` }}
                rx="1"
              />
            );
          })}

          {/* Ghost overlay waveform */}
          {Array.from({ length: 60 }, (_, i) => {
            const h = Math.abs(Math.sin(i * 0.3 + 0.5)) * 25 + Math.abs(Math.sin(i * 0.5)) * 15 + 8;
            return (
              <rect
                key={i}
                x={20 + i * 6}
                y={90 - h / 2}
                width="4"
                height={h}
                fill="#06b6d4"
                opacity={0.15}
                className="scan-audio-ghost"
                style={{ animationDelay: `${i * 0.03 + 0.1}s` }}
                rx="1"
              />
            );
          })}

          {/* Center line */}
          <line x1="20" y1="90" x2="380" y2="90" stroke="#334155" strokeWidth="0.5" />

          {/* Playhead */}
          <line x1="20" y1="40" x2="20" y2="140" stroke="#22c55e" strokeWidth="1" opacity="0.6" className="scan-audio-playhead" />

          {/* MFCC labels */}
          <text x="20" y="160" fill="#64748b" fontSize="8" fontFamily="monospace">VOICE CLONE SCORE</text>
          <text x="20" y="175" fill="#22c55e" fontSize="10" fontFamily="monospace" fontWeight="700">0.12 (REAL)</text>

          <text x="220" y="160" fill="#64748b" fontSize="8" fontFamily="monospace">FREQUENCY ANOMALY</text>
          <text x="220" y="175" fill="#22c55e" fontSize="10" fontFamily="monospace" fontWeight="700">NONE DETECTED</text>

          {/* Timeline */}
          <text x="20" y="195" fill="#64748b" fontSize="7" fontFamily="monospace">0:00</text>
          <text x="180" y="195" fill="#64748b" fontSize="7" fontFamily="monospace">1:30</text>
          <text x="360" y="195" fill="#64748b" fontSize="7" fontFamily="monospace">3:00</text>
        </svg>
      </div>
    </div>
  );
}
