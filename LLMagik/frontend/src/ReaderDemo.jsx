import { useState, useRef, useEffect } from "react";

const SAMPLE_PARAGRAPHS = [
  {
    id: "P1",
    text: "Trí tuệ nhân tạo đang thay đổi cách chúng ta tương tác với văn bản — không chỉ đọc mà còn hiểu, phân tích và tái tạo ngôn ngữ theo những cách chưa từng có trước đây.",
  },
  {
    id: "P2",
    text: "Những mô hình ngôn ngữ lớn như GPT hay Claude được huấn luyện trên hàng tỷ trang văn bản, giúp chúng nắm bắt được không chỉ ngữ nghĩa mà cả ngữ điệu, phong cách và ý định của người viết.",
  },
  {
    id: "P3",
    text: "Tuy nhiên, câu hỏi đặt ra là: liệu máy móc có thực sự \"hiểu\" văn bản hay chỉ đang thực hiện các phép tính thống kê phức tạp trên chuỗi ký tự? Đây là một trong những tranh luận triết học thú vị nhất của thời đại chúng ta.",
  },
  {
    id: "P4",
    text: "Về mặt thực tiễn, khả năng phân tích văn bản tự động mở ra cánh cửa cho nhiều ứng dụng: từ hỗ trợ học sinh trong việc cải thiện kỹ năng viết, đến giúp nhà báo kiểm chứng thông tin nhanh hơn.",
  },
  {
    id: "P5",
    text: "Một trong những thách thức lớn nhất là sự thiếu nhất quán: cùng một đoạn văn, AI có thể phân tích theo nhiều cách khác nhau tùy vào cách đặt câu hỏi. Đây là bản chất xác suất của các mô hình ngôn ngữ.",
  },
  {
    id: "P6",
    text: "Dù vậy, khi được sử dụng đúng cách với sự giám sát của con người, AI phân tích văn bản có thể trở thành một công cụ đắc lực — không thay thế tư duy phê phán mà bổ sung và mở rộng nó.",
  },
];

