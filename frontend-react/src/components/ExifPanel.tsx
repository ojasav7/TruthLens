import { useEffect, useRef, useState } from "react";
import "./ExifPanel.css";

interface ExifProps {
  confidence: number;
  label: string;
  signals?: Record<string, any>;
}

export default function ExifPanel({ label }: ExifProps) {
  const [mounted, setMounted] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);

  useEffect(() => { setMounted(true); }, []);

  const isTampered = label === "fake";

  // Animated face scan canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const W = (canvas.width = 320);
    const H = (canvas.height = 360);
    let t = 0;

    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      ctx.fillStyle = "#050505";
      ctx.fillRect(0, 0, W, H);

      // Grid
      ctx.strokeStyle = "rgba(6, 182, 212, 0.03)";
      ctx.lineWidth = 0.5;
      for (let x = 0; x < W; x += 18) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
      }
      for (let y = 0; y < H; y += 18) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
      }

      const cx = W / 2;
      const cy = H / 2 - 10;

      // Head outline
      ctx.beginPath();
      ctx.ellipse(cx, cy, 65, 85, 0, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(6, 182, 212, ${0.3 + Math.sin(t) * 0.1})`;
      ctx.lineWidth = 1;
      ctx.stroke();

      // Scanning rings
      for (let i = 0; i < 3; i++) {
        const r = 28 + i * 22 + Math.sin(t * 2 + i) * 4;
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(6, 182, 212, ${0.12 - i * 0.03})`;
        ctx.lineWidth = 0.8;
        ctx.stroke();
      }

      // Crosshair
      const ch = 35;
      ctx.beginPath();
      ctx.moveTo(cx - ch, cy); ctx.lineTo(cx + ch, cy);
      ctx.moveTo(cx, cy - ch); ctx.lineTo(cx, cy + ch);
      ctx.strokeStyle = `rgba(6, 182, 212, ${0.25 + Math.sin(t * 3) * 0.15})`;
      ctx.lineWidth = 0.8;
      ctx.stroke();

      // Eyes
      [-20, 20].forEach((dx) => {
        ctx.beginPath();
        ctx.ellipse(cx + dx, cy - 12, 9, 5, 0, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(6, 182, 212, ${0.4 + Math.sin(t * 4 + dx) * 0.2})`;
        ctx.lineWidth = 0.8;
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(cx + dx, cy - 12, 2, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(6, 182, 212, 0.7)";
        ctx.fill();
      });

      // Nose
      ctx.beginPath();
      ctx.moveTo(cx - 4, cy + 5);
      ctx.lineTo(cx, cy + 14);
      ctx.lineTo(cx + 4, cy + 5);
      ctx.strokeStyle = "rgba(255, 255, 255, 0.1)";
      ctx.lineWidth = 0.8;
      ctx.stroke();

      // Scan line
      const scanY = (cy - 85) + ((t * 25) % 170);
      const scanGrad = ctx.createLinearGradient(cx - 65, 0, cx + 65, 0);
      scanGrad.addColorStop(0, "rgba(6, 182, 212, 0)");
      scanGrad.addColorStop(0.5, "rgba(6, 182, 212, 0.5)");
      scanGrad.addColorStop(1, "rgba(6, 182, 212, 0)");
      ctx.beginPath();
      ctx.moveTo(cx - 65, scanY);
      ctx.lineTo(cx + 65, scanY);
      ctx.strokeStyle = scanGrad;
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Tamper indicator
      if (isTampered) {
        ctx.beginPath();
        ctx.arc(cx + 18, cy - 25, 12, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(239, 68, 68, ${0.4 + Math.sin(t * 5) * 0.2})`;
        ctx.lineWidth = 1.2;
        ctx.stroke();
        ctx.font = "600 7px 'JetBrains Mono', monospace";
        ctx.fillStyle = "rgba(239, 68, 68, 0.8)";
        ctx.textAlign = "center";
        ctx.fillText("TAMPER", cx + 18, cy - 23);
      }

      t += 0.015;
      animRef.current = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(animRef.current);
  }, [label, isTampered]);

  const exifTags = [
    { line: 1, tag: "Make", value: "Canon", flagged: false },
    { line: 2, tag: "Model", value: "Canon EOS R5", flagged: false },
    { line: 3, tag: "Software", value: "Adobe Photoshop 25.0", flagged: true },
    { line: 4, tag: "DateTime", value: "2024:11:30 15:30:00", flagged: false },
    { line: 5, tag: "ExposureTime", value: "1/250 sec", flagged: false },
    { line: 6, tag: "FNumber", value: "f/2.8", flagged: false },
    { line: 7, tag: "ISOSpeedRatings", value: "400", flagged: false },
    { line: 8, tag: "FocalLength", value: "85mm", flagged: false },
    { line: 9, tag: "ImageWidth", value: "8192 px", flagged: false },
    { line: 10, tag: "ImageHeight", value: "5464 px", flagged: false },
    { line: 11, tag: "ColorSpace", value: "sRGB IEC61966-2.1", flagged: false },
    { line: 12, tag: "GPSLatitude", value: "28.6139° N", flagged: false },
    { line: 13, tag: "GPSLongitude", value: "77.2090° E", flagged: false },
    { line: 14, tag: "Orientation", value: "Horizontal (normal)", flagged: false },
    { line: 15, tag: "Compression", value: "JPEG (lossy)", flagged: false },
    { line: 16, tag: "XMPToolkit", value: "Adobe XMP Core 7.0", flagged: true },
    { line: 17, tag: "HistoryAction", value: "saved, converted", flagged: true },
    { line: 18, tag: "DerivedFrom", value: "Original document", flagged: false },
  ];

  const stats = [
    { label: "Total Fields", value: `${exifTags.length}` },
    { label: "Flagged", value: `${exifTags.filter(t => t.flagged).length}` },
    { label: "File Size", value: "4.2 MB" },
    { label: "Resolution", value: "8192 × 5464" },
  ];

  return (
    <div className={`exp ${mounted ? "exp--mounted" : ""}`}>
      {/* Header */}
      <div className="exp__header">
        <div className="exp__header-left">
          <span className="exp__menu">☰</span>
          <span className="exp__title">EXIF Metadata Analysis</span>
        </div>
        <div className="exp__header-right">
          <span className="exp__status">Master Field</span>
          <span className="exp__badge">EXIF/DCF ▾</span>
        </div>
      </div>

      <div className="exp__body">
        {/* Left — Face Scan Canvas */}
        <div className="exp__scan">
          <div className="exp__scan-head">
            <span className="exp__scan-dot" />
            EXIF Metadata Scan
          </div>
          <canvas ref={canvasRef} className="exp__canvas" />
          <div className="exp__scan-foot">
            <span>RAW</span>
            <span>24.1 MP</span>
            <span>CMOS</span>
            <span>3:2</span>
          </div>
        </div>

        {/* Right — EXIF Tags */}
        <div className="exp__tags">
          <div className="exp__tags-head">
            <span>EXIF/DCF Fields</span>
            <span className="exp__tags-count">{exifTags.length} fields</span>
          </div>
          <div className="exp__tags-list">
            {exifTags.map((tag, i) => (
              <div
                key={i}
                className={`exp__tag ${tag.flagged ? "exp__tag--flag" : ""}`}
                style={{ animationDelay: `${i * 0.03}s` }}
              >
                <span className="exp__tag-line">{tag.line}</span>
                <span className="exp__tag-name">{tag.tag}</span>
                <span className="exp__tag-val">{tag.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Stats */}
      <div className="exp__stats">
        <div className="exp__stats-left">
          {stats.map((s) => (
            <div key={s.label} className="exp__stat">
              <span className="exp__stat-label">{s.label}</span>
              <span className="exp__stat-value">{s.value}</span>
            </div>
          ))}
        </div>
        <div className="exp__stats-center">
          <div className="exp__tamper">
            <div className="exp__tamper-title">Tampering Detection</div>
            <div className={`exp__tamper-val ${isTampered ? "exp__tamper-val--bad" : "exp__tamper-val--ok"}`}>
              {isTampered ? "Tampered" : "Normal"}
            </div>
            {isTampered && (
              <div className="exp__tamper-bar">
                <div className="exp__tamper-fill" />
              </div>
            )}
          </div>
        </div>
        <div className="exp__stats-right">
          <div className="exp__stat-label">Tags Matched</div>
          <div className="exp__stat-val-big">
            {exifTags.filter(t => !t.flagged).length}/{exifTags.length}
          </div>
          <div className="exp__stat-sub">clean</div>
        </div>
      </div>
    </div>
  );
}
