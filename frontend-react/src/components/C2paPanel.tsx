import { useEffect, useRef, useState } from "react";
import "./C2paPanel.css";

interface C2paProps {
  confidence: number;
  label: string;
  signals?: Record<string, any>;
}

export default function C2paPanel({ label }: C2paProps) {
  const [mounted, setMounted] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);

  useEffect(() => { setMounted(true); }, []);

  // Animated chain-of-trust flow diagram
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const W = (canvas.width = 500);
    const H = (canvas.height = 280);
    const isVerified = label === "real";
    let t = 0;

    const draw = () => {
      ctx.clearRect(0, 0, W, H);

      // Grid background
      ctx.strokeStyle = "rgba(34, 197, 94, 0.05)";
      ctx.lineWidth = 1;
      for (let x = 0; x < W; x += 30) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
      }
      for (let y = 0; y < H; y += 30) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
      }

      // Nodes
      const nodes = [
        { x: 80, y: 50, label: "Author", icon: "user" },
        { x: 250, y: 50, label: "Device", icon: "device" },
        { x: 420, y: 50, label: "Process", icon: "process" },
        { x: 80, y: 150, label: "Manifest", icon: "manifest" },
        { x: 250, y: 150, label: "Verify", icon: "verify" },
        { x: 420, y: 150, label: "Certify", icon: "certify" },
        { x: 250, y: 230, label: "Trust", icon: "trust" },
      ];

      // Edges
      const edges = [
        [0, 1], [1, 2], [0, 3], [1, 4], [2, 5],
        [3, 4], [4, 5], [3, 6], [4, 6], [5, 6],
      ];

      // Draw edges with pulse
      edges.forEach(([from, to]) => {
        const a = nodes[from];
        const b = nodes[to];
        const pulse = Math.sin(t * 3 + from + to) * 0.3 + 0.5;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.strokeStyle = isVerified
          ? `rgba(34, 197, 94, ${pulse * 0.6})`
          : `rgba(239, 68, 68, ${pulse * 0.4})`;
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Arrow dot traveling along edge
        const progress = (Math.sin(t * 2 + from) + 1) / 2;
        const dx = a.x + (b.x - a.x) * progress;
        const dy = a.y + (b.y - a.y) * progress;
        ctx.beginPath();
        ctx.arc(dx, dy, 2, 0, Math.PI * 2);
        ctx.fillStyle = isVerified ? "rgba(34, 197, 94, 0.8)" : "rgba(239, 68, 68, 0.6)";
        ctx.fill();
      });

      // Draw nodes
      nodes.forEach((n, i) => {
        // Glow
        ctx.beginPath();
        ctx.arc(n.x, n.y, 20 + Math.sin(t * 2 + i) * 3, 0, Math.PI * 2);
        ctx.fillStyle = isVerified
          ? `rgba(34, 197, 94, ${0.05 + Math.sin(t + i) * 0.03})`
          : `rgba(239, 68, 68, ${0.05 + Math.sin(t + i) * 0.03})`;
        ctx.fill();

        // Hexagon
        ctx.beginPath();
        for (let j = 0; j < 6; j++) {
          const angle = (Math.PI / 3) * j - Math.PI / 6;
          const x = n.x + 14 * Math.cos(angle);
          const y = n.y + 14 * Math.sin(angle);
          j === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.strokeStyle = isVerified
          ? `rgba(34, 197, 94, ${0.6 + Math.sin(t * 2 + i) * 0.2})`
          : `rgba(239, 68, 68, ${0.5 + Math.sin(t * 2 + i) * 0.2})`;
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Center dot
        ctx.beginPath();
        ctx.arc(n.x, n.y, 4, 0, Math.PI * 2);
        ctx.fillStyle = isVerified ? "rgba(34, 197, 94, 0.8)" : "rgba(239, 68, 68, 0.6)";
        ctx.fill();

        // Label
        ctx.font = "600 8px 'JetBrains Mono', monospace";
        ctx.fillStyle = "#9ca3af";
        ctx.textAlign = "center";
        ctx.fillText(n.label.toUpperCase(), n.x, n.y + 28);
      });

      t += 0.012;
      animRef.current = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(animRef.current);
  }, [label]);

  const isVerified = label === "real";

  const signedEntries = [
    { key: "Signed By", value: "TruthLens v4.0 (Adobe C2PA Toolkit)" },
    { key: "Assertion Service", value: "c2pa.truthlens.io" },
    { key: "Content Hash", value: "sha256-0a3f7c2e8b1d..." },
    { key: "Certificate", value: "Valid (expires 2027-03-15)" },
    { key: "Signature Algorithm", value: "ES256 (P-256 + SHA-256)" },
    { key: "Trust Anchor", value: "C2PA Root CA (Adobe)" },
    { key: "Timestamp", value: "2026-08-30T09:23:17Z" },
    { key: "Manifest Store", value: "1 active claim" },
  ];

  const categories = [
    { label: "Valid Claims", count: 1 },
    { label: "Core Certificate", count: 1 },
    { label: "Manifest Assertions", count: 3 },
    { label: "Hash Mappings", count: 4 },
    { label: "User Assertions", count: 1 },
  ];

  const bottomMetrics = [
    { label: "Provenance", value: "Verified" },
    { label: "Integrity", value: "Passed" },
    { label: "Revocation", value: "Clear" },
    { label: "Timestamp", value: "Valid" },
    { label: "Chain", value: "Complete" },
  ];

  return (
    <div className={`c2pa-panel ${mounted ? "c2pa-panel--mounted" : ""}`}>
      {/* Header */}
      <div className="c2pa-panel__header">
        <div className="c2pa-panel__title">
          <span className="c2pa-panel__menu">☰</span>
          C2PA — Content Provenance
        </div>
        <div className="c2pa-panel__header-right">
          <span className="c2pa-panel__status">{isVerified ? "Signed" : "Unsigned"}</span>
          <span className="c2pa-panel__badge">{isVerified ? "CERTIFIED" : "FAILED"}</span>
        </div>
      </div>

      <div className="c2pa-panel__body">
        {/* Left - Signed certificate */}
        <div className="c2pa-panel__cert">
          <div className="c2pa-panel__cert-header">
            <span className="c2pa-panel__cert-icon">✓</span>
            Signed
          </div>
          <div className="c2pa-panel__cert-entries">
            {signedEntries.map((entry, i) => (
              <div
                key={i}
                className="c2pa-panel__cert-entry"
                style={{ animationDelay: `${i * 0.08}s` }}
              >
                <span className="c2pa-panel__cert-key">{entry.key}:</span>
                <span className="c2pa-panel__cert-value">{entry.value}</span>
              </div>
            ))}
          </div>
          <div className="c2pa-panel__categories">
            <div className="c2pa-panel__categories-title">Validation Summary:</div>
            {categories.map((cat) => (
              <div key={cat.label} className="c2pa-panel__category">
                {cat.label}: <span className="c2pa-panel__category-count">{cat.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Center - Chain of trust flow */}
        <div className="c2pa-panel__flow">
          <div className="c2pa-panel__flow-header">
            <span className="c2pa-panel__flow-label">Chain of Trust</span>
            <span className="c2pa-panel__flow-filter">Signatures ▾</span>
          </div>
          <canvas ref={canvasRef} className="c2pa-panel__canvas" />
        </div>
      </div>

      {/* Bottom metrics */}
      <div className="c2pa-panel__bottom">
        <div className="c2pa-panel__bottom-left">
          <div className="c2pa-panel__bottom-title">Verification Checks</div>
          <div className="c2pa-panel__bottom-items">
            {bottomMetrics.map((m) => (
              <div key={m.label} className="c2pa-panel__bottom-item">
                {m.label}: <span className="c2pa-panel__bottom-value">{m.value}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="c2pa-panel__bottom-center">
          <div className="c2pa-panel__donut">
            <svg viewBox="0 0 60 60">
              <circle cx="30" cy="30" r="24" fill="none" stroke="var(--color-border)" strokeWidth="5" />
              <circle
                cx="30" cy="30" r="24"
                fill="none"
                stroke={isVerified ? "var(--color-primary)" : "var(--color-destructive)"}
                strokeWidth="5"
                strokeDasharray={`${(isVerified ? 0.85 : 0.25) * 150.8} 150.8`}
                strokeLinecap="round"
                transform="rotate(-90 30 30)"
                className="c2pa-ring-animated"
              />
            </svg>
            <div className="c2pa-panel__donut-label">
              STATUS<br />{isVerified ? "VERIFIED" : "FAILED"}
            </div>
          </div>
        </div>
        <div className="c2pa-panel__bottom-right">
          <div className="c2pa-panel__hashes">
            <div className="c2pa-panel__hash-col">
              <div className="c2pa-panel__hash-title">Assertion URIs</div>
              <div className="c2pa-panel__hash-val">c2pa://claim/0x3a7f</div>
              <div className="c2pa-panel__hash-val">c2pa://claim/0x8b2e</div>
              <div className="c2pa-panel__hash-val">c2pa://claim/0x1d4c</div>
            </div>
            <div className="c2pa-panel__hash-col">
              <div className="c2pa-panel__hash-title">Hash Values</div>
              <div className="c2pa-panel__hash-val">sha256-0a3f7c</div>
              <div className="c2pa-panel__hash-val">sha256-9e1b4d</div>
              <div className="c2pa-panel__hash-val">sha256-5f8a2c</div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer buttons */}
      <div className="c2pa-panel__footer">
        <button className="c2pa-panel__btn c2pa-panel__btn--primary">Continue</button>
        <div className="c2pa-panel__footer-actions">
          <button className="c2pa-panel__btn c2pa-panel__btn--ghost">Cancel</button>
          <button className="c2pa-panel__btn c2pa-panel__btn--ghost">Publish</button>
          <button className="c2pa-panel__btn c2pa-panel__btn--ghost">Close</button>
        </div>
      </div>
    </div>
  );
}
