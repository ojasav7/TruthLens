import { useState } from "react";
import ToggleSwitch from "./ToggleSwitch";
import { DISPLAY_OPTIONS, DISPLAY_TOGGLES } from "../../data/settingsData";

interface DisplayCardProps {
  onChange: () => void;
}

export default function DisplayCard({ onChange }: Readonly<DisplayCardProps>) {
  const [theme, setTheme] = useState("dark");
  const [toggles, setToggles] = useState<Record<string, boolean>>(
    Object.fromEntries(DISPLAY_TOGGLES.map((t) => [t.id, t.default]))
  );

  const handleToggle = (id: string) => {
    setToggles((prev) => ({ ...prev, [id]: !prev[id] }));
    onChange();
  };

  return (
    <div className="bg-card border border-border p-8">
      <div className="font-mono text-[10px] text-primary uppercase tracking-widest mb-6">
        Display
      </div>

      <div className="space-y-6">
        {/* Theme Selector */}
        <div>
          <label className="block text-sm font-bold mb-3">Theme</label>
          <div className="flex gap-2">
            {DISPLAY_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => { setTheme(opt.value); onChange(); }}
                className={`px-4 py-2 text-xs font-bold uppercase tracking-widest border transition-colors cursor-pointer ${
                  theme === opt.value
                    ? "bg-primary text-primary-foreground border-primary"
                    : "bg-secondary text-muted-foreground border-border hover:border-primary/30"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div className="h-px bg-border" />

        {/* Toggle Switches */}
        {DISPLAY_TOGGLES.map((toggle) => (
          <ToggleSwitch
            key={toggle.id}
            label={toggle.label}
            description={toggle.description}
            checked={toggles[toggle.id]}
            onChange={() => handleToggle(toggle.id)}
          />
        ))}
      </div>
    </div>
  );
}
