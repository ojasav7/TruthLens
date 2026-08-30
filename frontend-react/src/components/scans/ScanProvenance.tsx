export default function ScanProvenance() {
  const nodes = [
    { label: "Creator", x: 50, y: 60 },
    { label: "Tool", x: 130, y: 60 },
    { label: "Platform", x: 210, y: 60 },
    { label: "Viewer", x: 290, y: 60 },
  ];

  return (
    <div className="scan-card">
      <div className="scan-card__header">
        <span className="scan-card__icon">&#128274;</span>
        <span className="scan-card__label">PROVENANCE</span>
        <span className="scan-card__status">VERIFIED</span>
      </div>
      <div className="scan-card__body">
        <svg viewBox="0 0 400 200" className="scan-card__svg">
          {/* Chain of trust flow */}
          {nodes.map((node, i) => (
            <g key={i} className="scan-prov-node" style={{ animationDelay: `${i * 0.2}s` }}>
              {/* Connection line */}
              {i < nodes.length - 1 && (
                <line x1={node.x + 30} y1={node.y} x2={nodes[i + 1].x - 10} y2={node.y} stroke="#22c55e" strokeWidth="2" strokeDasharray="4 2" className="scan-prov-line" style={{ animationDelay: `${i * 0.2 + 0.1}s` }} />
              )}
              {/* Node circle */}
              <circle cx={node.x + 10} cy={node.y} r="16" fill="rgba(34, 197, 94, 0.1)" stroke="#22c55e" strokeWidth="1.5" />
              <text x={node.x + 10} y={node.y + 4} textAnchor="middle" fill="#22c55e" fontSize="8" fontFamily="monospace" fontWeight="600">{i + 1}</text>
              <text x={node.x + 10} y={node.y + 32} textAnchor="middle" fill="#94a3b8" fontSize="8" fontFamily="monospace">{node.label}</text>
            </g>
          ))}

          {/* Certificate box */}
          <rect x="20" y="100" width="360" height="40" fill="rgba(34, 197, 94, 0.05)" stroke="#22c55e" strokeWidth="1" rx="2" className="scan-prov-cert" />
          <text x="30" y="118" fill="#22c55e" fontSize="9" fontFamily="monospace" fontWeight="700">&#10003; SIGNED</text>
          <text x="30" y="132" fill="#94a3b8" fontSize="8" fontFamily="monospace">Certificate: Valid | Expires: 2027-01-15</text>

          {/* Hash display */}
          <text x="20" y="165" fill="#64748b" fontSize="8" fontFamily="monospace">CONTENT HASH</text>
          <text x="20" y="180" fill="#22c55e" fontSize="8" fontFamily="monospace">a3f8c2e1...b7d4</text>
          <text x="200" y="165" fill="#64748b" fontSize="8" fontFamily="monospace">SIGNATURE</text>
          <text x="200" y="180" fill="#22c55e" fontSize="8" fontFamily="monospace">SHA-256: 9e4d1...</text>

          {/* Animated verification pulse */}
          <circle cx="370" cy="20" r="8" fill="none" stroke="#22c55e" strokeWidth="1" className="scan-prov-pulse" />
          <circle cx="370" cy="20" r="3" fill="#22c55e" />
        </svg>
      </div>
    </div>
  );
}
