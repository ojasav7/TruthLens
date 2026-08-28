import { useState, useRef } from "react";
import {
  FileText,
  Image,
  Film,
  Music,
  Search,
} from "lucide-react";

interface InputPanelProps {
  onAnalyze: (data: {
    text?: string;
    image?: File;
    video?: File;
    audio?: File;
  }) => void;
  disabled?: boolean;
}

const tabs = [
  { id: "text", label: "Text", icon: FileText, emoji: "📝" },
  { id: "image", label: "Image", icon: Image, emoji: "🖼️" },
  { id: "video", label: "Video", icon: Film, emoji: "🎬" },
  { id: "audio", label: "Audio", icon: Music, emoji: "🔊" },
] as const;

type TabId = (typeof tabs)[number]["id"];

export default function InputPanel({ onAnalyze, disabled }: InputPanelProps) {
  const [activeTab, setActiveTab] = useState<TabId>("text");
  const [text, setText] = useState("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);

  const imageRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLInputElement>(null);
  const audioRef = useRef<HTMLInputElement>(null);

  const handleAnalyze = () => {
    const data: {
      text?: string;
      image?: File;
      video?: File;
      audio?: File;
    } = {};
    if (text.trim()) data.text = text.trim();
    if (imageFile) data.image = imageFile;
    if (videoFile) data.video = videoFile;
    if (audioFile) data.audio = audioFile;
    if (Object.keys(data).length > 0) onAnalyze(data);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      handleAnalyze();
    }
  };

  return (
    <aside
      className="w-80 shrink-0 bg-bg-surface border-r border-border-default p-5 flex flex-col gap-4"
      onKeyDown={handleKeyDown}
    >
      <h2 className="text-sm font-bold uppercase tracking-wider text-text-primary">
        📝 Analysis Input
      </h2>

      {/* Tabs */}
      <div className="flex gap-1.5">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-lg border transition-all ${
              activeTab === tab.id
                ? "bg-cyan-glow border-cyan text-cyan"
                : "bg-bg-surface border-border-default text-text-secondary hover:border-border-active hover:text-text-primary"
            }`}
          >
            {tab.emoji} {tab.label}
          </button>
        ))}
      </div>

      {/* Input Area */}
      <div className="flex-1">
        {activeTab === "text" && (
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste suspicious news, headline, or social media post…"
            className="w-full h-40 p-3 text-sm text-text-primary bg-bg-surface border border-border-default rounded-lg resize-none focus:border-cyan focus:ring-2 focus:ring-cyan-glow focus:outline-none placeholder:text-text-tertiary transition-all"
          />
        )}

        {activeTab === "image" && (
          <div
            onClick={() => imageRef.current?.click()}
            className="flex flex-col items-center justify-center h-40 border-2 border-dashed border-border-default rounded-xl cursor-pointer hover:border-cyan transition-colors"
          >
            <Image className="w-8 h-8 text-text-tertiary mb-2" />
            {imageFile ? (
              <span className="text-sm text-cyan font-medium">{imageFile.name}</span>
            ) : (
              <span className="text-sm text-text-tertiary">Click to upload image</span>
            )}
            <input
              ref={imageRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => setImageFile(e.target.files?.[0] || null)}
            />
          </div>
        )}

        {activeTab === "video" && (
          <div
            onClick={() => videoRef.current?.click()}
            className="flex flex-col items-center justify-center h-40 border-2 border-dashed border-border-default rounded-xl cursor-pointer hover:border-cyan transition-colors"
          >
            <Film className="w-8 h-8 text-text-tertiary mb-2" />
            {videoFile ? (
              <span className="text-sm text-cyan font-medium">{videoFile.name}</span>
            ) : (
              <span className="text-sm text-text-tertiary">Click to upload video</span>
            )}
            <input
              ref={videoRef}
              type="file"
              accept="video/*"
              className="hidden"
              onChange={(e) => setVideoFile(e.target.files?.[0] || null)}
            />
          </div>
        )}

        {activeTab === "audio" && (
          <div
            onClick={() => audioRef.current?.click()}
            className="flex flex-col items-center justify-center h-40 border-2 border-dashed border-border-default rounded-xl cursor-pointer hover:border-cyan transition-colors"
          >
            <Music className="w-8 h-8 text-text-tertiary mb-2" />
            {audioFile ? (
              <span className="text-sm text-cyan font-medium">{audioFile.name}</span>
            ) : (
              <span className="text-sm text-text-tertiary">Click to upload audio</span>
            )}
            <input
              ref={audioRef}
              type="file"
              accept="audio/*"
              className="hidden"
              onChange={(e) => setAudioFile(e.target.files?.[0] || null)}
            />
          </div>
        )}
      </div>

      {activeTab === "text" && text && (
        <p className="text-xs text-text-tertiary" style={{ fontVariantNumeric: "tabular-nums" }}>
          📊 {text.length} characters · {text.split(/\s+/).filter(Boolean).length} words
        </p>
      )}

      <div className="border-t border-border-default" />

      {/* Analyze Button */}
      <button
        onClick={handleAnalyze}
        disabled={disabled}
        className="flex items-center justify-center gap-2 w-full py-3 text-sm font-bold text-white bg-cyan rounded-lg hover:bg-cyan-hover active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Search className="w-4 h-4" />
        Analyze
      </button>
      <p className="text-xs text-text-tertiary text-center">⌨️ Ctrl+Enter to analyze</p>
    </aside>
  );
}
