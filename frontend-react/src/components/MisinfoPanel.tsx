import { useEffect, useState, useRef } from "react";
import "./MisinfoPanel.css";

interface MisinfoProps {
  confidence: number;
  label: string;
  text?: string;
  signals?: Record<string, any>;
}

export default function MisinfoPanel({ label, text }: MisinfoProps) {
  const [mounted, setMounted] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);

  useEffect(() => {
    setMounted(true);
    // Word highlighting is handled by CSS animation on .misinfo-highlight
  }, [text]);

  // Evidence graph animation
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const W = (canvas.width = 300);
    const H = (canvas.height = 250);

    // Nodes
    const nodes = Array.from({ length: 12 }, (_, i) => ({
      x: 60 + Math.random() * (W - 120),
      y: 40 + Math.random() * (H - 80),
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      r: 3 + Math.random() * 3,
      label: ["Source", "Claim", "Evidence", "Cross-ref", "Fact-check", "Verify", "Flag", "Audit", "Trail", "Hash", "Chain", "Trust"][i],
    }));

    // Edges
    const edges: { from: number; to: number; strength: number }[] = [];
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        if (Math.random() > 0.6) {
          edges.push({ from: i, to: j, strength: Math.random() });
        }
      }
    }

    let t = 0;

    const draw = () => {
      ctx.clearRect(0, 0, W, H);

      // Move nodes
      nodes.forEach((n) => {
        n.x += n.vx;
        n.y += n.vy;
        if (n.x < 20 || n.x > W - 20) n.vx *= -1;
        if (n.y < 20 || n.y > H - 20) n.vy *= -1;
      });

      // Draw edges
      edges.forEach((e) => {
        const a = nodes[e.from];
        const b = nodes[e.to];
        const pulse = Math.sin(t * 2 + e.strength * 10) * 0.3 + 0.5;
        ctx.beginPath();
        ctx.strokeStyle = e.strength > 0.7
          ? `rgba(239, 68, 68, ${pulse * 0.5})`
          : `rgba(34, 197, 94, ${pulse * 0.3})`;
        ctx.lineWidth = e.strength > 0.7 ? 1.5 : 0.5;
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
      });

      // Draw nodes
      nodes.forEach((n) => {
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(34, 197, 94, ${0.6 + Math.sin(t + n.x) * 0.3})`;
        ctx.fill();
        ctx.strokeStyle = "rgba(34, 197, 94, 0.3)";
        ctx.lineWidth = 1;
        ctx.stroke();
      });

      t += 0.01;
      animRef.current = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(animRef.current);
  }, []);

  const isFake = label === "fake";
  const biasScore = isFake ? { bias: 0.85, credibility: 0.15 } : { bias: 0.12, credibility: 0.88 };
  const sourceScore = isFake ? 23 : 91;
  const claimsFlagged = isFake ? 3 : 0;
  const totalClaims = 5;

  // Highlight suspicious words
  const highlightText = (input: string) => {
    if (!input) return "";
    const suspiciousWords = new Set([
      "shocking", "exposed", "breaking", "click", "now", "leaked",
      "secret", "conspiracy", "wake", "proof", "hate", "weird",
      "trick", "they", "dont", "want", "confirmed", "banned",
    ]);
    const words = input.split(/(\s+)/);
    return words.map((word, i) => {
      const clean = word.replace(/[^a-zA-Z]/g, "").toLowerCase();
      if (suspiciousWords.has(clean)) {
        return `<span class="misinfo-highlight" style="animation-delay:${i * 0.05}s">${word}</span>`;
      }
      return word;
    }).join("");
  };

  return (
    <div className={`misinfo-panel ${mounted ? "misinfo-panel--mounted" : ""}`}>
      {/* Header */}
      <div className="misinfo-panel__header">
        <div className="misinfo-panel__title">
          MISINFORMATION ANALYSIS
        </div>
        <div className="misinfo-panel__tabs">
          {["SCAN", "HEAVY", "TRACE", "TESTS"].map((tab, i) => (
            <button
              key={tab}
              className={`misinfo-panel__tab ${i === 0 ? "misinfo-panel__tab--active" : ""}`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      <div className="misinfo-panel__body">
        {/* Left column - Scores */}
        <div className="misinfo-panel__scores">
          {/* Bias Score */}
          <div className="misinfo-panel__score-card">
            <div className="misinfo-panel__score-label">BIAS SCORE</div>
            <div className="misinfo-panel__score-value" style={{ color: isFake ? "var(--color-destructive)" : "var(--color-primary)" }}>
              {isFake ? "1/4/0.8" : "1/1/0.1"}
            </div>
            <div className="misinfo-panel__score-bar">
              <div
                className="misinfo-panel__score-fill"
                style={{
                  width: `${biasScore.bias * 100}%`,
                  backgroundColor: "var(--color-destructive)",
                }}
              />
            </div>
          </div>

          {/* Claim Credibility */}
          <div className="misinfo-panel__score-card">
            <div className="misinfo-panel__score-label">CLAIM CREDIBILITY</div>
            <div className="misinfo-panel__score-ring">
              <svg viewBox="0 0 80 80">
                <circle cx="40" cy="40" r="34" fill="none" stroke="var(--color-border)" strokeWidth="4" />
                <circle
                  cx="40" cy="40" r="34"
                  fill="none"
                  stroke={isFake ? "var(--color-destructive)" : "var(--color-primary)"}
                  strokeWidth="4"
                  strokeDasharray={`${(isFake ? 0.2 : 0.9) * 213.6} 213.6`}
                  strokeLinecap="round"
                  transform="rotate(-90 40 40)"
                  className="misinfo-ring-animated"
                />
              </svg>
              <div className="misinfo-panel__score-ring-value">
                {isFake ? 2 : 9}
              </div>
            </div>
          </div>

          {/* Source */}
          <div className="misinfo-panel__score-card">
            <div className="misinfo-panel__score-label">SOURCE</div>
            <div className="misinfo-panel__score-big" style={{ color: isFake ? "var(--color-destructive)" : "var(--color-primary)" }}>
              {sourceScore}%
            </div>
            <div className="misinfo-panel__score-bar">
              <div
                className="misinfo-panel__score-fill"
                style={{
                  width: `${sourceScore}%`,
                  backgroundColor: isFake ? "var(--color-destructive)" : "var(--color-primary)",
                }}
              />
            </div>
          </div>
        </div>

        {/* Center - Article text */}
        <div className="misinfo-panel__article">
          <div className="misinfo-panel__article-title">Article — Misinformation Analysis</div>
          <div className="misinfo-panel__article-content">
            {text ? (
              <div dangerouslySetInnerHTML={{ __html: highlightText(text) }} />
            ) : (
              <div className="misinfo-panel__article-placeholder">
                Analyzing text content for misinformation patterns, bias indicators,
                and fabricated claims. Highlighting suspicious phrases in real-time.
              </div>
            )}
          </div>
        </div>

        {/* Right - Evidence graph */}
        <div className="misinfo-panel__graph">
          <div className="misinfo-panel__graph-tabs">
            <span>Source Chain</span>
            <span>Space Probability</span>
            <span className="misinfo-panel__graph-tab--active">The Path</span>
          </div>
          <canvas ref={canvasRef} className="misinfo-panel__graph-canvas" />
          <div className="misinfo-panel__graph-legend">
            <div className="misinfo-panel__legend-item">
              <span className="misinfo-panel__legend-dot" style={{ background: "var(--color-primary)" }} />
              Verified
            </div>
            <div className="misinfo-panel__legend-item">
              <span className="misinfo-panel__legend-dot" style={{ background: "var(--color-destructive)" }} />
              Suspicious
            </div>
          </div>
        </div>
      </div>

      {/* Footer - Claims flagged */}
      <div className="misinfo-panel__footer">
        <div className="misinfo-panel__claims-flagged">
          <span className="misinfo-panel__claims-icon">!</span>
          FABRICATED CLAIMS FLAGGED
          <span className="misinfo-panel__claims-count">
            {claimsFlagged} / {totalClaims}
          </span>
        </div>
      </div>
    </div>
  );
}
