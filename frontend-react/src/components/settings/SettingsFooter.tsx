interface SettingsFooterProps {
  dirty: boolean;
  onSave: () => void;
  onReset: () => void;
}

export default function SettingsFooter({
  dirty,
  onSave,
  onReset,
}: Readonly<SettingsFooterProps>) {
  return (
    <div className="sticky bottom-0 border-t border-border bg-background/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        {/* Left — Unsaved indicator */}
        <div className="flex items-center gap-2">
          {dirty && (
            <>
              <span className="w-2 h-2 rounded-full bg-amber animate-pulse" />
              <span className="text-xs text-amber font-mono uppercase tracking-widest">
                Unsaved changes
              </span>
            </>
          )}
        </div>

        {/* Right — Actions */}
        <div className="flex items-center gap-4">
          <button
            onClick={onReset}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
          >
            Reset to Defaults
          </button>
          <button
            onClick={onSave}
            disabled={!dirty}
            className={`px-6 py-2 text-xs font-bold uppercase tracking-widest transition-all cursor-pointer ${
              dirty
                ? "bg-primary text-primary-foreground hover:brightness-110"
                : "bg-border text-muted-foreground cursor-not-allowed"
            }`}
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}
