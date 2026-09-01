import { useEffect, useRef, useState } from "react";

interface Sprite {
  src: string;
  x: number;
  y: number;
  w: number;
  h: number;
}

interface HeatmapMeta {
  w: number;
  h: number;
  green: Sprite[];
  orange: Sprite[];
  chev: Sprite[];
  prog: Sprite;
}

interface AnimatedHeatmapProps {
  className?: string;
  style?: React.CSSProperties;
}

export default function AnimatedHeatmap({
  className = "",
  style,
}: AnimatedHeatmapProps) {
  const stageRef = useRef<HTMLDivElement>(null);
  const [meta, setMeta] = useState<HeatmapMeta | null>(null);

  useEffect(() => {
    fetch("/heatmap/meta.json")
      .then((r) => r.json())
      .then(setMeta)
      .catch(console.error);
  }, []);

  useEffect(() => {
    const stage = stageRef.current;
    if (!stage) return;
    const fit = () => {
      const s = Math.min(
        window.innerWidth / 1024,
        window.innerHeight / 768
      );
      stage.style.transform = `scale(${s})`;
    };
    fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, []);

  return (
    <div
      className={`animated-heatmap-container ${className}`}
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        overflow: "hidden",
        background: "#000",
        ...style,
      }}
    >
      <div
        ref={stageRef}
        className="animated-heatmap-stage"
        style={{
          width: 1024,
          height: 768,
          transformOrigin: "center center",
          willChange: "transform",
        }}
      >
        <div
          className="animated-heatmap-frame"
          style={{
            position: "relative",
            width: 1024,
            height: 768,
            background: "#000",
            overflow: "hidden",
          }}
        >
          {/* Base plate image */}
          <img
            src="/heatmap/plate.png"
            alt="Deepfake scan heatmap"
            style={{
              position: "absolute",
              inset: 0,
              width: 1024,
              height: 768,
              display: "block",
              userSelect: "none",
            }}
          />

          {/* Green horizontal bars */}
          {meta?.green.map((o, i) => (
            <div
              key={`g-${i}`}
              className="hm-bar-g"
              style={{
                position: "absolute",
                left: o.x,
                top: o.y,
                width: o.w,
                height: o.h,
                overflow: "hidden",
                animationDelay: `${260 + i * 62}ms`,
              }}
            >
              <img
                src={`/heatmap/${o.src}`}
                width={o.w}
                height={o.h}
                alt=""
                style={{ position: "absolute", left: 0, top: 0 }}
              />
            </div>
          ))}

          {/* Orange vertical bars */}
          {meta?.orange.map((o, i) => (
            <div
              key={`o-${i}`}
              className="hm-bar-o"
              style={{
                position: "absolute",
                left: o.x,
                top: o.y,
                width: o.w,
                height: o.h,
                overflow: "hidden",
                animationDelay: `${620 + i * 130}ms`,
              }}
            >
              <img
                src={`/heatmap/${o.src}`}
                width={o.w}
                height={o.h}
                alt=""
                style={{ position: "absolute", left: 0, top: 0 }}
              />
              <div
                className="hm-pulse"
                style={{
                  position: "absolute",
                  inset: 0,
                  background: "rgba(255,129,2,1)",
                  mixBlendMode: "screen" as const,
                  animationDelay: `${i * 420}ms`,
                }}
              />
            </div>
          ))}

          {/* Progress bar */}
          {meta?.prog && (
            <div
              className="hm-bar-p"
              style={{
                position: "absolute",
                left: meta.prog.x,
                top: meta.prog.y,
                width: meta.prog.w,
                height: meta.prog.h,
                overflow: "hidden",
              }}
            >
              <img
                src={`/heatmap/${meta.prog.src}`}
                width={meta.prog.w}
                height={meta.prog.h}
                alt=""
                style={{ position: "absolute", left: 0, top: 0 }}
              />
            </div>
          )}

          {/* Chevrons */}
          {meta?.chev?.[0] && (
            <div
              className="hm-chev-l"
              style={{
                position: "absolute",
                left: meta.chev[0].x,
                top: meta.chev[0].y,
                width: meta.chev[0].w,
                height: meta.chev[0].h,
              }}
            >
              <img
                src={`/heatmap/${meta.chev[0].src}`}
                width={meta.chev[0].w}
                height={meta.chev[0].h}
                alt=""
              />
            </div>
          )}
          {meta?.chev?.[1] && (
            <div
              className="hm-chev-r"
              style={{
                position: "absolute",
                left: meta.chev[1].x,
                top: meta.chev[1].y,
                width: meta.chev[1].w,
                height: meta.chev[1].h,
              }}
            >
              <img
                src={`/heatmap/${meta.chev[1].src}`}
                width={meta.chev[1].w}
                height={meta.chev[1].h}
                alt=""
              />
            </div>
          )}

          {/* FX layers */}
          <div
            className="hm-halo"
            style={{
              position: "absolute",
              inset: "52px 47px 41px 52px",
              border: "1px solid rgba(56,180,150,.12)",
            }}
          />

          {/* Face panel FX */}
          <div
            className="hm-face"
            style={{
              position: "absolute",
              left: 340,
              top: 195,
              width: 362,
              height: 380,
              overflow: "hidden",
              pointerEvents: "none",
            }}
          >
            <div className="hm-heat" />
            <div className="hm-scanline" />
            <div className="hm-scanedge" />
            <div className="hm-ping" />
            <div className="hm-brk hm-tl" />
            <div className="hm-brk hm-tr" />
            <div className="hm-brk hm-bl" />
            <div className="hm-brk hm-br" />
          </div>

          <div className="hm-pill" />
          <div className="hm-legend">
            <i />
          </div>
          <div className="hm-flicker" />
        </div>
      </div>
    </div>
  );
}
