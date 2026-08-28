import { useState, useRef } from "react";
import {
  Type,
  Image as ImageIcon,
  Film,
  Mic,
  Upload,
  X,
} from "lucide-react";

interface InputPanelProps {
  onAnalyze: (data: {
    text?: string;
    image?: File;
    video?: File;
    audio?: File;
  }) => void;
  loading: boolean;
}

const tabs = [
  { id: "text", label: "Text", icon: Type },
  { id: "image", label: "Image", icon: ImageIcon },
  { id: "video", label: "Video", icon: Film },
  { id: "audio", label: "Audio", icon: Mic },
] as const;

type TabId = (typeof tabs)[number]["id"];

export default function InputPanel({ onAnalyze, loading }: InputPanelProps) {
  const [activeTab, setActiveTab] = useState<TabId>("text");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleSubmit = () => {
    if (activeTab === "text" && text.trim()) {
      onAnalyze({ text: text.trim() });
    } else if (file) {
      const key = activeTab as "image" | "video" | "audio";
      onAnalyze({ [key]: file });
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] || null;
    setFile(f);
  };

  const canSubmit =
    (activeTab === "text" && text.trim().length > 0) ||
    (activeTab !== "text" && file !== null);

  return (
    <div className="bg-card border border-border p-6">
      {/* Section Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="font-mono text-[10px] text-primary uppercase tracking-widest">
          Analysis Input
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-px bg-border border border-border mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => {
              setActiveTab(tab.id);
              setFile(null);
            }}
            className={`flex-1 flex items-center justify-center gap-2 px-3 py-2.5 font-mono text-[10px] uppercase tracking-widest transition-colors cursor-pointer border-none ${
              activeTab === tab.id
                ? "bg-primary text-primary-foreground"
                : "bg-background text-muted-foreground hover:bg-primary/5"
            }`}
          >
            <tab.icon className="size-3" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="mb-6">
        {activeTab === "text" && (
          <div>
            <label className="block font-mono text-[10px] text-muted-foreground uppercase tracking-widest mb-2">
              Text Content
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste suspicious text, news headline, or social media post..."
              className="w-full h-40 bg-background border border-border p-4 text-sm text-foreground placeholder:text-muted-foreground resize-none focus:border-primary focus:outline-none transition-colors font-sans"
            />
            <div className="flex justify-between mt-2">
              <span className="font-mono text-[10px] text-muted-foreground">
                {text.length} chars · {text.split(/\s+/).filter(Boolean).length} words
              </span>
              <span className="font-mono text-[10px] text-muted-foreground">
                Max 10,000
              </span>
            </div>
          </div>
        )}

        {activeTab !== "text" && (
          <div>
            <label className="block font-mono text-[10px] text-muted-foreground uppercase tracking-widest mb-2">
              {activeTab === "image" ? "Image File" : activeTab === "video" ? "Video File" : "Audio File"}
            </label>
            {file ? (
              <div className="flex items-center justify-between bg-background border border-primary p-4">
                <div className="flex items-center gap-3">
                  <div className="size-8 bg-primary/10 flex items-center justify-center">
                    {activeTab === "image" && <ImageIcon className="size-4 text-primary" />}
                    {activeTab === "video" && <Film className="size-4 text-primary" />}
                    {activeTab === "audio" && <Mic className="size-4 text-primary" />}
                  </div>
                  <div>
                    <div className="text-sm text-foreground font-medium truncate max-w-[200px]">
                      {file.name}
                    </div>
                    <div className="font-mono text-[10px] text-muted-foreground">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => setFile(null)}
                  className="p-1 text-muted-foreground hover:text-foreground transition-colors cursor-pointer bg-transparent border-none"
                >
                  <X className="size-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => fileRef.current?.click()}
                className="w-full h-32 border-2 border-dashed border-border hover:border-primary/50 flex flex-col items-center justify-center gap-3 transition-colors cursor-pointer bg-transparent"
              >
                <Upload className="size-6 text-muted-foreground" />
                <div className="text-sm text-muted-foreground">
                  Drop file or click to upload
                </div>
                <div className="font-mono text-[10px] text-muted-foreground">
                  {activeTab === "image"
                    ? "PNG, JPG, WebP — Max 20MB"
                    : activeTab === "video"
                    ? "MP4, MOV, AVI — Max 100MB"
                    : "WAV, MP3, FLAC — Max 50MB"}
                </div>
              </button>
            )}
            <input
              ref={fileRef}
              type="file"
              accept={
                activeTab === "image"
                  ? "image/*"
                  : activeTab === "video"
                  ? "video/*"
                  : "audio/*"
              }
              onChange={handleFileChange}
              className="hidden"
            />
          </div>
        )}
      </div>

      {/* Analyze Button */}
      <button
        onClick={handleSubmit}
        disabled={!canSubmit || loading}
        className={`w-full py-3 font-mono text-[10px] uppercase tracking-widest font-bold transition-all cursor-pointer border-none ${
          canSubmit && !loading
            ? "bg-primary text-primary-foreground hover:brightness-110"
            : "bg-muted text-muted-foreground cursor-not-allowed"
        }`}
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="size-3 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin"></span>
            Analyzing…
          </span>
        ) : (
          "Start Scan"
        )}
      </button>

      <div className="mt-3 text-center font-mono text-[10px] text-muted-foreground">
        Ctrl+Enter to trigger
      </div>
    </div>
  );
}
