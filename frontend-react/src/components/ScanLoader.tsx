import "./ScanLoader.css";

interface LoaderProps {
  size?: number;
  text?: string;
}

export default function ScanLoader({ size = 180, text = "Analyzing" }: LoaderProps) {
  const letters = text.split("");

  return (
    <div className="scan-loader-overlay">
      <div
        className="scan-loader-container"
        style={{ width: size, height: size }}
      >
        {letters.map((letter, index) => (
          <span
            key={index}
            className="scan-loader-letter"
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            {letter}
          </span>
        ))}

        <div className="scan-loader-circle" />
      </div>
    </div>
  );
}
