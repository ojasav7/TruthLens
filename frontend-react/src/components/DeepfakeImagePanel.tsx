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

  const isFake = label === "fake";
  const conf = Math.round(confidence * 100);

  // Animated heatmap canvas — beautiful face visualization
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const W = (canvas.width = 360);
    const H = (canvas.height = 380);
    let t = 0;

    const draw = () => {
      ctx.clearRect(0, 0, W, H);

      // Dark background
      ctx.fillStyle = "#0a0a0a";
      ctx.fillRect(0, 0, W, H);

      // Subtle grid
      ctx.strokeStyle = "rgba(34, 197, 94, 0.03)";
      ctx.lineWidth = 0.5;
      for (let x = 0; x < W; x += 24) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
      }
      for (let y = 0; y < H; y += 24) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
      }

      const cx = W / 2;
      const cy = H / 2 - 10;

      // Face outline — smooth oval
      ctx.beginPath();
      ctx.ellipse(cx, cy, 70, 95, 0, 0, Math.PI * 2);
      ctx.strokeStyle = isFake
        ? `rgba(239, 68, 68, ${0.4 + Math.sin(t * 2) * 0.15})`
        : `rgba(34, 197, 94, ${0.4 + Math.sin(t * 2) * 0.15})`;
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Inner face features — eyes
      const eyeY = cy - 15;
      [-22, 22].forEach((dx) => {
        // Eye socket
        ctx.beginPath();
        ctx.ellipse(cx + dx, eyeY, 12, 7, 0, 0, Math.PI * 2);
        ctx.strokeStyle = isFake
          ? `rgba(239, 68, 68, ${0.3 + Math.sin(t * 3 + dx) * 0.15})`
          : `rgba(34, 197, 94, ${0.3 + Math.sin(t * 3 + dx) * 0.15})`;
        ctx.lineWidth = 1;
        ctx.stroke();

        // Pupil
        ctx.beginPath();
        ctx.arc(cx + dx, eyeY, 3, 0, Math.PI * 2);
        ctx.fillStyle = isFake
          ? `rgba(239, 68, 68, ${0.6 + Math.sin(t * 4 + dx) * 0.2})`
          : `rgba(34, 197, 94, ${0.6 + Math.sin(t * 4 + dx) * 0.2})`;
        ctx.fill();
      });

      // Nose
      ctx.beginPath();
      ctx.moveTo(cx - 6, cy + 5);
      ctx.lineTo(cx, cy + 18);
      ctx.lineTo(cx + 6, cy + 5);
      ctx.strokeStyle = `rgba(255, 255, 255, 0.15)`;
      ctx.lineWidth = 1;
      ctx.stroke();

      // Mouth
      ctx.beginPath();
      ctx.ellipse(cx, cy + 40, 18, 6, 0, 0, Math.PI);
      ctx.strokeStyle = `rgba(255, 255, 255, 0.12)`;
      ctx.lineWidth = 1;
      ctx.stroke();

      // Scanning line — sweeps across face
      const scanY = (cy - 95) + ((t * 35) % 190);
      const scanGrad = ctx.createLinearGradient(cx - 70, 0, cx + 70, 0);
      scanGrad.addColorStop(0, "rgba(34, 197, 94, 0)");
      scanGrad.addColorStop(0.3, isFake ? "rgba(239, 68, 68, 0.4)" : "rgba(34, 197, 94, 0.4)");
      scanGrad.addColorStop(0.5, isFake ? "rgba(239, 68, 68, 0.7)" : "rgba(34, 197, 94, 0.7)");
      scanGrad.addColorStop(0.7, isFake ? "rgba(239, 68, 68, 0.4)" : "rgba(34, 197, 94, 0.4)");
      scanGrad.addColorStop(1, "rgba(34, 197, 94, 0)");
      ctx.beginPath();
      ctx.moveTo(cx - 70, scanY);
      ctx.lineTo(cx + 70, scanY);
      ctx.strokeStyle = scanGrad;
      ctx.lineWidth = 2;
      ctx.stroke();

      // Corner brackets
      const bSize = 16;
      const corners = [
        [cx - 55, cy - 75], [cx + 55, cy - 75],
        [cx - 55, cy + 75], [cx + 55, cy + 75]
      ];
      corners.forEach(([x, y], i) => {
        const dx = i % 2 === 0 ? 1 : -1;
        const dy = i < 2 ? 1 : -1;
        ctx.beginPath();
        ctx.moveTo(x, y + dy * bSize);
        ctx.lineTo(x, y);
        ctx.lineTo(x + dx * bSize, y);
        ctx.strokeStyle = isFake
          ? `rgba(239, 68, 68, ${0.4 + Math.sin(t + i) * 0.15})`
          : `rgba(34, 197, 94, ${0.4 + Math.sin(t + i) * 0.15})`;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      });

      // Confidence ring around face
      const ringProgress = confidence;
      ctx.beginPath();
      ctx.arc(cx, cy, 110, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * ringProgress);
      ctx.strokeStyle = isFake
        ? `rgba(239, 68, 68, 0.3)`
        : `rgba(34, 197, 94, 0.3)`;
      ctx.lineWidth = 3;
      ctx.stroke();

      // Confidence text
      ctx.font = "700 22px 'JetBrains Mono', monospace";
      ctx.fillStyle = isFake ? "rgba(239, 68, 68, 0.8)" : "rgba(34, 197, 94, 0.8)";
      ctx.textAlign = "center";
      ctx.fillText(`${conf}%`, cx, H - 30);

      ctx.font = "500 9px 'JetBrains Mono', monospace";
      ctx.fillStyle = "rgba(255, 255, 255, 0.3)";
      ctx.fillText(isFake ? "MANIPULATION DETECTED" : "NO MANIPULATION DETECTED", cx, H - 14);

      t += 0.015;
      animRef.current = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(animRef.current);
  }, [label, confidence, isFake, conf]);

  const channelBars = [
    { label: "Frequency", value: isFake ? 0.72 : 0.35, severity: isFake ? "high" : "low" },
    { label: "Texture", value: isFake ? 0.65 : 0.28, severity: isFake ? "high" : "low" },
    { label: "Noise", value: isFake ? 0.58 : 0.15, severity: isFake ? "medium" : "low" },
    { label: "Color", value: isFake ? 0.45 : 0.22, severity: isFake ? "medium" : "low" },
    { label: "Edges", value: isFake ? 0.68 : 0.30, severity: isFake ? "high" : "low" },
  ];

  const channelData = [
    { label: "Luminance", value: isFake ? 0.75 : 0.30 },
    { label: "Chroma", value: isFake ? 0.60 : 0.25 },
    { label: "Saturation", value: isFake ? 0.45 : 0.20 },
    { label: "Hue Shift", value: isFake ? 0.55 : 0.35 },
  ];

  const metrics = [
    { label: "Face Samples", value: String(signals?.faces_detected ?? 1) },
    { label: "Eye Distortion", value: `${isFake ? 8.3 : 1.2}%` },
    { label: "Network Faces", value: signals?.network_periages ?? "Normal" },
  ];

  return (
    <div className={`dfp ${mounted ? "dfp--mounted" : ""}`}>
      {/* Header */}
      <div className="dfp__header">
        <div className="dfp__header-left">
          <div className="dfp__dot dfp__dot--green" />
          <span className="dfp__title">DEEPFAKE IMAGE ANALYSIS</span>
        </div>
        <div className="dfp__tabs">
          <span className="dfp__tab dfp__tab--active">Detect</span>
          <span className="dfp__tab">Results</span>
          <span className="dfp__tab">Native</span>
        </div>
      </div>

      <div className="dfp__body">
        {/* Left — Channel Analysis */}
        <div className="dfp__left">
          <div className="dfp__section-head">Channel Analysis</div>
          <div className="dfp__bars">
            {channelBars.map((bar, i) => (
              <div key={bar.label} className="dfp__bar-row" style={{ animationDelay: `${i * 0.08}s` }}>
                <span className="dfp__bar-label">{bar.label}</span>
                <div className="dfp__bar-track">
                  <div
                    className={`dfp__bar-fill dfp__bar-fill--${bar.severity}`}
                    style={{ width: `${bar.value * 100}%`, animationDelay: `${0.2 + i * 0.08}s` }}
                  />
                </div>
                <span className="dfp__bar-val">{Math.round(bar.value * 100)}%</span>
              </div>
            ))}
          </div>
          <div className="dfp__legend">
            <span className="dfp__legend-item"><span className="dfp__legend-dot dfp__legend-dot--green" /> Normal</span>
            <span className="dfp__legend-item"><span className="dfp__legend-dot dfp__legend-dot--red" /> Flagged</span>
          </div>
        </div>

        {/* Center — Face Canvas */}
        <div className="dfp__center">
          <canvas ref={canvasRef} className="dfp__canvas" />
          <div className="dfp__badge-row">
            <span className={`dfp__badge ${isFake ? "dfp__badge--threat" : "dfp__badge--clean"}`}>
              {isFake ? "THREAT" : "CLEAN"}
            </span>
          </div>
        </div>

        {/* Right — Channel Data */}
        <div className="dfp__right">
          <div className="dfp__section-head">Channel Data</div>
          <div className="dfp__vbars">
            {channelData.map((bar, i) => (
              <div key={bar.label} className="dfp__vbar-col" style={{ animationDelay: `${0.3 + i * 0.1}s` }}>
                <div className="dfp__vbar-track">
                  <div
                    className="dfp__vbar-fill"
                    style={{ height: `${bar.value * 100}%`, animationDelay: `${0.4 + i * 0.1}s` }}
                  />
                </div>
                <span className="dfp__vbar-label">{bar.label}</span>
              </div>
            ))}
          </div>
          <div className="dfp__axis">
            <span>0</span><span>100</span><span>200</span><span>300</span><span>400</span>
          </div>
          <div className="dfp__axis-title">Raw Channel Pixels</div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="dfp__metrics">
        {metrics.map((m) => (
          <div key={m.label} className="dfp__metric">
            <span className="dfp__metric-label">{m.label}</span>
            <span className="dfp__metric-value">{m.value}</span>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="dfp__footer">
        <div className="dfp__footer-item">
          <span className="dfp__footer-icon">🔍</span>
          Forensic CAM Analysis
        </div>
        <div className="dfp__footer-item">
          <span className="dfp__footer-icon">📊</span>
          Confidence: {conf > 70 ? "HIGH" : conf > 40 ? "MEDIUM" : "LOW"} ({conf}%)
        </div>
        <div className="dfp__footer-item">
          <span className="dfp__footer-icon">👥</span>
          Network Faces: {signals?.faces_detected ?? 0} — {conf}% manipulation
        </div>
      </div>
    </div>
  );
}