// ── CSS injected as string ──────────────────────────────────
const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,500;0,600;1,400&family=DM+Mono:wght@400;500&display=swap');

  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #f0ede8; }

  .rv-shell {
    --rv-bg: #f7f4ef;
    --rv-ink: #1a1714;
    --rv-ink-muted: #6b6560;
    --rv-ink-faint: #c5bfb8;
    --rv-accent: #b8522a;
    --rv-active-bg: #fef3ec;
    --rv-hover-bg: #f9f6f2;
    --rv-font-body: 'Lora', Georgia, serif;
    --rv-font-mono: 'DM Mono', monospace;

    display: flex;
    flex-direction: column;
    height: 100vh;
    background: var(--rv-bg);
    font-family: var(--rv-font-body);
    position: relative;
  }

  .rv-progress-track {
    position: absolute; top: 0; left: 0; right: 0;
    height: 3px; background: var(--rv-ink-faint); z-index: 10;
  }
  .rv-progress-fill {
    height: 100%; background: var(--rv-accent);
    transition: width 0.2s ease;
  }

  .rv-header {
    padding: 28px 40px 20px;
    border-bottom: 1px solid var(--rv-ink-faint);
    display: flex; flex-direction: column; gap: 6px;
    background: var(--rv-bg); flex-shrink: 0;
  }
  .rv-header-label {
    font-family: var(--rv-font-mono); font-size: 10px;
    letter-spacing: 0.2em; color: var(--rv-accent); text-transform: uppercase;
  }
  .rv-title {
    font-size: 1.1rem; font-weight: 600; color: var(--rv-ink);
    line-height: 1.35; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }
  .rv-meta {
    font-family: var(--rv-font-mono); font-size: 11px; color: var(--rv-ink-muted);
  }

  .rv-scroll {
    flex: 1; overflow-y: auto; scroll-behavior: smooth;
    scrollbar-width: thin; scrollbar-color: var(--rv-ink-faint) transparent;
  }
  .rv-scroll::-webkit-scrollbar { width: 5px; }
  .rv-scroll::-webkit-scrollbar-thumb {
    background: var(--rv-ink-faint); border-radius: 10px;
  }

  .rv-page {
    max-width: 680px; margin: 0 auto;
    padding: 36px 40px 60px;
    display: flex; flex-direction: column; gap: 4px;
  }

  .rv-para {
    position: relative;
    padding: 18px 36px 18px 16px;
    border-left: 3px solid transparent;
    border-radius: 2px;
    cursor: pointer;
    background: transparent;
    transition: background 0.18s ease, border-color 0.18s ease;
    outline: none;
    animation: rv-fade-in 0.35s ease both;
  }
  @keyframes rv-fade-in {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .rv-para:hover { background: var(--rv-hover-bg); border-left-color: var(--rv-ink-faint); }
  .rv-para:focus-visible { outline: 2px solid var(--rv-accent); outline-offset: 2px; }
  .rv-para--active { background: var(--rv-active-bg); border-left-color: var(--rv-accent); }
  .rv-para--active .rv-para-id { color: var(--rv-accent); }

  .rv-para-id {
    display: inline-block;
    font-family: var(--rv-font-mono); font-size: 10px; font-weight: 500;
    letter-spacing: 0.08em; color: var(--rv-ink-faint);
    margin-bottom: 8px; transition: color 0.18s ease; user-select: none;
  }
  .rv-para-text {
    font-size: 1rem; line-height: 1.9; color: var(--rv-ink);
    font-weight: 400; letter-spacing: 0.005em; word-break: break-word;
  }
  .rv-para-arrow {
    position: absolute; right: 14px; top: 50%;
    transform: translateY(-50%);
    font-size: 10px; color: var(--rv-ink-faint);
    opacity: 0; transition: opacity 0.18s ease;
    font-family: var(--rv-font-mono);
  }
  .rv-para:hover .rv-para-arrow,
  .rv-para--active .rv-para-arrow { opacity: 1; color: var(--rv-accent); }

  .rv-footer {
    padding: 10px 40px;
    border-top: 1px solid var(--rv-ink-faint);
    display: flex; align-items: center; justify-content: space-between;
    background: var(--rv-bg); flex-shrink: 0;
  }
  .rv-progress-text {
    font-family: var(--rv-font-mono); font-size: 11px; color: var(--rv-ink-muted);
  }
  .rv-selected-label {
    font-family: var(--rv-font-mono); font-size: 11px; color: var(--rv-ink-muted);
  }
  .rv-selected-label strong { color: var(--rv-accent); font-weight: 500; }

  .rv-toast {
    position: fixed; bottom: 60px; left: 50%; transform: translateX(-50%);
    background: var(--rv-ink); color: #f7f4ef;
    font-family: var(--rv-font-mono); font-size: 12px;
    padding: 8px 18px; border-radius: 20px;
    opacity: 0; transition: opacity 0.25s ease;
    pointer-events: none; white-space: nowrap;
  }
  .rv-toast--show { opacity: 1; }
`;

function ParagraphBlock({ paragraph, index, isActive, onClick }) {
  const ref = useRef(null);

  useEffect(() => {
    if (isActive && ref.current) {
      ref.current.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [isActive]);

  return (
    <div
      ref={ref}
      className={`rv-para ${isActive ? "rv-para--active" : ""}`}
      style={{ animationDelay: `${index * 50}ms` }}
      onClick={() => onClick(paragraph.id)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onClick(paragraph.id)}
    >
      <span className="rv-para-id">{paragraph.id}</span>
      <p className="rv-para-text">{paragraph.text}</p>
      <span className="rv-para-arrow">→</span>
    </div>
  );
}

export default function ReaderDemo() {
  const [activeId, setActiveId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [toast, setToast] = useState("");
  const [showToast, setShowToast] = useState(false);
  const scrollRef = useRef(null);
  const toastTimer = useRef(null);

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

  const handleSelect = (id) => {
    setActiveId(id);
    setToast(`onSelectParagraph("${id}") called`);
    setShowToast(true);
    clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setShowToast(false), 2000);
  };

  return (
    <>
      <style>{styles}</style>
      <div className="rv-shell">
        <div className="rv-progress-track">
          <div className="rv-progress-fill" style={{ width: `${progress}%` }} />
        </div>

        <header className="rv-header">
          <span className="rv-header-label">ĐANG ĐỌC</span>
          <h1 className="rv-title">AI và Tương Lai Của Phân Tích Văn Bản</h1>
          <span className="rv-meta">{SAMPLE_PARAGRAPHS.length} đoạn · Click vào đoạn để chọn</span>
        </header>

        <div className="rv-scroll" ref={scrollRef}>
          <div className="rv-page">
            {SAMPLE_PARAGRAPHS.map((p, i) => (
              <ParagraphBlock
                key={p.id}
                paragraph={p}
                index={i}
                isActive={activeId === p.id}
                onClick={handleSelect}
              />
            ))}
          </div>
        </div>

        <footer className="rv-footer">
          <span className="rv-progress-text">{progress}%</span>
          {activeId
            ? <span className="rv-selected-label">Đoạn <strong>{activeId}</strong> đang chọn</span>
            : <span className="rv-selected-label">Chưa chọn đoạn nào</span>
          }
        </footer>

        <div className={`rv-toast ${showToast ? "rv-toast--show" : ""}`}>{toast}</div>
      </div>
    </>
  );
}
