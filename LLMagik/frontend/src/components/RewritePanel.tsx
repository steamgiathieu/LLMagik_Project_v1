// src/components/RewritePanel.tsx
import { useState } from "react";
import { rewriteApi } from "@/api/client";
import "./RewritePanel.css";

interface RewritePanelProps {
  paragraphId: string;
  originalText: string;
  documentId: string;
}

export default function RewritePanel({
  paragraphId,
  originalText,
  documentId,
}: RewritePanelProps) {
  const [goal, setGoal] = useState("");
  const [rewritten, setRewritten] = useState("");
  const [explanation, setExplanation] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const PRESET_GOALS = [
    "trung lập hơn",
    "rõ ràng và súc tích hơn",
    "trang trọng và chuyên nghiệp hơn",
    "thân thiện và gần gũi hơn",
    "ngắn gọn hơn",
    "chi tiết và mở rộng hơn",
  ];

  const handleRewrite = async () => {
    if (!goal.trim()) {
      setError("Vui lòng nhập mục tiêu viết lại");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const result = await rewriteApi.rewrite({
        paragraph_id: paragraphId,
        original_text: originalText,
        goal: goal,
        document_id: documentId,
      });

      setRewritten(result.rewritten_text);
      setExplanation(result.explanation || "");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rewrite-panel">
      <h3>✏️ Viết lại đoạn văn</h3>

      <div className="rewrite-section">
        <label>Mục tiêu viết lại</label>
        <textarea
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          placeholder="Mô tả cách bạn muốn đoạn văn được viết lại..."
          rows={2}
          disabled={loading}
          className="rewrite-textarea"
        />

        <div className="rewrite-presets">
          {PRESET_GOALS.map((preset) => (
            <button
              key={preset}
              onClick={() => setGoal(preset)}
              disabled={loading}
              className="preset-btn"
            >
              {preset}
            </button>
          ))}
        </div>
      </div>

      <div className="rewrite-section">
        <label>Đoạn gốc</label>
        <div className="rewrite-original">
          <p>{originalText}</p>
        </div>
      </div>

      {rewritten && (
        <div className="rewrite-section">
          <label>Đoạn được viết lại</label>
          <div className="rewrite-result">
            <p>{rewritten}</p>
          </div>

          {explanation && (
            <div className="rewrite-explanation">
              <strong>Giải thích:</strong>
              <p>{explanation}</p>
            </div>
          )}
        </div>
      )}

      {error && <div className="rewrite-error">{error}</div>}

      <button
        onClick={handleRewrite}
        disabled={loading || !goal.trim()}
        className="btn-rewrite"
      >
        {loading ? "Đang viết lại..." : "Viết lại"}
      </button>
    </div>
  );
}
