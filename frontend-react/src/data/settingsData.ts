export interface SettingOption {
  label: string;
  value: string;
}

export interface SettingToggle {
  id: string;
  label: string;
  description: string;
  default: boolean;
  locked?: boolean;
}

export interface ApiKeyField {
  id: string;
  label: string;
  placeholder: string;
  configured: boolean;
}

export const DISPLAY_OPTIONS: SettingOption[] = [
  { label: "Dark", value: "dark" },
  { label: "Light", value: "light" },
  { label: "System", value: "system" },
];

export const TIMEOUT_OPTIONS: SettingOption[] = [
  { label: "15 minutes", value: "15" },
  { label: "30 minutes", value: "30" },
  { label: "1 hour", value: "60" },
  { label: "4 hours", value: "240" },
];

export const MODALITY_OPTIONS: SettingOption[] = [
  { label: "Auto-detect", value: "auto" },
  { label: "Text", value: "text" },
  { label: "Image", value: "image" },
  { label: "Video", value: "video" },
  { label: "Audio", value: "audio" },
];

export const RETENTION_OPTIONS: SettingOption[] = [
  { label: "30 days", value: "30" },
  { label: "90 days", value: "90" },
  { label: "1 year", value: "365" },
  { label: "Forever", value: "forever" },
];

export const NOTIFICATION_TOGGLES: SettingToggle[] = [
  { id: "email_alerts", label: "Email Alerts", description: "Receive analysis results via email", default: false },
  { id: "browser_notifs", label: "Browser Notifications", description: "Get notified in your browser", default: false },
  { id: "analysis_complete", label: "Analysis Complete", description: "Notify when analysis finishes", default: true },
  { id: "high_risk", label: "High Risk Detected", description: "Alert on high-risk content", default: true, locked: true },
  { id: "weekly_report", label: "Weekly Report", description: "Summary of weekly analyses", default: false },
];

export const DISPLAY_TOGGLES: SettingToggle[] = [
  { id: "compact_mode", label: "Compact Mode", description: "Reduce spacing for denser layout", default: false },
  { id: "show_confidence", label: "Show Confidence Scores", description: "Display percentage confidence on results", default: true },
  { id: "animate_results", label: "Animate Results", description: "Enable result panel animations", default: true },
];

export const ANALYSIS_TOGGLES: SettingToggle[] = [
  { id: "auto_analyze", label: "Auto-analyze on Upload", description: "Start analysis immediately when file is uploaded", default: true },
  { id: "save_history", label: "Save to History", description: "Keep a record of all analyses", default: true },
];

export const API_KEYS: ApiKeyField[] = [
  { id: "truthlens", label: "TruthLens API Key", placeholder: "tl_", configured: true },
  { id: "telegram", label: "Telegram Bot Token", placeholder: "Not configured", configured: false },
  { id: "discord", label: "Discord Webhook URL", placeholder: "Not configured", configured: false },
];
