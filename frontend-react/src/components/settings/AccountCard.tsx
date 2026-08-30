interface AccountCardProps {
  onChange: () => void;
}

export default function AccountCard({ onChange }: Readonly<AccountCardProps>) {
  return (
    <div className="bg-card border border-border p-8">
      <div className="font-mono text-[10px] text-primary uppercase tracking-widest mb-6">
        Account
      </div>

      {/* User Avatar */}
      <div className="flex items-center gap-4 mb-6">
        <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center text-primary-foreground font-bold text-lg">
          OT
        </div>
        <div>
          <div className="font-bold">Ojasav Thakur</div>
          <div className="text-sm text-muted-foreground">Owner</div>
        </div>
      </div>

      <div className="space-y-4">
        {/* Display Name */}
        <div>
          <label className="block font-mono text-[10px] text-muted-foreground uppercase tracking-widest mb-2">
            Display Name
          </label>
          <input
            type="text"
            defaultValue="Ojasav Thakur"
            onChange={onChange}
            className="w-full bg-secondary border border-border px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background"
          />
        </div>

        {/* Email */}
        <div>
          <label className="block font-mono text-[10px] text-muted-foreground uppercase tracking-widest mb-2">
            Email
          </label>
          <div className="flex items-center gap-2">
            <input
              type="email"
              defaultValue="ojasavthakur88@gmail.com"
              readOnly
              className="flex-1 bg-secondary border border-border px-4 py-3 text-sm text-muted-foreground"
            />
            <span className="px-2 py-1 bg-primary/10 text-primary text-[10px] font-mono uppercase tracking-widest">
              Verified
            </span>
          </div>
        </div>

        {/* Last Login */}
        <div className="font-mono text-[10px] text-muted-foreground uppercase tracking-widest pt-2">
          Last login: 2 hours ago
        </div>
      </div>
    </div>
  );
}
