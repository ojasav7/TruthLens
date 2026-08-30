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

  // Animated face scan canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const W = (canvas.width = 350);
    const H = (canvas.height = 400);
    const isTampered = label === "fake";
    let t = 0;

    const draw = () => {
      ctx.clearRect(0, 0, W, H);

      // Dark background with subtle grid
      ctx.fillStyle = "rgba(0, 10, 20, 0.9)";
      ctx.fillRect(0, 0, W, H);

      // Grid
      ctx.strokeStyle = "rgba(6, 182, 212, 0.04)";
      ctx.lineWidth = 1;
      for (let x = 0; x < W; x += 20) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
      }
      for (let y = 0; y < H; y += 20) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
      }

      // Face silhouette
      const cx = W / 2;
      const cy = H / 2 - 20;

      // Head outline
      ctx.beginPath();
      ctx.ellipse(cx, cy, 80, 100, 0, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(6, 182, 212, ${0.3 + Math.sin(t) * 0.1})`;
      ctx.lineWidth = 1;
      ctx.stroke();

      // Scanning circles
      for (let i = 0; i < 3; i++) {
        const r = 30 + i * 25 + Math.sin(t * 2 + i) * 5;
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(6, 182, 212, ${0.15 - i * 0.04})`;
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      // Crosshair
      const chSize = 40;
      ctx.beginPath();
      ctx.moveTo(cx - chSize, cy); ctx.lineTo(cx + chSize, cy);
      ctx.moveTo(cx, cy - chSize); ctx.lineTo(cx, cy + chSize);
      ctx.strokeStyle = `rgba(6, 182, 212, ${0.3 + Math.sin(t * 3) * 0.2})`;
      ctx.lineWidth = 1;
      ctx.stroke();

      // Eye dots
      [-25, 25].forEach((dx) => {
        ctx.beginPath();
        ctx.arc(cx + dx, cy - 15, 5, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(6, 182, 212, ${0.5 + Math.sin(t * 4 + dx) * 0.3})`;
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(cx + dx, cy - 15, 1.5, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(6, 182, 212, 0.9)";
        ctx.fill();
      });

      // Scan line
      const scanY = (cy - 100) + ((t * 30) % 200);
      ctx.beginPath();
      ctx.moveTo(cx - 80, scanY);
      ctx.lineTo(cx + 80, scanY);
      const scanGrad = ctx.createLinearGradient(cx - 80, 0, cx + 80, 0);
      scanGrad.addColorStop(0, "rgba(6, 182, 212, 0)");
      scanGrad.addColorStop(0.5, "rgba(6, 182, 212, 0.5)");
      scanGrad.addColorStop(1, "rgba(6, 182, 212, 0)");
      ctx.strokeStyle = scanGrad;
      ctx.lineWidth = 2;
      ctx.stroke();

      // Tampering indicator
      if (isTampered) {
        ctx.beginPath();
        ctx.arc(cx + 20, cy - 30, 15, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(239, 68, 68, ${0.4 + Math.sin(t * 5) * 0.3})`;
        ctx.lineWidth = 1.5;
        ctx.stroke();
        ctx.font = "600 8px 'JetBrains Mono', monospace";
        ctx.fillStyle = "rgba(239, 68, 68, 0.8)";
        ctx.textAlign = "center";
        ctx.fillText("TAMPER", cx + 20, cy - 28);
      }

      t += 0.015;
      animRef.current = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(animRef.current);
  }, [label]);

  const isTampered = label === "fake";

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
    { line: 15, tag: "PixelXDimension", value: "8192", flagged: false },
    { line: 16, tag: "Compression", value: "JPEG (lossy)", flagged: false },
    { line: 17, tag: "ThumbnailOffset", value: "0x0104 (260)", flagged: false },
    { line: 18, tag: "XMPToolkit", value: "Adobe XMP Core 7.0", flagged: true },
    { line: 19, tag: "HistoryAction", value: "saved, converted", flagged: true },
    { line: 20, tag: "DerivedFrom", value: "Original document", flagged: false },
  ];

  const stats = [
    { label: "Total Tags", value: `${exifTags.length}` },
    { label: "Flagged", value: `${exifTags.filter(t => t.flagged).length}` },
    { label: "File Size", value: "4.2 MB" },
    { label: "Resolution", value: "8192 × 5464" },
  ];

  return (
    <div className={`exif-panel ${mounted ? "exif-panel--mounted" : ""}`}>
      {/* Header */}
      <div className="exif-panel__header">
        <div className="exif-panel__title">
          <span className="exif-panel__menu">☰</span>
          EXIF Metadata Analysis
        </div>
        <div className="exif-panel__header-right">
          <span className="exif-panel__status">Master Field</span>
          <span className="exif-panel__badge">EXIF/DCF ▾</span>
        </div>
      </div>

      <div className="exif-panel__body">
        {/* Left - Face scan canvas */}
        <div className="exif-panel__scan">
          <div className="exif-panel__scan-header">
            <span className="exif-panel__scan-dot" />
            EXIF Metadata Scan
          </div>
          <canvas ref={canvasRef} className="exif-panel__canvas" />
          <div className="exif-panel__scan-footer">
            <span>RAW</span>
            <span>24.1 MP</span>
            <span>CMOS</span>
            <span>3:2</span>
          </div>
        </div>

        {/* Right - EXIF tags */}
        <div className="exif-panel__tags">
          <div className="exif-panel__tags-header">
            <span>EXIF/DCF Fields</span>
            <span className="exif-panel__tags-count">{exifTags.length} fields</span>
          </div>
          <div className="exif-panel__tags-list">
            {exifTags.map((tag, i) => (
              <div
                key={i}
                className={`exif-panel__tag ${tag.flagged ? "exif-panel__tag--flagged" : ""}`}
                style={{ animationDelay: `${i * 0.04}s` }}
              >
                <span className="exif-panel__tag-line">{tag.line}</span>
                <span className="exif-panel__tag-name">{tag.tag}</span>
                <span className="exif-panel__tag-value">{tag.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom stats */}
      <div className="exif-panel__stats">
        <div className="exif-panel__stats-left">
          {stats.map((s) => (
            <div key={s.label} className="exif-panel__stat-group">
              <div className="exif-panel__stat-label">{s.label}</div>
              <div className="exif-panel__stat-value">{s.value}</div>
            </div>
          ))}
        </div>
        <div className="exif-panel__stats-center">
          <div className="exif-panel__tamper-badge">
            <div className="exif-panel__tamper-title">Tampering Detection</div>
            <div className="exif-panel__tamper-value">
              {isTampered ? "Tampered" : "Normal"}
            </div>
            {isTampered && (
              <div className="exif-panel__tamper-bar">
                <div className="exif-panel__tamper-fill" />
              </div>
            )}
          </div>
        </div>
        <div className="exif-panel__stats-right">
          <div className="exif-panel__version">Tags Matched</div>
          <div className="exif-panel__version-value">
            {exifTags.filter(t => !t.flagged).length}/{exifTags.length} clean
          </div>
        </div>
      </div>
    </div>
  );
}
