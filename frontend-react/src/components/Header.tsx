import { Shield, ExternalLink } from "lucide-react";
import { useNavigate } from "react-router-dom";

interface HeaderProps {
  backendStatus: "live" | "down" | "checking";
}

export default function Header({ backendStatus }: HeaderProps) {
  const navigate = useNavigate();

  return (
    <nav className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate("/")}
            className="flex items-center gap-2 cursor-pointer bg-transparent border-none p-0"
          >
            <div className="size-6 bg-primary rounded-sm"></div>
            <span className="font-mono font-bold tracking-tighter text-lg uppercase text-foreground">
              TruthLens
            </span>
          </button>
          <span className="font-mono text-[10px] text-muted-foreground uppercase tracking-widest hidden sm:inline">
            / Dashboard
          </span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span
              className={`size-2 rounded-full ${
                backendStatus === "live"
                  ? "bg-primary animate-pulse"
                  : backendStatus === "down"
                  ? "bg-destructive"
                  : "bg-muted-foreground"
              }`}
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
            className="flex items-center gap-1 font-mono text-[10px] text-muted-foreground uppercase tracking-widest hover:text-primary transition-colors no-underline"
          >
            <ExternalLink className="size-3" />
            API Docs
          </a>
        </div>
      </div>
    </nav>
  );
}
