import { useState, useRef, useEffect } from "react";
import "./ReaderView.css";

export interface Paragraph {
  id: string;
  text: string;
}

export interface ReaderViewProps {
  paragraphs: Paragraph[];
  title?: string;
  onSelectParagraph?: (id: string) => void;
  selectedId?: string | null;
}

export default function ReaderView({
  paragraphs,
  title,
  onSelectParagraph,
  selectedId = null,
}: ReaderViewProps) {
  const [activeId, setActiveId] = useState<string | null>(selectedId);
  const [progress, setProgress] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Sync external selectedId
  useEffect(() => {
    setActiveId(selectedId);
  }, [selectedId]);

  // Track read progress
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const onScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = el;
      const max = scrollHeight - clientHeight;
      setProgress(max > 0 ? Math.round((scrollTop / max) * 100) : 0);
    };
    el.addEventListener("scroll", onScroll, { passive: true });
    return () => el.removeEventListener("scroll", onScroll);
  }, []);

  const handleClick = (id: string) => {
    setActiveId(id);
    onSelectParagraph?.(id);
  };

  return (
    <div className="rv-shell">
      {/* Progress bar */}
      <div className="rv-progress-track">
        <div className="rv-progress-fill" style={{ width: `${progress}%` }} />
      </div>

      {/* Header */}
      {title && (
        <header className="rv-header">
          <span className="rv-header-label">ĐANG ĐỌC</span>
          <h1 className="rv-title">{title}</h1>
          <span className="rv-meta">{paragraphs.length} đoạn</span>
        </header>
      )}

      {/* Scrollable body */}
      <div className="rv-scroll" ref={scrollRef}>
        <div className="rv-page">
          {paragraphs.map((p, index) => (
            <ParagraphBlock
              key={p.id}
              paragraph={p}
              index={index}
              isActive={activeId === p.id}
              onClick={handleClick}
            />
          ))}

          {paragraphs.length === 0 && (
            <div className="rv-empty">
              <span className="rv-empty-icon">📖</span>
              <p>Chưa có nội dung để hiển thị</p>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="rv-footer">
        <span className="rv-progress-text">{progress}%</span>
        {activeId && (
          <span className="rv-selected-label">
            Đoạn <strong>{activeId}</strong> đang chọn
          </span>
        )}
      </footer>
    </div>
  );
}

// ── ParagraphBlock ──────────────────────────────────────────

interface ParagraphBlockProps {
  paragraph: Paragraph;
  index: number;
  isActive: boolean;
  onClick: (id: string) => void;
}

function ParagraphBlock({ paragraph, index, isActive, onClick }: ParagraphBlockProps) {
  const ref = useRef<HTMLDivElement>(null);

  // Scroll into view when activated externally
  useEffect(() => {
    if (isActive && ref.current) {
      ref.current.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [isActive]);

  return (
    <div
      ref={ref}
      className={`rv-para ${isActive ? "rv-para--active" : ""}`}
      style={{ animationDelay: `${index * 40}ms` }}
      onClick={() => onClick(paragraph.id)}
      role="button"
      tabIndex={0}
      aria-pressed={isActive}
      onKeyDown={(e) => e.key === "Enter" && onClick(paragraph.id)}
    >
      <span className="rv-para-id">{paragraph.id}</span>
      <p className="rv-para-text">{paragraph.text}</p>
      <div className="rv-para-hover-bar" />
    </div>
  );
}
