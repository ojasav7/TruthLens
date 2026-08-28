import { Scan, FileText, Image as ImageIcon, Film, Mic, Shield } from "lucide-react";

export default function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-6" role="status" aria-label="No analysis running — select a modality and provide input to begin">
      <div className="relative mb-8">
        <div className="size-20 border border-border flex items-center justify-center bg-card">
          <Scan className="size-10 text-primary" aria-hidden="true" />
        </div>
        <div className="absolute -inset-3 border border-primary/10 -z-10" aria-hidden="true"></div>
      </div>

      <h2 className="text-2xl font-extrabold tracking-tighter uppercase text-center mb-3">
        No Analysis Running
      </h2>
      <p className="text-sm text-muted-foreground text-center max-w-md mb-10 leading-relaxed">
        Select a modality in the sidebar and provide input to begin a forensic
        scan. TruthLens will analyze the content across all available signals.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-border border border-border w-full max-w-2xl" role="list" aria-label="Available analysis modalities">
        {[
          { icon: FileText, label: "Text", desc: "NLP Classification" },
          { icon: ImageIcon, label: "Image", desc: "Deepfake Detection" },
          { icon: Film, label: "Video", desc: "Temporal Analysis" },
          { icon: Mic, label: "Audio", desc: "Voice Clone ID" },
        ].map(({ icon: Icon, label, desc }) => (
          <div key={label} className="bg-background p-6 text-center" role="listitem">
            <Icon className="size-6 text-primary mx-auto mb-3" aria-hidden="true" />
            <div className="font-mono text-[10px] text-primary uppercase tracking-widest mb-1">
              {label}
            </div>
            <div className="text-[11px] text-muted-foreground">{desc}</div>
          </div>
        ))}
      </div>

      <div className="mt-10 flex items-center gap-2 font-mono text-[10px] text-muted-foreground uppercase tracking-widest">
        <Shield className="size-3" aria-hidden="true" />
        All analysis runs in a secure sandbox
      </div>
    </div>
  );
}
