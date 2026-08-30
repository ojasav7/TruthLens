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
      ctx.strokeStyle = "rgba(34, 197, 94, 0.04)";
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
      ctx.strokeStyle = `rgba(34, 197, 94, ${0.3 + Math.sin(t) * 0.1})`;
      ctx.lineWidth = 1;
      ctx.stroke();

      // Scanning circles
      for (let i = 0; i < 3; i++) {
        const r = 30 + i * 25 + Math.sin(t * 2 + i) * 5;
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(34, 197, 94, ${0.15 - i * 0.04})`;
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      // Crosshair
      const chSize = 40;
      ctx.beginPath();
      ctx.moveTo(cx - chSize, cy); ctx.lineTo(cx + chSize, cy);
      ctx.moveTo(cx, cy - chSize); ctx.lineTo(cx, cy + chSize);
      ctx.strokeStyle = `rgba(34, 197, 94, ${0.3 + Math.sin(t * 3) * 0.2})`;
      ctx.lineWidth = 1;
      ctx.stroke();

      // Eye dots
      [-25, 25].forEach((dx) => {
        ctx.beginPath();
        ctx.arc(cx + dx, cy - 15, 5, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(34, 197, 94, ${0.5 + Math.sin(t * 4 + dx) * 0.3})`;
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(cx + dx, cy - 15, 1.5, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(34, 197, 94, 0.9)";
        ctx.fill();
      });

      // Scan line
      const scanY = (cy - 100) + ((t * 30) % 200);
      ctx.beginPath();
      ctx.moveTo(cx - 80, scanY);
      ctx.lineTo(cx + 80, scanY);
      const scanGrad = ctx.createLinearGradient(cx - 80, 0, cx + 80, 0);
      scanGrad.addColorStop(0, "rgba(34, 197, 94, 0)");
      scanGrad.addColorStop(0.5, "rgba(34, 197, 94, 0.5)");
      scanGrad.addColorStop(1, "rgba(34, 197, 94, 0)");
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
    { line: 1, text: "12  Matter Issussed Field", flagged: false },
    { line: 42, text: "Cust Tesk A Sate Teks ANEED CDP,", flagged: true },
    { line: 45, text: "Anent Sectar folic Lows", flagged: true },
    { line: 47, text: "Weiepes: FEPPS GPP 3 hes 23 conte(609)", flagged: false },
    { line: 19, text: "Trdectal — CBM,", flagged: true },
    { line: 45, text: "Ancradate: Past neteratfonyments,,ourraisstedd", flagged: false },
    { line: 7, text: "tiffers,,pilgep", flagged: true },
    { line: 60, text: "Rej as 1as facters cancer cistances GPP", flagged: true },
    { line: 73, text: "Hosses: (Gft lavdcei seatcets, Shingcrefal)", flagged: false },
    { line: 72, text: "Tampver 1:08 lerising = Groute,", flagged: true },
    { line: 16, text: "Hex e delereiesf ficg cetes", flagged: false },
    { line: 72, text: "Reports: Bar/ T meslying oaosline detoing strater", flagged: false },
    { line: 28, text: "Micence al (castanpe — CEMDO,)", flagged: true },
    { line: 29, text: "Terepes: AL Tostercaing conator rnoFGSS fetetor", flagged: false },
    { line: 87, text: "Renies — ref Fortmations GEP7.", flagged: true },
    { line: 37, text: "Assors are nate datlery softringind", flagged: false },
    { line: 72, text: "Relessoces (YUOL etorprader anxia for VQL ~10)", flagged: false },
    { line: 18, text: "Tetanbers rnetertg — 18.", flagged: true },
    { line: 57, text: "Tnerger erl weing Mssing compeie-mew10.00", flagged: true },
  ];

  const stats = [
    { label: "EXIF Data Total", values: ["9000", "05,805"] },
    { label: "Status", values: ["3,22.00", "545.50"] },
  ];

  return (
    <div className={`exif-panel ${mounted ? "exif-panel--mounted" : ""}`}>
      {/* Header */}
      <div className="exif-panel__header">
        <div className="exif-panel__title">
          <span className="exif-panel__menu">☰</span>
          EXIF Metadata
        </div>
        <div className="exif-panel__header-right">
          <span className="exif-panel__status">Master Fecties</span>
          <span className="exif-panel__badge">ASSTRENST ▾</span>
        </div>
      </div>

      <div className="exif-panel__body">
        {/* Left - Face scan canvas */}
        <div className="exif-panel__scan">
          <div className="exif-panel__scan-header">
            <span className="exif-panel__scan-dot" />
            ENFF DFCP metedies analyins
          </div>
          <canvas ref={canvasRef} className="exif-panel__canvas" />
          <div className="exif-panel__scan-footer">
            <span>6AT</span>
            <span>9:30</span>
            <span>A89M</span>
            <span>1 2 3 4 1 0 0 B</span>
          </div>
        </div>

        {/* Right - EXIF tags */}
        <div className="exif-panel__tags">
          <div className="exif-panel__tags-header">
            <span>EXIFERCUNCIUPS</span>
            <span className="exif-panel__tags-count">{exifTags.length}</span>
          </div>
          <div className="exif-panel__tags-list">
            {exifTags.map((tag, i) => (
              <div
                key={i}
                className={`exif-panel__tag ${tag.flagged ? "exif-panel__tag--flagged" : ""}`}
                style={{ animationDelay: `${i * 0.04}s` }}
              >
                <span className="exif-panel__tag-line">{tag.line}</span>
                <span className="exif-panel__tag-text">{tag.text}</span>
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
              <div className="exif-panel__stat-vals">
                {s.values.map((v) => (
                  <span key={v} className="exif-panel__stat-val">{v}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
        <div className="exif-panel__stats-center">
          <div className="exif-panel__tamper-badge">
            <div className="exif-panel__tamper-title">Tampered</div>
            <div className="exif-panel__tamper-value">
              {isTampered ? "Calibrated" : "Normal"}
            </div>
            {isTampered && (
              <div className="exif-panel__tamper-bar">
                <div className="exif-panel__tamper-fill" />
              </div>
            )}
          </div>
        </div>
        <div className="exif-panel__stats-right">
          <div className="exif-panel__version">Lack 1</div>
          <div className="exif-panel__version">Correct</div>
        </div>
      </div>
    </div>
  );
}
