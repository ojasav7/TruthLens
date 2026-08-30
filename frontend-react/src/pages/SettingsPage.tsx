import { useState } from "react";
import Header from "../components/Header";
import AccountCard from "../components/settings/AccountCard";
import ApiKeysCard from "../components/settings/ApiKeysCard";
import SecurityCard from "../components/settings/SecurityCard";
import DisplayCard from "../components/settings/DisplayCard";
import NotificationsCard from "../components/settings/NotificationsCard";
import AnalysisDefaultsCard from "../components/settings/AnalysisDefaultsCard";
import DangerZoneCard from "../components/settings/DangerZoneCard";
import SettingsFooter from "../components/settings/SettingsFooter";

export default function SettingsPage() {
  const [dirty, setDirty] = useState(false);

  const markDirty = () => setDirty(true);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header backendStatus="live" />
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Page Title */}
        <div className="mb-10">
          <h1 className="text-4xl font-extrabold tracking-tighter uppercase mb-2">
            Settings
          </h1>
          <p className="text-muted-foreground">
            Configure your forensic analysis instance
          </p>
          <div className="h-px bg-border mt-6" />
        </div>

        {/* Settings Grid */}
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Column — Account & Security */}
          <div className="space-y-8">
            <AccountCard onChange={markDirty} />
            <ApiKeysCard onChange={markDirty} />
            <SecurityCard onChange={markDirty} />
          </div>

          {/* Right Column — Preferences */}
          <div className="space-y-8">
            <DisplayCard onChange={markDirty} />
            <NotificationsCard onChange={markDirty} />
            <AnalysisDefaultsCard onChange={markDirty} />
          </div>
        </div>

        {/* Danger Zone */}
        <div className="mt-12">
          <DangerZoneCard />
        </div>
      </div>

      {/* Footer */}
      <SettingsFooter
        dirty={dirty}
        onSave={() => setDirty(false)}
        onReset={() => setDirty(false)}
      />
    </div>
  );
}
