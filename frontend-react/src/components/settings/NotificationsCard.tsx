import { useState } from "react";
import ToggleSwitch from "./ToggleSwitch";
import { NOTIFICATION_TOGGLES } from "../../data/settingsData";

interface NotificationsCardProps {
  onChange: () => void;
}

export default function NotificationsCard({ onChange }: Readonly<NotificationsCardProps>) {
  const [toggles, setToggles] = useState<Record<string, boolean>>(
    Object.fromEntries(NOTIFICATION_TOGGLES.map((t) => [t.id, t.default]))
  );

  const handleToggle = (id: string) => {
    setToggles((prev) => ({ ...prev, [id]: !prev[id] }));
    onChange();
  };

  return (
    <div className="bg-card border border-border p-8">
      <div className="font-mono text-[10px] text-primary uppercase tracking-widest mb-6">
        Notifications
      </div>

      <div className="space-y-6">
        {NOTIFICATION_TOGGLES.map((toggle) => (
          <div key={toggle.id}>
            <ToggleSwitch
              label={toggle.label}
              description={toggle.description}
              checked={toggles[toggle.id]}
              onChange={() => handleToggle(toggle.id)}
              locked={toggle.locked}
            />
            {toggle.id !== NOTIFICATION_TOGGLES[NOTIFICATION_TOGGLES.length - 1].id && (
              <div className="h-px bg-border mt-6" />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
