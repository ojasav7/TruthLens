import { useNavigate } from "react-router-dom";
import { useEffect, useRef } from "react";
import heroScan from "../assets/hero-scan.jpg";
import { useScrollReveal } from "../hooks/useScrollReveal";
import ScanVideo from "../components/scans/ScanVideo";
import ScanText from "../components/scans/ScanText";
import ScanProvenance from "../components/scans/ScanProvenance";
import ScanMetadata from "../components/scans/ScanMetadata";
import AnimatedHeatmap from "../components/AnimatedHeatmap";
import "../components/AnimatedHeatmap.css";
import ScanAudio from "../components/scans/ScanAudio";
import "../components/scans/ScanCards.css";

export default function LandingPage() {
  const navigate = useNavigate();
  const heroRef = useRef<HTMLDivElement>(null);

  // Keyboard shortcut: Enter on focused buttons (accessibility skill)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Enter" && document.activeElement instanceof HTMLButtonElement) {
        document.activeElement.click();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  const modalityRef = useScrollReveal();
  const intelligenceRef = useScrollReveal();
  const infraRef = useScrollReveal();
  const statsRef = useScrollReveal();
  const ctaRef = useScrollReveal();

  return (
    <div className="min-h-screen bg-background text-foreground font-sans selection:bg-primary/30">
      {/* Skip to main content link (accessibility skill) */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[100] focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:font-bold"
      >
        Skip to main content
      </a>

      {/* Navigation (semantic HTML per accessibility skill) */}
      <nav aria-label="Main navigation" className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <a href="/" className="flex items-center gap-2 no-underline" aria-label="TruthLens home">
              <div className="size-6 bg-primary rounded-sm" aria-hidden="true"></div>
              <span className="font-mono font-bold tracking-tighter text-lg uppercase text-foreground">
                TruthLens
              </span>
            </a>
          </div>
          <div className="hidden md:flex gap-8 text-sm font-medium text-muted-foreground" role="menubar">
            <a href="#protocols" role="menuitem" className="hover:text-primary transition-colors">
              Protocols
            </a>
            <a href="#intelligence" role="menuitem" className="hover:text-primary transition-colors">
              Intelligence
            </a>
            <a href="#infrastructure" role="menuitem" className="hover:text-primary transition-colors">
              Infrastructure
            </a>
          </div>
          <button
            onClick={() => navigate("/dashboard")}
            className="px-4 py-1.5 bg-foreground text-background text-xs font-bold uppercase tracking-widest hover:bg-primary transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            aria-label="Start a forensic scan — navigates to dashboard"
          >
            Start Scan
          </button>
        </div>
      </nav>

      <main id="main-content" className="relative">
        <div className="absolute inset-0 bg-dots pointer-events-none" aria-hidden="true"></div>

        {/* Hero Section */}
        <section ref={heroRef} className="relative pt-24 pb-32 overflow-hidden" aria-labelledby="hero-heading">
          <div className="max-w-7xl mx-auto px-6 grid lg:grid-cols-2 gap-16 items-center">
            <div style={{ animation: "fadeIn 0.6s cubic-bezier(0.16,1,0.3,1) both" }}>
              <div className="inline-flex items-center gap-2 px-2 py-1 bg-primary/10 border border-primary/20 rounded-sm mb-6" role="status" aria-label="System status: active version 4.0.2">
                <span className="size-1.5 rounded-full bg-primary animate-pulse" aria-hidden="true"></span>
                <span className="text-[10px] font-mono text-primary uppercase tracking-widest">
                  System Active: v4.0.2
                </span>
              </div>
              <h1 id="hero-heading" className="text-5xl sm:text-6xl md:text-7xl font-extrabold tracking-tighter text-balance leading-[0.9] mb-8">
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
                  className="px-8 py-4 bg-primary text-primary-foreground font-bold uppercase tracking-widest text-sm hover:brightness-110 transition-all cursor-pointer focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                  aria-label="Deploy your own TruthLens instance — opens dashboard"
                >
                  Deploy Instance
                </button>
                <a
                  href="http://127.0.0.1:8000/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-8 py-4 border border-border font-bold uppercase tracking-widest text-sm hover:bg-border transition-all inline-block text-foreground no-underline focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                  aria-label="Open API documentation in new tab"
                >
                  Documentation
                </a>
              </div>
            </div>

            {/* Hero Result Card / Scan Visualization */}
            <div className="relative" style={{ animation: "fadeIn 0.8s cubic-bezier(0.16,1,0.3,1) 0.2s both" }}>
              <div className="relative bg-background border border-border p-1 shadow-2xl shadow-primary/5">
                <div className="absolute -inset-4 border border-primary/10 -z-10" aria-hidden="true"></div>
                <div className="w-full aspect-[4/3] bg-muted overflow-hidden relative group">
                  <img
                    src={heroScan}
                    alt="Forensic scan visualization showing digital artifact detection on a face with threat score overlay"
                    className="w-full h-full object-cover"
                    loading="eager"
                    width="800"
                    height="600"
                  />
                  <div className="absolute inset-0 scan-line bg-gradient-to-b from-transparent via-primary/40 to-transparent h-1 w-full z-20" aria-hidden="true"></div>
                  <div className="absolute top-4 left-4 z-10 font-mono text-[10px] bg-background/60 p-2 backdrop-blur-sm border border-foreground/10" aria-hidden="true">
                    [ FRAME_ID: 0x82A1 ]<br />
                    [ LATENCY: 12ms ]
                  </div>
                </div>

                {/* Floating Result Badge */}
                <div
                  className="absolute -bottom-8 -right-4 sm:-right-8 w-60 sm:w-64 bg-background border border-primary p-5 sm:p-6 shadow-2xl"
                  style={{ animation: "slideUp 0.5s cubic-bezier(0.16,1,0.3,1) 0.8s both" }}
                  role="status"
                  aria-label="Sample threat score: 84.2 percent, verdict: High Risk Artifacts"
                >
                  <div className="flex justify-between items-start mb-4">
                    <span className="font-mono text-[10px] text-muted-foreground uppercase">
                      Threat Score
                    </span>
                    <span className="text-primary font-mono font-bold" style={{ fontVariantNumeric: "tabular-nums" }}>
                      84.2%
                    </span>
                  </div>
                  <div className="h-1.5 w-full bg-border rounded-full overflow-hidden mb-4" role="progressbar" aria-valuenow={84} aria-valuemin={0} aria-valuemax={100} aria-label="Threat score progress">
                    <div className="h-full bg-primary w-[84%]"></div>
                  </div>
                  <div className="text-xs font-bold uppercase tracking-wider text-primary">
                    Verdict: High Risk Artifacts
                  </div>
                  <div className="mt-4 pt-4 border-t border-border flex gap-2" aria-hidden="true">
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

        {/* Scan Gallery */}
        <section className="py-24 border-t border-border">
          <div className="max-w-7xl mx-auto px-6">
            <div className="flex flex-col md:flex-row justify-between items-end gap-8 mb-16">
              <h2 className="text-4xl font-extrabold tracking-tighter uppercase">
                Scan Capabilities
              </h2>
              <p className="max-w-xs text-sm text-muted-foreground font-mono uppercase leading-relaxed tracking-tighter">
                Real-time forensic analysis across every media vector.
              </p>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-px bg-border border border-border">
              <ScanVideo />
              <ScanText />
              <ScanProvenance />
              <ScanMetadata />
              <AnimatedHeatmap style={{ minHeight: 400 }} />
              <ScanAudio />
            </div>
          </div>
        </section>

        {/* Modality Grid */}
        <section ref={modalityRef} id="protocols" className="py-24 border-t border-border scroll-hidden" aria-labelledby="modality-heading">
          <div className="max-w-7xl mx-auto px-6">
            <div className="flex flex-col md:flex-row justify-between items-end gap-8 mb-16">
              <h2 id="modality-heading" className="text-4xl font-extrabold tracking-tighter uppercase">
                Modality Coverage
              </h2>
              <p className="max-w-xs text-sm text-muted-foreground font-mono uppercase leading-relaxed tracking-tighter">
                Complete heuristic and neural coverage for every vector of
                disinformation.
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-px bg-border border border-border" role="list">
              {[
                { num: "01", title: "NLP Semantic Analysis", desc: "BERT-driven classification of fake news, bias detection, and cross-source verification." },
                { num: "02", title: "Diffusion Forensics", desc: "CNN detection of GAN and Stable Diffusion artifacts in sub-frame level." },
                { num: "03", title: "Temporal Deepfake", desc: "MobileNetV2 + LSTM consistency checks revealing unnatural frame transitions and lip-sync errors." },
                { num: "04", title: "Voice Clone ID", desc: "1D-CNN raw waveform analysis to identify frequency anomalies in AI-generated voice." },
              ].map((item, i) => (
                <div key={item.num} className="bg-background p-8 group hover:bg-primary/5 transition-colors scroll-hidden-stagger" role="listitem" style={{ transitionDelay: `${i * 0.08}s` }}>
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

        {/* Intelligence Section */}
        <section ref={intelligenceRef} id="intelligence" className="py-24 border-t border-border scroll-hidden" aria-labelledby="intelligence-heading">
          <div className="max-w-7xl mx-auto px-6">
            <div className="flex flex-col md:flex-row justify-between items-end gap-8 mb-16">
              <h2 id="intelligence-heading" className="text-4xl font-extrabold tracking-tighter uppercase">
                Intelligence Layer
              </h2>
              <p className="max-w-xs text-sm text-muted-foreground font-mono uppercase leading-relaxed tracking-tighter">
                Beyond detection — investigation, evidence, and provenance.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-px bg-border border border-border" role="list">
              {[
                { num: "05", title: "Evidence Ledger", desc: "Cryptographic chain of custody for every analysis. Tamper-proof audit trail with timestamped hashing." },
                { num: "06", title: "Provenance Tracking", desc: "C2PA content credentials, EXIF forensics, and source credibility scoring for media lineage." },
                { num: "07", title: "Contradiction Engine", desc: "Cross-reference claims against verified fact-checks and detect internal inconsistencies." },
                { num: "08", title: "Red Team Lab", desc: "Adversarial robustness testing — apply jitter, compression, noise, and re-encode to stress-test models." },
                { num: "09", title: "Drift Monitor", desc: "Real-time model performance tracking with automatic alerts on accuracy degradation." },
                { num: "10", title: "Case Management", desc: "Organize investigations into cases with timeline views, reviewer assignment, and status tracking." },
              ].map((item, i) => (
                <div key={item.num} className="bg-background p-8 group hover:bg-primary/5 transition-colors scroll-hidden-stagger" role="listitem" style={{ transitionDelay: `${i * 0.08}s` }}>
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
        <section ref={infraRef} id="infrastructure" className="py-24 border-t border-border scroll-hidden" aria-labelledby="infra-heading">
          <div className="max-w-7xl mx-auto px-6">
            <div className="flex flex-col md:flex-row justify-between items-end gap-8 mb-16">
              <h2 id="infra-heading" className="text-4xl font-extrabold tracking-tighter uppercase">
                Infrastructure
              </h2>
              <p className="max-w-xs text-sm text-muted-foreground font-mono uppercase leading-relaxed tracking-tighter">
                Production-grade security, observability, and deployment.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-6">
              {[
                { icon: "shield", title: "Secure Sandbox", items: ["Upload validation", "MIME + magic bytes", "Privacy mode", "Data retention policies"] },
                { icon: "chart", title: "Observability", items: ["Prometheus metrics", "Trace IDs per analysis", "System health checks", "Performance monitoring"] },
                { icon: "rocket", title: "Deployment", items: ["Docker ready", "Kubernetes manifests", "Chrome extension", "Telegram / Slack / Discord bots"] },
              ].map((card, i) => (
                <article key={card.title} className="bg-background border border-border p-8 hover:border-primary/30 transition-colors scroll-hidden-stagger" style={{ transitionDelay: `${i * 0.12}s` }}>
                  <div className="text-3xl mb-4" aria-hidden="true">
                    {card.icon === "shield" && "🛡"}
                    {card.icon === "chart" && "📊"}
                    {card.icon === "rocket" && "🚀"}
                  </div>
                  <h3 className="text-xl font-bold mb-4 uppercase">{card.title}</h3>
                  <ul className="space-y-2">
                    {card.items.map((item) => (
                      <li key={item} className="flex items-center gap-2 text-sm text-muted-foreground">
                        <span className="size-1 bg-primary rounded-full shrink-0" aria-hidden="true"></span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* Data Readout / Trust */}
        <section ref={statsRef} className="py-24 bg-foreground text-background scroll-hidden" aria-label="Platform statistics">
          <div className="max-w-7xl mx-auto px-6 grid md:grid-cols-3 gap-12">
            <div>
              <div className="text-5xl font-extrabold tracking-tighter mb-2" style={{ fontVariantNumeric: "tabular-nums" }}>
                95%+
              </div>
              <div className="font-mono text-[10px] uppercase tracking-widest opacity-60">
                Image Detection Accuracy
              </div>
            </div>
            <div>
              <div className="text-5xl font-extrabold tracking-tighter mb-2" style={{ fontVariantNumeric: "tabular-nums" }}>
                100%
              </div>
              <div className="font-mono text-[10px] uppercase tracking-widest opacity-60">
                Audio / Video Accuracy
              </div>
            </div>
            <div>
              <div className="text-5xl font-extrabold tracking-tighter mb-2" style={{ fontVariantNumeric: "tabular-nums" }}>
                240
              </div>
              <div className="font-mono text-[10px] uppercase tracking-widest opacity-60">
                Automated Tests Passing
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section ref={ctaRef} className="py-24 border-t border-border scroll-hidden" aria-labelledby="cta-heading">
          <div className="max-w-7xl mx-auto px-6 text-center">
            <h2 id="cta-heading" className="text-4xl md:text-5xl font-extrabold tracking-tighter uppercase mb-6">
              Ready to Scan?
            </h2>
            <p className="max-w-lg mx-auto text-muted-foreground mb-10">
              Deploy your own TruthLens instance or try the live demo to see
              multimodal forensic analysis in action.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <button
                onClick={() => navigate("/dashboard")}
                className="px-8 py-4 bg-primary text-primary-foreground font-bold uppercase tracking-widest text-sm hover:brightness-110 transition-all cursor-pointer focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                aria-label="Launch the TruthLens analysis dashboard"
              >
                Launch Dashboard
              </button>
              <a
                href="http://127.0.0.1:8000/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="px-8 py-4 border border-border font-bold uppercase tracking-widest text-sm hover:bg-border transition-all inline-block text-foreground no-underline focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                aria-label="Open API reference documentation in new tab"
              >
                API Reference
              </a>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-border py-12" role="contentinfo">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-2 grayscale">
            <div className="size-4 bg-foreground rounded-sm" aria-hidden="true"></div>
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
