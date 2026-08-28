export default function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-8 text-center animate-fade-in-up">
      <div className="text-6xl mb-5 drop-shadow-[0_0_20px_rgba(6,182,212,0.3)]">
        🔍
      </div>
      <h2 className="text-2xl font-bold text-text-primary uppercase tracking-wider mb-2">
        Forensic Intelligence Dashboard
      </h2>
      <p className="text-base text-text-secondary max-w-md leading-relaxed">
        Paste text or upload media to start your first investigation. TruthLens
        analyzes across{" "}
        <span className="font-semibold text-cyan">NLP</span>,{" "}
        <span className="font-semibold text-cyan">Image</span>,{" "}
        <span className="font-semibold text-cyan">Video</span>, and{" "}
        <span className="font-semibold text-cyan">Audio</span> modalities.
      </p>

      <div className="grid grid-cols-3 gap-6 mt-12 w-full max-w-lg">
        <FeatureCard
          icon="🛡️"
          title="Security"
          desc="Upload sandbox, privacy mode, data retention"
        />
        <FeatureCard
          icon="📊"
          title="Operations"
          desc="System health, trace IDs, observability"
        />
        <FeatureCard
          icon="🔬"
          title="Research"
          desc="Red team, drift detection, model comparison"
        />
      </div>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  desc,
}: {
  icon: string;
  title: string;
  desc: string;
}) {
  return (
    <div className="flex flex-col items-center gap-2 p-4 bg-bg-surface border border-border-default rounded-xl hover:border-border-active transition-all">
      <span className="text-2xl">{icon}</span>
      <span className="text-sm font-semibold text-text-primary">{title}</span>
      <span className="text-xs text-text-tertiary text-center leading-snug">
        {desc}
      </span>
    </div>
  );
}
