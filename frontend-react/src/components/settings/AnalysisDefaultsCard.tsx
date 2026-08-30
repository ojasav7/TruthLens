import { useState } from "react";
import ToggleSwitch from "./ToggleSwitch";
import { MODALITY_OPTIONS, RETENTION_OPTIONS, ANALYSIS_TOGGLES } from "../../data/settingsData";

interface AnalysisDefaultsCardProps {
  onChange: () => void;
}

export default function AnalysisDefaultsCard({ onChange }: Readonly<AnalysisDefaultsCardProps>) {
  const [modality, setModality] = useState("auto");
  const [retention, setRetention] = useState("90");
  const [toggles, setToggles] = useState<Record<string, boolean>>(
    Object.fromEntries(ANALYSIS_TOGGLES.map((t) => [t.id, t.default]))
  );

  const handleToggle = (id: string) => {
    setToggles((prev) => ({ ...prev, [id]: !prev[id] }));
    onChange();
  };

  return (
    <div className="bg-card border border-border p-8">
      <div className="font-mono text-[10px] text-primary uppercase tracking-widest mb-6">
        Analysis Defaults
      </div>

      <div className="space-y-6">
        {/* Default Modality */}
        <div>
          <label className="block text-sm font-bold mb-2">Default Modality</label>
          <select
            value={modality}
            onChange={(e) => { setModality(e.target.value); onChange(); }}
            className="w-full bg-secondary border border-border px-4 py-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background"
          >
            {MODALITY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="h-px bg-border" />

        {/* Toggles */}
        {ANALYSIS_TOGGLES.map((toggle) => (
          <div key={toggle.id}>
            <ToggleSwitch
              label={toggle.label}
              description={toggle.description}
              checked={toggles[toggle.id]}
              onChange={() => handleToggle(toggle.id)}
            />
            <div className="h-px bg-border mt-6" />
          </div>
        ))}

        {/* Data Retention */}
        <div>
          <label className="block text-sm font-bold mb-2">Data Retention</label>
          <select
            value={retention}
            onChange={(e) => { setRetention(e.target.value); onChange(); }}
            className="w-full bg-secondary border border-border px-4 py-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background"
          >
            {RETENTION_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
