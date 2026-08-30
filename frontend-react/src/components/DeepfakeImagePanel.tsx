import { useEffect, useRef, useState } from "react";
import "./DeepfakeImagePanel.css";

interface DeepfakeImageProps {
  confidence: number;
  label: string;
  signals?: Record<string, any>;
}

export default function DeepfakeImagePanel({ confidence, label, signals }: DeepfakeImageProps) {
  const [mounted, setMounted] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);

  useEffect(() => { setMounted(true); }, []);

  // Animated heatmap canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const W = (canvas.width = 400);
    const H = (canvas.height = 350);
    let t = 0;

    const draw = () => {
      ctx.clearRect(0, 0, W, H);

      // Face outline
      const cx = W / 2;
      const cy = H / 2 - 20;
      const rx = 120;
      const ry = 150;

      // Heatmap glow
      const isFake = label === "fake";
      const grad = ctx.createRadialGradient(cx, cy, 10, cx, cy, rx * 1.5);
      if (isFake) {
        grad.addColorStop(0, `rgba(239, 68, 68, ${0.4 + Math.sin(t * 2) * 0.15})`);
        grad.addColorStop(0.5, `rgba(245, 158, 11, ${0.2 + Math.sin(t * 1.5) * 0.1})`);
        grad.addColorStop(1, "rgba(0, 0, 0, 0)");
      } else {
        grad.addColorStop(0, `rgba(34, 197, 94, ${0.3 + Math.sin(t * 2) * 0.1})`);
        grad.addColorStop(0.5, `rgba(6, 182, 212, ${0.15 + Math.sin(t * 1.5) * 0.05})`);
        grad.addColorStop(1, "rgba(0, 0, 0, 0)");
      }
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, W, H);

      // Face ellipse outline
      ctx.beginPath();
      ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
      ctx.strokeStyle = isFake
        ? `rgba(239, 68, 68, ${0.5 + Math.sin(t * 3) * 0.3})`
        : `rgba(34, 197, 94, ${0.5 + Math.sin(t * 3) * 0.3})`;
      ctx.lineWidth = 2;
      ctx.stroke();

      // Scanning line
      const scanY = (cy - ry) + ((t * 40) % (ry * 2));
      ctx.beginPath();
      ctx.moveTo(cx - rx, scanY);
      ctx.lineTo(cx + rx, scanY);
      ctx.strokeStyle = isFake
        ? "rgba(239, 68, 68, 0.6)"
        : "rgba(34, 197, 94, 0.6)";
      ctx.lineWidth = 1;
      ctx.stroke();

      // Eye markers
      const eyeY = cy - 20;
      [-40, 40].forEach((dx) => {
        ctx.beginPath();
        ctx.arc(cx + dx, eyeY, 8, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(6, 182, 212, ${0.5 + Math.sin(t * 4 + dx) * 0.3})`;
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(cx + dx, eyeY, 2, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(6, 182, 212, 0.8)";
        ctx.fill();
      });

      // Nose/mouth markers
      ctx.beginPath();
      ctx.arc(cx, cy + 20, 4, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(6, 182, 212, ${0.4 + Math.sin(t * 5) * 0.3})`;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(cx, cy + 60, 15, 0, Math.PI);
      ctx.strokeStyle = `rgba(6, 182, 212, ${0.3 + Math.sin(t * 2.5) * 0.2})`;
      ctx.lineWidth = 1;
      ctx.stroke();

      // Corner markers
      const corners = [[cx-rx, cy-ry], [cx+rx, cy-ry], [cx-rx, cy+ry], [cx+rx, cy+ry]];
      corners.forEach(([x, y]) => {
        ctx.beginPath();
        ctx.moveTo(x-8, y); ctx.lineTo(x+8, y);
        ctx.moveTo(x, y-8); ctx.lineTo(x, y+8);
        ctx.strokeStyle = "rgba(6, 182, 212, 0.4)";
        ctx.lineWidth = 1;
        ctx.stroke();
      });

      // Label
      ctx.font = "600 11px 'JetBrains Mono', monospace";
      ctx.fillStyle = isFake ? "rgba(239, 68, 68, 0.8)" : "rgba(34, 197, 94, 0.8)";
      ctx.textAlign = "center";
      ctx.fillText(isFake ? "MANIPULATION DETECTED" : "NO MANIPULATION DETECTED", cx, H - 20);

      t += 0.015;
      animRef.current = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(animRef.current);
  }, [label]);

  const isFake = label === "fake";

  const channelBars = [
    { label: "Frequency", value: isFake ? 0.72 : 0.35, color: isFake ? "var(--color-destructive)" : "var(--color-primary)" },
    { label: "Texture", value: isFake ? 0.65 : 0.28, color: isFake ? "var(--color-destructive)" : "var(--color-primary)" },
    { label: "Noise", value: isFake ? 0.58 : 0.15, color: isFake ? "var(--color-amber)" : "var(--color-primary)" },
    { label: "Color", value: isFake ? 0.45 : 0.22, color: isFake ? "var(--color-amber)" : "var(--color-primary)" },
    { label: "Edges", value: isFake ? 0.68 : 0.30, color: isFake ? "var(--color-destructive)" : "var(--color-primary)" },
  ];

  const rightBars = [
    { label: "Luminance", value: isFake ? 0.75 : 0.30, color: "var(--color-amber)" },
    { label: "Chroma", value: isFake ? 0.60 : 0.25, color: "var(--color-destructive)" },
    { label: "Saturation", value: isFake ? 0.45 : 0.20, color: "var(--color-primary)" },
    { label: "Hue Shift", value: isFake ? 0.55 : 0.35, color: "var(--color-amber)" },
  ];

  const metrics = [
    { label: "Face Samples", value: signals?.faces_detected ?? 1 },
    { label: "Eye Distortion", value: `${isFake ? 8.3 : 1.2}%` },
    { label: "Network Faces", value: signals?.network_periages ?? "Normal" },
  ];

  return (
    <div className={`deepfake-panel ${mounted ? "deepfake-panel--mounted" : ""}`}>
      {/* Header */}
      <div className="deepfake-panel__header">
        <div className="deepfake-panel__title">DEEPFAKE IMAGE ANALYSIS</div>
        <div className="deepfake-panel__nav">
          <span className="deepfake-panel__nav-item">Detect</span>
          <span className="deepfake-panel__nav-item">Results</span>
          <span className="deepfake-panel__nav-item">Native</span>
        </div>
      </div>

      <div className="deepfake-panel__body">
        {/* Left - Channel analysis bars */}
        <div className="deepfake-panel__left">
          <div className="deepfake-panel__section-title">Channel Analysis</div>
          <div className="deepfake-panel__bars">
            {channelBars.map((bar, i) => (
              <div key={bar.label} className="deepfake-panel__bar-row" style={{ animationDelay: `${i * 0.1}s` }}>
                <span className="deepfake-panel__bar-label">{bar.label}</span>
                <div className="deepfake-panel__bar-track">
                  <div
                    className="deepfake-panel__bar-fill"
                    style={{
                      width: `${bar.value * 100}%`,
                      backgroundColor: bar.color,
                      animationDelay: `${0.3 + i * 0.1}s`,
                    }}
                  />
                </div>
                <span className="deepfake-panel__bar-value">{(bar.value * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
          <div className="deepfake-panel__legend">
            <span><span className="deepfake-panel__legend-dot deepfake-panel__legend-dot--green" /> Detected</span>
            <span><span className="deepfake-panel__legend-dot deepfake-panel__legend-dot--red" /> Flagged</span>
          </div>
        </div>

        {/* Center - Face analysis canvas */}
        <div className="deepfake-panel__center">
          <canvas ref={canvasRef} className="deepfake-panel__canvas" />
        </div>

        {/* Right - Confidence bars */}
        <div className="deepfake-panel__right">
          <div className="deepfake-panel__confidence-badge">
            {isFake ? "THREAT" : "CLEAN"}
          </div>
          <div className="deepfake-panel__section-title">Channel Data</div>
          <div className="deepfake-panel__bars deepfake-panel__bars--right">
            {rightBars.map((bar, i) => (
              <div key={bar.label} className="deepfake-panel__bar-row" style={{ animationDelay: `${0.5 + i * 0.1}s` }}>
                <div className="deepfake-panel__bar-track deepfake-panel__bar-track--vertical">
                  <div
                    className="deepfake-panel__bar-fill deepfake-panel__bar-fill--vertical"
                    style={{
                      height: `${bar.value * 100}%`,
                      backgroundColor: bar.color,
                      animationDelay: `${0.6 + i * 0.1}s`,
                    }}
                  />
                </div>
                <span className="deepfake-panel__bar-label">{bar.label}</span>
              </div>
            ))}
          </div>
          <div className="deepfake-panel__axis-labels">
            <span>0</span><span>100</span><span>200</span><span>300</span><span>400</span>
          </div>
          <div className="deepfake-panel__axis-title">Raw Channel Pixels</div>
        </div>
      </div>

      {/* Metrics row */}
      <div className="deepfake-panel__metrics">
        {metrics.map((m) => (
          <div key={m.label} className="deepfake-panel__metric">
            <span className="deepfake-panel__metric-label">{m.label}</span>
            <span className="deepfake-panel__metric-value">{m.value}</span>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="deepfake-panel__footer">
        <div className="deepfake-panel__footer-item">
          <span className="deepfake-panel__footer-icon">🔍</span>
          Forensic CAM Analysis
        </div>
        <div className="deepfake-panel__footer-item">
          <span className="deepfake-panel__footer-icon">📊</span>
          Confidence: {confidence > 0.7 ? "HIGH" : confidence > 0.4 ? "MEDIUM" : "LOW"} ({(confidence * 100).toFixed(0)}%)
        </div>
        <div className="deepfake-panel__footer-item">
          <span className="deepfake-panel__footer-icon">👥</span>
          Network Faces: {signals?.faces_detected ?? 0} — {(confidence * 100).toFixed(0)}% manipulation
        </div>
      </div>
    </div>
  );
}
