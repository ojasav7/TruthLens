import { useNavigate } from "react-router-dom";
import heroScan from "../assets/hero-scan.jpg";

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background text-foreground font-sans selection:bg-primary/30">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="size-6 bg-primary rounded-sm"></div>
            <span className="font-mono font-bold tracking-tighter text-lg uppercase">
              TruthLens
            </span>
          </div>
          <div className="hidden md:flex gap-8 text-sm font-medium text-muted-foreground">
            <a href="#protocols" className="hover:text-primary transition-colors">
              Protocols
            </a>
            <a href="#intelligence" className="hover:text-primary transition-colors">
              Intelligence
            </a>
            <a href="#infrastructure" className="hover:text-primary transition-colors">
              Infrastructure
            </a>
          </div>
          <button
            onClick={() => navigate("/dashboard")}
            className="px-4 py-1.5 bg-foreground text-background text-xs font-bold uppercase tracking-widest hover:bg-primary transition-colors cursor-pointer"
          >
            Start Scan
          </button>
        </div>
      </nav>

      <main className="relative">
        <div className="absolute inset-0 bg-dots pointer-events-none"></div>

        {/* Hero Section */}
        <section className="relative pt-24 pb-32 overflow-hidden">
          <div className="max-w-7xl mx-auto px-6 grid lg:grid-cols-2 gap-16 items-center">
            <div style={{ animation: "fadeIn 0.6s cubic-bezier(0.16,1,0.3,1) both" }}>
              <div className="inline-flex items-center gap-2 px-2 py-1 bg-primary/10 border border-primary/20 rounded-sm mb-6">
                <span className="size-1.5 rounded-full bg-primary animate-pulse"></span>
                <span className="text-[10px] font-mono text-primary uppercase tracking-widest">
                  System Active: v4.0.2
                </span>
              </div>
              <h1 className="text-5xl sm:text-6xl md:text-7xl font-extrabold tracking-tighter text-balance leading-[0.9] mb-8">
                THE FORENSIC <span className="text-primary">STANDARD</span> FOR
                MEDIA AUTHENTICITY.
              </h1>
              <p className="max-w-md text-lg text-muted-foreground mb-10 text-pretty">
                Advanced multimodal threat detection for a post-truth era.
                Surface synthetic artifacts across text, image, and voice with
                sub-millisecond precision.
              </p>
              <div className="flex flex-wrap items-center gap-4">
                <button
                  onClick={() => navigate("/dashboard")}
                  className="px-8 py-4 bg-primary text-primary-foreground font-bold uppercase tracking-widest text-sm hover:brightness-110 transition-all cursor-pointer"
                >
                  Deploy Instance
                </button>
                <a
                  href="http://127.0.0.1:8000/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-8 py-4 border border-border font-bold uppercase tracking-widest text-sm hover:bg-border transition-all inline-block text-foreground no-underline"
                >
                  Documentation
                </a>
              </div>
            </div>

            {/* Hero Result Card / Scan Visualization */}
            <div className="relative" style={{ animation: "fadeIn 0.8s cubic-bezier(0.16,1,0.3,1) 0.2s both" }}>
              <div className="relative bg-background border border-border p-1 shadow-2xl shadow-primary/5">
                <div className="absolute -inset-4 border border-primary/10 -z-10"></div>
                <div className="w-full aspect-[4/3] bg-muted overflow-hidden relative group">
                  <img
                    src={heroScan}
                    alt="Forensic scan visualization showing digital artifacts on a face"
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 scan-line bg-gradient-to-b from-transparent via-primary/40 to-transparent h-1 w-full z-20"></div>
                  <div className="absolute top-4 left-4 z-10 font-mono text-[10px] bg-background/60 p-2 backdrop-blur-sm border border-foreground/10">
                    [ FRAME_ID: 0x82A1 ]<br />
                    [ LATENCY: 12ms ]
                  </div>
                </div>

                {/* Floating Result Badge */}
                <div className="absolute -bottom-8 -right-4 sm:-right-8 w-60 sm:w-64 bg-background border border-primary p-5 sm:p-6 shadow-2xl" style={{ animation: "slideUp 0.5s cubic-bezier(0.16,1,0.3,1) 0.8s both" }}>
                  <div className="flex justify-between items-start mb-4">
                    <span className="font-mono text-[10px] text-muted-foreground uppercase">
                      Threat Score
                    </span>
                    <span className="text-primary font-mono font-bold">
                      84.2%
                    </span>
                  </div>
                  <div className="h-1.5 w-full bg-border rounded-full overflow-hidden mb-4">
                    <div className="h-full bg-primary w-[84%]"></div>
                  </div>
                  <div className="text-xs font-bold uppercase tracking-wider text-primary">
                    Verdict: High Risk Artifacts
                  </div>
                  <div className="mt-4 pt-4 border-t border-border flex gap-2">
                    <div className="size-2 bg-primary"></div>
                    <div className="size-2 bg-primary"></div>
                    <div className="size-2 bg-primary"></div>
                    <div className="size-2 bg-border"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Modality Grid */}
        <section id="protocols" className="py-24 border-t border-border">
          <div className="max-w-7xl mx-auto px-6">
            <div className="flex flex-col md:flex-row justify-between items-end gap-8 mb-16">
              <h2 className="text-4xl font-extrabold tracking-tighter uppercase">
                Modality Coverage
              </h2>
              <p className="max-w-xs text-sm text-muted-foreground font-mono uppercase leading-relaxed tracking-tighter">
                Complete heuristic and neural coverage for every vector of
                disinformation.
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-px bg-border border border-border">
              <div className="bg-background p-8 group hover:bg-primary/5 transition-colors">
                <div className="font-mono text-[10px] text-primary mb-8 uppercase tracking-widest">
                  01 / Text
                </div>
                <h3 className="text-xl font-bold mb-4 uppercase">
                  NLP Semantic Analysis
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  BERT-driven classification of fake news, bias detection, and
                  cross-source verification.
                </p>
              </div>
              <div className="bg-background p-8 group hover:bg-primary/5 transition-colors">
                <div className="font-mono text-[10px] text-primary mb-8 uppercase tracking-widest">
                  02 / Image
                </div>
                <h3 className="text-xl font-bold mb-4 uppercase">
                  Diffusion Forensics
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  CNN detection of GAN and Stable Diffusion artifacts
                  in sub-frame level.
                </p>
              </div>
              <div className="bg-background p-8 group hover:bg-primary/5 transition-colors">
                <div className="font-mono text-[10px] text-primary mb-8 uppercase tracking-widest">
                  03 / Video
                </div>
                <h3 className="text-xl font-bold mb-4 uppercase">
                  Temporal Deepfake
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  MobileNetV2 + LSTM consistency checks revealing unnatural frame
                  transitions and lip-sync errors.
                </p>
              </div>
              <div className="bg-background p-8 group hover:bg-primary/5 transition-colors">
                <div className="font-mono text-[10px] text-primary mb-8 uppercase tracking-widest">
                  04 / Audio
                </div>
                <h3 className="text-xl font-bold mb-4 uppercase">
                  Voice Clone ID
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  1D-CNN raw waveform analysis to identify frequency anomalies in
                  AI-generated voice.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Intelligence Section */}
        <section id="intelligence" className="py-24 border-t border-border">
          <div className="max-w-7xl mx-auto px-6">
            <div className="flex flex-col md:flex-row justify-between items-end gap-8 mb-16">
              <h2 className="text-4xl font-extrabold tracking-tighter uppercase">
                Intelligence Layer
              </h2>
              <p className="max-w-xs text-sm text-muted-foreground font-mono uppercase leading-relaxed tracking-tighter">
                Beyond detection — investigation, evidence, and provenance.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-px bg-border border border-border">
              {[
                { num: "05", title: "Evidence Ledger", desc: "Cryptographic chain of custody for every analysis. Tamper-proof audit trail with timestamped hashing." },
                { num: "06", title: "Provenance Tracking", desc: "C2PA content credentials, EXIF forensics, and source credibility scoring for media lineage." },
                { num: "07", title: "Contradiction Engine", desc: "Cross-reference claims against verified fact-checks and detect internal inconsistencies." },
                { num: "08", title: "Red Team Lab", desc: "Adversarial robustness testing — apply jitter, compression, noise, and re-encode to stress-test models." },
                { num: "09", title: "Drift Monitor", desc: "Real-time model performance tracking with automatic alerts on accuracy degradation." },
                { num: "10", title: "Case Management", desc: "Organize investigations into cases with timeline views, reviewer assignment, and status tracking." },
              ].map((item) => (
                <div key={item.num} className="bg-background p-8 group hover:bg-primary/5 transition-colors">
                  <div className="font-mono text-[10px] text-primary mb-8 uppercase tracking-widest">
                    {item.num}
                  </div>
                  <h3 className="text-xl font-bold mb-4 uppercase">
                    {item.title}
                  </h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {item.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Infrastructure Section */}
        <section id="infrastructure" className="py-24 border-t border-border">
          <div className="max-w-7xl mx-auto px-6">
            <div className="flex flex-col md:flex-row justify-between items-end gap-8 mb-16">
              <h2 className="text-4xl font-extrabold tracking-tighter uppercase">
                Infrastructure
              </h2>
              <p className="max-w-xs text-sm text-muted-foreground font-mono uppercase leading-relaxed tracking-tighter">
                Production-grade security, observability, and deployment.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-6">
              {[
                { icon: "🛡", title: "Secure Sandbox", items: ["Upload validation", "MIME + magic bytes", "Privacy mode", "Data retention policies"] },
                { icon: "📊", title: "Observability", items: ["Prometheus metrics", "Trace IDs per analysis", "System health checks", "Performance monitoring"] },
                { icon: "🚀", title: "Deployment", items: ["Docker ready", "Kubernetes manifests", "Chrome extension", "Telegram / Slack / Discord bots"] },
              ].map((card) => (
                <div key={card.title} className="bg-background border border-border p-8 hover:border-primary/30 transition-colors">
                  <div className="text-3xl mb-4">{card.icon}</div>
                  <h3 className="text-xl font-bold mb-4 uppercase">{card.title}</h3>
                  <ul className="space-y-2">
                    {card.items.map((item) => (
                      <li key={item} className="flex items-center gap-2 text-sm text-muted-foreground">
                        <span className="size-1 bg-primary rounded-full shrink-0"></span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Data Readout / Trust */}
        <section className="py-24 bg-foreground text-background">
          <div className="max-w-7xl mx-auto px-6 grid md:grid-cols-3 gap-12">
            <div>
              <div className="text-5xl font-extrabold tracking-tighter mb-2">
                95%+
              </div>
              <div className="font-mono text-[10px] uppercase tracking-widest opacity-60">
                Image Detection Accuracy
              </div>
            </div>
            <div>
              <div className="text-5xl font-extrabold tracking-tighter mb-2">
                100%
              </div>
              <div className="font-mono text-[10px] uppercase tracking-widest opacity-60">
                Audio / Video Accuracy
              </div>
            </div>
            <div>
              <div className="text-5xl font-extrabold tracking-tighter mb-2">
                240
              </div>
              <div className="font-mono text-[10px] uppercase tracking-widest opacity-60">
                Automated Tests Passing
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-24 border-t border-border">
          <div className="max-w-7xl mx-auto px-6 text-center">
            <h2 className="text-4xl md:text-5xl font-extrabold tracking-tighter uppercase mb-6">
              Ready to Scan?
            </h2>
            <p className="max-w-lg mx-auto text-muted-foreground mb-10">
              Deploy your own TruthLens instance or try the live demo to see
              multimodal forensic analysis in action.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <button
                onClick={() => navigate("/dashboard")}
                className="px-8 py-4 bg-primary text-primary-foreground font-bold uppercase tracking-widest text-sm hover:brightness-110 transition-all cursor-pointer"
              >
                Launch Dashboard
              </button>
              <a
                href="http://127.0.0.1:8000/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="px-8 py-4 border border-border font-bold uppercase tracking-widest text-sm hover:bg-border transition-all inline-block text-foreground no-underline"
              >
                API Reference
              </a>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-border py-12">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-2 grayscale">
            <div className="size-4 bg-foreground rounded-sm"></div>
            <span className="font-mono font-bold tracking-tighter text-sm uppercase">
              TruthLens Ops
            </span>
          </div>
          <div className="font-mono text-[10px] text-muted-foreground uppercase tracking-widest">
            © 2026 TruthLens Systems — All Media Scanned
          </div>
        </div>
      </footer>
    </div>
  );
}
