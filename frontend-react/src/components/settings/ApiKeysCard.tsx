import { useState } from "react";
import { Copy, RefreshCw } from "lucide-react";
import { API_KEYS } from "../../data/settingsData";

interface ApiKeysCardProps {
  onChange: () => void;
}

export default function ApiKeysCard({ onChange }: Readonly<ApiKeysCardProps>) {
  const [copied, setCopied] = useState<string | null>(null);

  const handleCopy = (id: string) => {
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div className="bg-card border border-border p-8">
      <div className="font-mono text-[10px] text-primary uppercase tracking-widest mb-6">
        API Keys
      </div>

      <div className="space-y-4">
        {API_KEYS.map((key) => (
          <div key={key.id}>
            <label className="block font-mono text-[10px] text-muted-foreground uppercase tracking-widest mb-2">
              {key.label}
            </label>
            <div className="flex items-center gap-2">
              <div className="flex-1 flex items-center bg-secondary border border-border px-4 py-3">
                <span className="flex-1 text-sm font-mono text-muted-foreground">
                  {key.configured ? "••••••••••••••••" : key.placeholder}
                </span>
                <div className="flex items-center gap-1 ml-2">
                  <span
                    className={`w-2 h-2 rounded-full ${
                      key.configured ? "bg-primary" : "bg-muted-foreground"
                    }`}
                  />
                </div>
              </div>
              {key.configured && (
                <>
                  <button
                    onClick={() => handleCopy(key.id)}
                    className="p-3 bg-secondary border border-border hover:border-primary/30 transition-colors cursor-pointer"
                    aria-label={`Copy ${key.label}`}
                  >
                    <Copy className="size-4" />
                  </button>
                  <button
                    onClick={onChange}
                    className="p-3 bg-secondary border border-border hover:border-primary/30 transition-colors cursor-pointer"
                    aria-label={`Regenerate ${key.label}`}
                  >
                    <RefreshCw className="size-4" />
                  </button>
                </>
              )}
            </div>
            {copied === key.id && (
              <div className="text-[10px] text-primary mt-1 font-mono uppercase tracking-widest">
                Copied!
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
