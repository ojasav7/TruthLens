export default function DangerZoneCard() {
  return (
    <div className="bg-card border border-destructive/30 p-8">
      <div className="font-mono text-[10px] text-destructive uppercase tracking-widest mb-6">
        Danger Zone
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-bold">Export All Data</div>
            <div className="text-xs text-muted-foreground mt-1">
              Download all your analysis results and history
            </div>
          </div>
          <button className="px-4 py-2 border border-destructive text-destructive text-xs font-bold uppercase tracking-widest hover:bg-destructive/10 transition-colors cursor-pointer">
            Export
          </button>
        </div>

        <div className="h-px bg-border" />

        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-bold">Revoke All API Keys</div>
            <div className="text-xs text-muted-foreground mt-1">
              Invalidate all API keys immediately
            </div>
          </div>
          <button className="px-4 py-2 border border-destructive text-destructive text-xs font-bold uppercase tracking-widest hover:bg-destructive/10 transition-colors cursor-pointer">
            Revoke
          </button>
        </div>

        <div className="h-px bg-border" />

        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-bold">Delete Account</div>
            <div className="text-xs text-muted-foreground mt-1">
              Permanently delete your account and all data
            </div>
          </div>
          <button className="px-4 py-2 bg-destructive text-destructive-foreground text-xs font-bold uppercase tracking-widest hover:brightness-110 transition-all cursor-pointer">
            Delete Account
          </button>
        </div>
      </div>
    </div>
  );
}
