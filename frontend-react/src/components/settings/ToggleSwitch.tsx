interface ToggleSwitchProps {
  label: string;
  description: string;
  checked: boolean;
  onChange: () => void;
  locked?: boolean;
}

export default function ToggleSwitch({
  label,
  description,
  checked,
  onChange,
  locked,
}: Readonly<ToggleSwitchProps>) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <div className="text-sm font-bold">{label}</div>
        <div className="text-xs text-muted-foreground mt-1">{description}</div>
      </div>
      <button
        role="switch"
        aria-checked={checked}
        disabled={locked}
        onClick={onChange}
        className={`relative w-11 h-6 rounded-full transition-colors cursor-pointer ${
          checked ? "bg-primary" : "bg-border"
        } ${locked ? "opacity-50 cursor-not-allowed" : ""}`}
      >
        <span
          className={`absolute top-0.5 left-0.5 w-5 h-5 bg-foreground rounded-full transition-transform ${
            checked ? "translate-x-5" : ""
          }`}
        />
      </button>
    </div>
  );
}
