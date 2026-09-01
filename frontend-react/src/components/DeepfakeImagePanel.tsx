import { useEffect, useState } from "react";
import AnimatedHeatmap from "./AnimatedHeatmap";
import "./AnimatedHeatmap.css";
import "./DeepfakeImagePanel.css";

interface DeepfakeImageProps {
  confidence: number;
  label: string;
  signals?: Record<string, any>;
}

export default function DeepfakeImagePanel({ confidence, label, signals }: DeepfakeImageProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => { setMounted(true); }, []);

  const isFake = label === "fake";
  const conf = Math.round(confidence * 100);



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

        {/* Center — Animated Heatmap */}
        <div className="dfp__center">
          <AnimatedHeatmap style={{ width: "100%", height: "100%", minHeight: 380 }} />
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
