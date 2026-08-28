import { ExternalLink } from "lucide-react";
import { useNavigate } from "react-router-dom";

interface HeaderProps {
  backendStatus: "live" | "down" | "checking";
}

export default function Header({ backendStatus }: HeaderProps) {
  const navigate = useNavigate();

  return (
    <nav aria-label="Dashboard navigation" className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate("/")}
            className="flex items-center gap-2 cursor-pointer bg-transparent border-none p-0 focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background rounded"
            aria-label="Return to TruthLens landing page"
          >
            <div className="size-6 bg-primary rounded-sm" aria-hidden="true"></div>
            <span className="font-mono font-bold tracking-tighter text-lg uppercase text-foreground">
              TruthLens
            </span>
          </button>
          <span className="font-mono text-[10px] text-muted-foreground uppercase tracking-widest hidden sm:inline" aria-hidden="true">
            / Dashboard
          </span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2" role="status" aria-label={`Backend status: ${backendStatus === "live" ? "online" : backendStatus === "down" ? "offline" : "checking"}`}>
            <span
              className={`size-2 rounded-full ${
                backendStatus === "live"
                  ? "bg-primary animate-pulse"
                  : backendStatus === "down"
                  ? "bg-destructive"
                  : "bg-muted-foreground"
              }`}
              aria-hidden="true"
            />
            <span className="font-mono text-[10px] text-muted-foreground uppercase tracking-widest hidden sm:inline">
              {backendStatus === "live"
                ? "System Online"
                : backendStatus === "down"
                ? "Offline"
                : "Checking..."}
            </span>
          </div>
          <a
            href="http://127.0.0.1:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 font-mono text-[10px] text-muted-foreground uppercase tracking-widest hover:text-primary transition-colors no-underline focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background rounded"
            aria-label="Open API documentation in new tab"
          >
            <ExternalLink className="size-3" aria-hidden="true" />
            <span className="hidden sm:inline">API Docs</span>
          </a>
        </div>
      </div>
    </nav>
  );
}
