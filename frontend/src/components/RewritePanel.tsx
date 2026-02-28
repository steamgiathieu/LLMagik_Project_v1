// src/components/RewritePanel.tsx
import { useState } from "react";
import { rewriteApi } from "@/api/client";
import { useUiPreferences } from "@/lib/uiPreferences";
import "./RewritePanel.css";

interface RewritePanelProps {
  paragraphId: string;
  originalText: string;
  documentId?: string;
}

export default function RewritePanel({
  paragraphId,
  originalText,
  documentId,
}: RewritePanelProps) {
  const { t } = useUiPreferences();
  const [goal, setGoal] = useState("");
  const [rewritten, setRewritten] = useState("");
  const [explanation, setExplanation] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const PRESET_GOALS = [
    t("trung lập hơn", "more neutral"),
    t("rõ ràng và súc tích hơn", "clearer and more concise"),
    t("trang trọng và chuyên nghiệp hơn", "more formal and professional"),
    t("thân thiện và gần gũi hơn", "friendlier and more approachable"),
    t("ngắn gọn hơn", "shorter"),
    t("chi tiết và mở rộng hơn", "more detailed and expanded"),
  ];

  const handleRewrite = async () => {
    if (!goal.trim()) {
      setError(t("Vui lòng nhập mục tiêu viết lại", "Please enter a rewrite goal"));
      return;
    }
    if (!originalText.trim() || originalText.trim().length < 10) {
      setError(t("Ngữ liệu quá ngắn để viết lại", "Input text is too short to rewrite"));
      return;
    }

    setLoading(true);
    setError("");

    try {
      const result = await rewriteApi.rewrite({
        paragraph_id: paragraphId,
        original_text: originalText,
        goal: goal,
        document_id: documentId || undefined,
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
      <h3>✏️ {t("Viết lại đoạn văn", "Rewrite paragraph")}</h3>

      <div className="rewrite-section">
        <label>{t("Mục tiêu viết lại", "Rewrite goal")}</label>
        <textarea
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          placeholder={t(
            "Mô tả cách bạn muốn đoạn văn được viết lại...",
            "Describe how you want this paragraph to be rewritten..."
          )}
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
        <label>{t("Đoạn gốc", "Original paragraph")}</label>
        <div className="rewrite-original">
          <p>{originalText}</p>
        </div>
      </div>

      {rewritten && (
        <div className="rewrite-section">
          <label>{t("Đoạn được viết lại", "Rewritten paragraph")}</label>
          <div className="rewrite-result">
            <p>{rewritten}</p>
          </div>

          {explanation && (
            <div className="rewrite-explanation">
              <strong>{t("Giải thích", "Explanation")}:</strong>
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
        {loading ? t("Đang viết lại...", "Rewriting...") : t("Viết lại", "Rewrite")}
      </button>
    </div>
  );
}
