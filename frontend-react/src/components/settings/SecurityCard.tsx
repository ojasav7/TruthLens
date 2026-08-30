import { useState } from "react";
import { TIMEOUT_OPTIONS } from "../../data/settingsData";

interface SecurityCardProps {
  onChange: () => void;
}

export default function SecurityCard({ onChange }: Readonly<SecurityCardProps>) {
  const [twoFactor, setTwoFactor] = useState(false);
  const [timeout, setTimeout_] = useState("30");

  return (
    <div className="bg-card border border-border p-8">
      <div className="font-mono text-[10px] text-primary uppercase tracking-widest mb-6">
        Security
      </div>

      <div className="space-y-6">
        {/* 2FA Toggle */}
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-bold">Two-Factor Authentication</div>
            <div className="text-xs text-muted-foreground mt-1">
              Add an extra layer of security to your account
            </div>
          </div>
          <button
            role="switch"
            aria-checked={twoFactor}
            onClick={() => { setTwoFactor(!twoFactor); onChange(); }}
            className={`relative w-11 h-6 rounded-full transition-colors cursor-pointer ${
              twoFactor ? "bg-primary" : "bg-border"
            }`}
          >
            <span
              className={`absolute top-0.5 left-0.5 w-5 h-5 bg-foreground rounded-full transition-transform ${
                twoFactor ? "translate-x-5" : ""
              }`}
            />
          </button>
        </div>

        <div className="h-px bg-border" />

        {/* Session Timeout */}
        <div>
          <label className="block text-sm font-bold mb-2">Session Timeout</label>
          <select
            value={timeout}
            onChange={(e) => { setTimeout_(e.target.value); onChange(); }}
            className="w-full bg-secondary border border-border px-4 py-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background"
          >
            {TIMEOUT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="h-px bg-border" />

        {/* Active Sessions */}
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-bold">Active Sessions</div>
            <div className="text-xs text-muted-foreground mt-1">
              3 devices currently signed in
            </div>
          </div>
          <button
            onClick={onChange}
            className="text-xs text-destructive hover:underline cursor-pointer"
          >
            Revoke All
          </button>
        </div>
      </div>
    </div>
  );
}
