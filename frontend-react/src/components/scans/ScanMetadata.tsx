export default function ScanMetadata() {
  const tags = [
    { line: "12", text: "Camera: Canon EOS R5", flagged: false },
    { line: "42", text: "GPS: 40.7128° N, 74.0060° W", flagged: false },
    { line: "45", text: "Modified: Adobe Photoshop 25.4", flagged: true },
    { line: "67", text: "Tamper: 3 anomalies detected", flagged: true },
    { line: "73", text: "Exposure: 1/250s f/2.8 ISO 400", flagged: false },
  ];

  return (
    <div className="scan-card">
      <div className="scan-card__header">
        <span className="scan-card__icon">&#128269;</span>
        <span className="scan-card__label">METADATA</span>
        <span className="scan-card__status">ANALYZING</span>
      </div>
      <div className="scan-card__body">
        <svg viewBox="0 0 400 200" className="scan-card__svg">
          {/* Face scan circle */}
          <circle cx="100" cy="90" r="50" fill="none" stroke="#06b6d4" strokeWidth="1" opacity="0.3" className="scan-meta-circle" />
          <circle cx="100" cy="90" r="35" fill="none" stroke="#06b6d4" strokeWidth="0.5" opacity="0.2" />
          <circle cx="100" cy="90" r="4" fill="#06b6d4" className="scan-meta-dot" />

          {/* Crosshair */}
          <line x1="100" y1="30" x2="100" y2="50" stroke="#06b6d4" strokeWidth="0.5" opacity="0.5" />
          <line x1="100" y1="130" x2="100" y2="150" stroke="#06b6d4" strokeWidth="0.5" opacity="0.5" />
          <line x1="40" y1="90" x2="60" y2="90" stroke="#06b6d4" strokeWidth="0.5" opacity="0.5" />
          <line x1="140" y1="90" x2="160" y2="90" stroke="#06b6d4" strokeWidth="0.5" opacity="0.5" />

          {/* Scan line */}
          <line x1="50" y1="0" x2="150" y2="0" stroke="#06b6d4" strokeWidth="1" opacity="0.4" className="scan-meta-scanline" />

          {/* EXIF tags */}
          <text x="180" y="25" fill="#64748b" fontSize="8" fontFamily="monospace">EXIF TAGS</text>
          {tags.map((tag, i) => (
            <g key={i} className="scan-meta-tag" style={{ animationDelay: `${i * 0.12}s` }}>
              <text x="180" y={42 + i * 20} fill="#64748b" fontSize="7" fontFamily="monospace">{tag.line}</text>
              <text x="200" y={42 + i * 20} fill={tag.flagged ? "#ef4444" : "#94a3b8"} fontSize="8" fontFamily="monospace" fontWeight={tag.flagged ? "600" : "400"}>{tag.text}</text>
              {tag.flagged && <circle cx="370" cy={38 + i * 20} r="3" fill="#ef4444" className="scan-meta-flag" />}
            </g>
          ))}

          {/* Stats */}
          <text x="20" y="175" fill="#64748b" fontSize="8" fontFamily="monospace">EXIF ENTRIES: 847</text>
          <text x="20" y="190" fill="#06b6d4" fontSize="8" fontFamily="monospace">TAMPER SCORE: 0.34</text>
          <text x="200" y="175" fill="#64748b" fontSize="8" fontFamily="monospace">MODIFIED: YES</text>
          <text x="200" y="190" fill="#ef4444" fontSize="8" fontFamily="monospace">3 ANOMALIES</text>
        </svg>
      </div>
    </div>
  );
}
