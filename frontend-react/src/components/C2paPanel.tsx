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

  const isVerified = label === "real";

  // Animated chain-of-trust diagram
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const W = (canvas.width = 480);
    const H = (canvas.height = 260);
    let t = 0;

    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      ctx.fillStyle = "#050505";
      ctx.fillRect(0, 0, W, H);

      // Subtle grid
      ctx.strokeStyle = "rgba(34, 197, 94, 0.03)";
      ctx.lineWidth = 0.5;
      for (let x = 0; x < W; x += 20) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
      }
      for (let y = 0; y < H; y += 20) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
      }

      // Chain nodes — horizontal flow
      const nodes = [
        { x: 60, y: 80, label: "Creator" },
        { x: 170, y: 80, label: "Device" },
        { x: 280, y: 80, label: "Tool" },
        { x: 390, y: 80, label: "Platform" },
        { x: 225, y: 180, label: "Viewer" },
      ];

      // Draw edges
      const edges = [[0,1],[1,2],[2,3],[0,4],[1,4],[2,4],[3,4]];
      edges.forEach(([from, to]) => {
        const a = nodes[from];
        const b = nodes[to];
        const pulse = Math.sin(t * 2 + from + to) * 0.15 + 0.25;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.strokeStyle = isVerified
          ? `rgba(34, 197, 94, ${pulse})`
          : `rgba(239, 68, 68, ${pulse * 0.7})`;
        ctx.lineWidth = 1;
        ctx.stroke();

        // Traveling dot
        const p = (Math.sin(t * 1.5 + from) + 1) / 2;
        const dx = a.x + (b.x - a.x) * p;
        const dy = a.y + (b.y - a.y) * p;
        ctx.beginPath();
        ctx.arc(dx, dy, 2, 0, Math.PI * 2);
        ctx.fillStyle = isVerified ? "rgba(34, 197, 94, 0.6)" : "rgba(239, 68, 68, 0.4)";
        ctx.fill();
      });

      // Draw nodes
      nodes.forEach((n, i) => {
        // Outer ring
        ctx.beginPath();
        ctx.arc(n.x, n.y, 18 + Math.sin(t + i) * 2, 0, Math.PI * 2);
        ctx.strokeStyle = isVerified
          ? `rgba(34, 197, 94, ${0.25 + Math.sin(t * 2 + i) * 0.1})`
          : `rgba(239, 68, 68, ${0.2 + Math.sin(t * 2 + i) * 0.1})`;
        ctx.lineWidth = 1;
        ctx.stroke();

        // Inner hexagon
        ctx.beginPath();
        for (let j = 0; j < 6; j++) {
          const angle = (Math.PI / 3) * j - Math.PI / 6;
          const hx = n.x + 12 * Math.cos(angle);
          const hy = n.y + 12 * Math.sin(angle);
          j === 0 ? ctx.moveTo(hx, hy) : ctx.lineTo(hx, hy);
        }
        ctx.closePath();
        ctx.fillStyle = isVerified
          ? `rgba(34, 197, 94, ${0.08 + Math.sin(t + i) * 0.04})`
          : `rgba(239, 68, 68, ${0.06 + Math.sin(t + i) * 0.03})`;
        ctx.fill();
        ctx.strokeStyle = isVerified
          ? `rgba(34, 197, 94, ${0.5 + Math.sin(t * 2 + i) * 0.15})`
          : `rgba(239, 68, 68, ${0.4 + Math.sin(t * 2 + i) * 0.15})`;
        ctx.lineWidth = 1;
        ctx.stroke();

        // Center dot
        ctx.beginPath();
        ctx.arc(n.x, n.y, 3, 0, Math.PI * 2);
        ctx.fillStyle = isVerified ? "rgba(34, 197, 94, 0.7)" : "rgba(239, 68, 68, 0.5)";
        ctx.fill();

        // Label
        ctx.font = "600 8px 'JetBrains Mono', monospace";
        ctx.fillStyle = "#9ca3af";
        ctx.textAlign = "center";
        ctx.fillText(n.label.toUpperCase(), n.x, n.y + 30);
      });

      t += 0.012;
      animRef.current = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(animRef.current);
  }, [label, isVerified]);

  const certEntries = [
    { key: "Signed By", value: "TruthLens v4.0 (Adobe C2PA Toolkit)" },
    { key: "Assertion Service", value: "c2pa.truthlens.io" },
    { key: "Content Hash", value: "sha256-0a3f7c2e8b1d..." },
    { key: "Certificate", value: "Valid (expires 2027-03-15)" },
    { key: "Signature", value: "ES256 (P-256 + SHA-256)" },
    { key: "Trust Anchor", value: "C2PA Root CA (Adobe)" },
    { key: "Timestamp", value: "2026-08-30T09:23:17Z" },
    { key: "Manifest", value: "1 active claim" },
  ];

  const categories = [
    { label: "Valid Claims", count: 1 },
    { label: "Core Certificate", count: 1 },
    { label: "Assertions", count: 3 },
    { label: "Hash Mappings", count: 4 },
    { label: "User Assertions", count: 1 },
  ];

  const checks = [
    { label: "Provenance", status: "Verified" },
    { label: "Integrity", status: "Passed" },
    { label: "Revocation", status: "Clear" },
    { label: "Timestamp", status: "Valid" },
    { label: "Chain", status: "Complete" },
  ];

  return (
    <div className={`c2p ${mounted ? "c2p--mounted" : ""}`}>
      {/* Header */}
      <div className="c2p__header">
        <div className="c2p__header-left">
          <span className="c2p__menu">☰</span>
          <span className="c2p__title">C2PA — Content Provenance</span>
        </div>
        <div className="c2p__header-right">
          <span className="c2p__status">{isVerified ? "Signed" : "Unsigned"}</span>
          <span className={`c2p__badge ${isVerified ? "c2p__badge--ok" : "c2p__badge--fail"}`}>
            {isVerified ? "CERTIFIED" : "FAILED"}
          </span>
        </div>
      </div>

      <div className="c2p__body">
        {/* Left — Certificate */}
        <div className="c2p__cert">
          <div className={`c2p__cert-head ${isVerified ? "c2p__cert-head--ok" : "c2p__cert-head--fail"}`}>
            <span className="c2p__cert-icon">{isVerified ? "✓" : "✗"}</span>
            {isVerified ? "Signed" : "Unsigned"}
          </div>
          <div className="c2p__cert-list">
            {certEntries.map((entry, i) => (
              <div key={i} className="c2p__cert-row" style={{ animationDelay: `${i * 0.06}s` }}>
                <span className="c2p__cert-key">{entry.key}:</span>
                <span className="c2p__cert-val">{entry.value}</span>
              </div>
            ))}
          </div>
          <div className="c2p__cats">
            <div className="c2p__cats-title">Validation Summary</div>
            {categories.map((cat) => (
              <div key={cat.label} className="c2p__cat">
                <span>{cat.label}</span>
                <span className="c2p__cat-count">{cat.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Right — Chain of Trust */}
        <div className="c2p__flow">
          <div className="c2p__flow-head">
            <span className="c2p__flow-label">Chain of Trust</span>
            <span className="c2p__flow-filter">Signatures ▾</span>
          </div>
          <canvas ref={canvasRef} className="c2p__canvas" />
        </div>
      </div>

      {/* Bottom */}
      <div className="c2p__bottom">
        {/* Verification Checks */}
        <div className="c2p__checks">
          <div className="c2p__checks-title">Verification Checks</div>
          {checks.map((c) => (
            <div key={c.label} className="c2p__check">
              <span className={`c2p__check-dot ${isVerified ? "c2p__check-dot--ok" : "c2p__check-dot--fail"}`} />
              <span className="c2p__check-label">{c.label}</span>
              <span className={`c2p__check-status ${isVerified ? "c2p__check-status--ok" : "c2p__check-status--fail"}`}>
                {c.status}
              </span>
            </div>
          ))}
        </div>

        {/* Donut */}
        <div className="c2p__donut-wrap">
          <div className="c2p__donut">
            <svg viewBox="0 0 60 60">
              <circle cx="30" cy="30" r="24" fill="none" stroke="#1a1a1a" strokeWidth="5" />
              <circle
                cx="30" cy="30" r="24"
                fill="none"
                stroke={isVerified ? "#22c55e" : "#ef4444"}
                strokeWidth="5"
                strokeDasharray={`${(isVerified ? 0.85 : 0.25) * 150.8} 150.8`}
                strokeLinecap="round"
                transform="rotate(-90 30 30)"
                className="c2p__ring"
              />
            </svg>
            <div className="c2p__donut-text">
              <span className="c2p__donut-label">{isVerified ? "VERIFIED" : "FAILED"}</span>
              <span className="c2p__donut-sub">{isVerified ? "ALL PASS" : "CONFLICTS"}</span>
            </div>
          </div>
        </div>

        {/* Hashes */}
        <div className="c2p__hashes">
          <div className="c2p__hash-col">
            <div className="c2p__hash-title">Assertion URIs</div>
            <div className="c2p__hash-val">c2pa://claim/0x3a7f</div>
            <div className="c2p__hash-val">c2pa://claim/0x8b2e</div>
            <div className="c2p__hash-val">c2pa://claim/0x1d4c</div>
          </div>
          <div className="c2p__hash-col">
            <div className="c2p__hash-title">Hash Values</div>
            <div className="c2p__hash-val">sha256-0a3f7c</div>
            <div className="c2p__hash-val">sha256-9e1b4d</div>
            <div className="c2p__hash-val">sha256-5f8a2c</div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="c2p__footer">
        <button className="c2p__btn c2p__btn--primary">Continue</button>
        <div className="c2p__footer-actions">
          <button className="c2p__btn c2p__btn--ghost">Cancel</button>
          <button className="c2p__btn c2p__btn--ghost">Publish</button>
          <button className="c2p__btn c2p__btn--ghost">Close</button>
        </div>
      </div>
    </div>
  );
}
