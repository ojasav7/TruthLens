import { useEffect, useState } from "react";
import { API_URL } from "../lib/utils";

export default function Header() {
  const [status, setStatus] = useState<"live" | "down">("down");

  useEffect(() => {
    fetch(`${API_URL}/health`, { signal: AbortSignal.timeout(3000) })
      .then((r) => (r.ok ? setStatus("live") : setStatus("down")))
      .catch(() => setStatus("down"));
  }, []);

  return (
    <header className="flex items-center justify-between px-6 py-3 border-b border-border-default">
      <div className="flex items-center gap-3">
        <span className="text-2xl">🔍</span>
        <span className="text-lg font-bold tracking-widest text-text-primary">
          TRUTHLENS
        </span>
        <span className="px-2 py-0.5 text-xs font-medium text-cyan bg-cyan-glow border border-cyan/30 rounded-full">
          v2.0.0
        </span>
      </div>
      <div className="flex items-center gap-5">
        <span
          className={`flex items-center gap-2 text-sm font-medium ${
            status === "live" ? "text-emerald" : "text-crimson"
          }`}
        >
          <span
            className={`w-2 h-2 rounded-full ${
              status === "live"
                ? "bg-emerald shadow-[0_0_8px_var(--color-emerald)]"
                : "bg-crimson shadow-[0_0_8px_var(--color-crimson)]"
            }`}
          />
          {status === "live" ? "LIVE" : "DOWN"}
        </span>
        <a
          href={`${API_URL}/docs`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm font-medium text-cyan hover:text-cyan-hover transition-colors"
        >
          API Docs ↗
        </a>
      </div>
    </header>
  );
}
