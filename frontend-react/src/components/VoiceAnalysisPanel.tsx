import { useEffect, useRef, useState } from "react";
import "./VoiceAnalysisPanel.css";

interface VoiceAnalysisProps {
  confidence: number;
  label: string;
  signals?: Record<string, any>;
}

export default function VoiceAnalysisPanel({ confidence, label }: VoiceAnalysisProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Animated waveform
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const W = canvas.width = 800;
    const H = canvas.height = 200;
    let t = 0;

    const draw = () => {
      ctx.clearRect(0, 0, W, H);

      // Grid lines
      ctx.strokeStyle = "rgba(34, 197, 94, 0.08)";
      ctx.lineWidth = 1;
      for (let y = 0; y < H; y += 20) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(W, y);
        ctx.stroke();
      }
      for (let x = 0; x < W; x += 40) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, H);
        ctx.stroke();
      }

      // Waveform
      const mid = H / 2;
      const isFake = label === "fake" || label === "cloned";

      // Primary waveform
      ctx.beginPath();
      ctx.strokeStyle = isFake ? "rgba(239, 68, 68, 0.9)" : "rgba(34, 197, 94, 0.9)";
      ctx.lineWidth = 1.5;
      for (let x = 0; x < W; x++) {
        const freq1 = Math.sin((x * 0.02) + t * 2) * 30;
        const freq2 = Math.sin((x * 0.05) + t * 3) * 15;
        const freq3 = Math.sin((x * 0.01) + t * 0.5) * 20;
        const noise = (Math.random() - 0.5) * (isFake ? 8 : 3);
        const envelope = Math.sin((x / W) * Math.PI);
        const y = mid + (freq1 + freq2 + freq3 + noise) * envelope;
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      // Ghost waveform (offset)
      ctx.beginPath();
      ctx.strokeStyle = isFake ? "rgba(239, 68, 68, 0.3)" : "rgba(34, 197, 94, 0.3)";
      ctx.lineWidth = 1;
      for (let x = 0; x < W; x++) {
        const freq1 = Math.sin((x * 0.025) + t * 1.8 + 1) * 25;
        const freq2 = Math.sin((x * 0.04) + t * 2.5 + 2) * 12;
        const envelope = Math.sin((x / W) * Math.PI);
        const y = mid + (freq1 + freq2) * envelope;
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      // Playhead
      const playX = (t * 50) % W;
      ctx.beginPath();
      ctx.strokeStyle = "rgba(34, 197, 94, 0.6)";
      ctx.lineWidth = 2;
      ctx.moveTo(playX, 0);
      ctx.lineTo(playX, H);
      ctx.stroke();

      t += 0.02;
      animRef.current = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(animRef.current);
  }, [label]);

  const isFake = label === "fake" || label === "cloned";
  const detectionItems = [
    { name: "Voice Clarity", value: isFake ? 0.3 : 0.85, animated: true },
    { name: "Anomalies", value: isFake ? 0.82 : 0.12, animated: true },
    { name: "Pitch Consistency", value: isFake ? 0.25 : 0.91, animated: true },
    { name: "Spectral Integrity", value: isFake ? 0.18 : 0.88, animated: true },
    { name: "Timing Patterns", value: isFake ? 0.35 : 0.79, animated: true },
  ];

  const spectralValues = [
    { label: "FREQ", value: isFake ? "2,847 Hz" : "1,203 Hz" },
    { label: "SPEC", value: isFake ? "0.42" : "0.87" },
    { label: "NOISE", value: isFake ? "HIGH" : "LOW" },
    { label: "RATE", value: "16000 Hz" },
  ];

  return (
    <div className={`voice-panel ${mounted ? "voice-panel--mounted" : ""}`}>
      {/* Header */}
      <div className="voice-panel__header">
        <div className="voice-panel__header-label">
          <span className="voice-panel__dot" />
          VOICE ANALYSIS
        </div>
        <div className="voice-panel__header-status">
          {isFake ? "~ THREAT DETECTED ~" : "~ NO THREAT ~"}
        </div>
      </div>

      <div className="voice-panel__body">
        {/* Left sidebar - Detection items */}
        <div className="voice-panel__sidebar">
          <div className="voice-panel__sidebar-title">
            VOICECLONE<br />DETECTIONS
          </div>
          {detectionItems.map((item, i) => (
            <div
              key={item.name}
              className="voice-panel__detection-item"
              style={{ animationDelay: `${i * 0.15}s` }}
            >
              <div className="voice-panel__detection-name">{item.name}</div>
              <div className="voice-panel__detection-bar">
                <div
                  className="voice-panel__detection-fill"
                  style={{
                    width: `${item.value * 100}%`,
                    backgroundColor: item.value > 0.5 ? "var(--color-destructive)" : "var(--color-primary)",
                    animationDelay: `${0.5 + i * 0.15}s`,
                  }}
                />
              </div>
              <div className="voice-panel__detection-value">
                {(item.value * 100).toFixed(0)}%
              </div>
            </div>
          ))}
        </div>

        {/* Center - Waveform */}
        <div className="voice-panel__waveform">
          <canvas ref={canvasRef} className="voice-panel__canvas" />
          <div className="voice-panel__waveform-label">
            SPECTRAL VALUES: {(confidence * 100000).toFixed(0)}
          </div>
        </div>

        {/* Right sidebar - Spectral info */}
        <div className="voice-panel__spectral">
          <div className="voice-panel__spectral-title">SPECTRAL VALUES</div>
          <div className="voice-panel__spectral-big">
            {(confidence * 100).toFixed(1)}%
          </div>
          <div className="voice-panel__spectral-grid">
            {spectralValues.map((sv) => (
              <div key={sv.label} className="voice-panel__spectral-item">
                <span className="voice-panel__spectral-label">{sv.label}</span>
                <span className="voice-panel__spectral-val">{sv.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom timeline */}
      <div className="voice-panel__timeline">
        <div className="voice-panel__timeline-bar">
          <div className="voice-panel__timeline-progress" />
        </div>
        <div className="voice-panel__timeline-markers">
          {[0, 500, 1000, 1500, 2000, 2500].map((ms) => (
            <span key={ms}>{ms}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
