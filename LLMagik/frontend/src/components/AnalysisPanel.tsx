// src/components/AnalysisPanel.tsx
import { AnalysisResult } from "@/api/client";
import "./AnalysisPanel.css";

interface AnalysisPanelProps {
  result: AnalysisResult | null;
  selectedParagraphId: string | null;
  isAnalyzing: boolean;
}

export default function AnalysisPanel({
  result,
  selectedParagraphId,
  isAnalyzing,
}: AnalysisPanelProps) {
  if (isAnalyzing) {
    return (
      <div className="analysis-panel">
        <div className="panel-loading">
          <div className="spinner" />
          <p>Đang phân tích...</p>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="analysis-panel">
        <div className="panel-empty">
          <p>Chưa có kết quả phân tích</p>
          <p className="hint">Chọn chế độ và nhấn "Phân tích" để bắt đầu</p>
        </div>
      </div>
    );
  }

  const annotation = result.paragraph_analyses?.find(
    (p) => p.paragraph_id === selectedParagraphId
  );

  return (
    <div className="analysis-panel">
      <div className="panel-scroll">
        {/* Summary */}
        {result.summary && (
          <section className="panel-section">
            <h3>📋 Tóm tắt</h3>
            <p>{result.summary}</p>
          </section>
        )}

        {/* Tone Analysis */}
        {result.tone_analysis && (
          <section className="panel-section">
            <h3>🎨 Giọng văn</h3>
            <p>
              <strong>Tổn thể:</strong> {result.tone_analysis.overall_tone}
            </p>
            <p>
              <strong>Cảm xúc:</strong> {result.tone_analysis.sentiment}
            </p>
          </section>
        )}

        {/* Selected paragraph annotation */}
        {annotation && (
          <section className="panel-section panel-highlight">
            <h3>💡 Đoạn {annotation.paragraph_id}</h3>
            <p>
              <strong>Ý chính:</strong> {annotation.main_idea}
            </p>
            <p>
              <strong>Ghi chú:</strong> {annotation.notes}
            </p>
          </section>
        )}

        {/* Reader mode specifics */}
        {result.key_takeaways && result.key_takeaways.length > 0 && (
          <section className="panel-section">
            <h3>⭐ Điểm chính</h3>
            <ul>
              {result.key_takeaways.map((t, i) => (
                <li key={i}>{t}</li>
              ))}
            </ul>
          </section>
        )}

        {result.reading_difficulty && (
          <section className="panel-section">
            <h3>📖 Mức độ khó</h3>
            <p>
              <strong>{result.reading_difficulty}</strong>
            </p>
          </section>
        )}

        {result.logic_issues && result.logic_issues.length > 0 && (
          <section className="panel-section">
            <h3>⚠️ Vấn đề logic</h3>
            {result.logic_issues.map((issue, i) => (
              <div key={i} className="issue-card">
                <strong>{issue.paragraph_id}:</strong> {issue.issue}
              </div>
            ))}
          </section>
        )}

        {/* Writer mode specifics */}
        {result.style_issues && result.style_issues.length > 0 && (
          <section className="panel-section">
            <h3>✏️ Vấn đề văn phong</h3>
            {result.style_issues.map((issue, i) => (
              <div key={i} className={`issue-card issue-${issue.severity}`}>
                <strong>{issue.paragraph_id}:</strong> {issue.issue}
              </div>
            ))}
          </section>
        )}

        {result.rewrite_suggestions && result.rewrite_suggestions.length > 0 && (
          <section className="panel-section">
            <h3>💭 Đề xuất viết lại</h3>
            {result.rewrite_suggestions.map((s, i) => (
              <div key={i} className="suggestion-card">
                <p>
                  <strong>Gốc:</strong> {s.original}
                </p>
                <p>
                  <strong>Đề xuất:</strong> {s.suggestion}
                </p>
              </div>
            ))}
          </section>
        )}

        {result.overall_score && (
          <section className="panel-section">
            <h3>📊 Điểm tổng</h3>
            <table className="score-table">
              <tbody>
                <tr>
                  <td>Rõ ràng</td>
                  <td className="score">{result.overall_score.clarity}/10</td>
                </tr>
                <tr>
                  <td>Mạch lạc</td>
                  <td className="score">{result.overall_score.coherence}/10</td>
                </tr>
                <tr>
                  <td>Văn phong</td>
                  <td className="score">{result.overall_score.style}/10</td>
                </tr>
              </tbody>
            </table>
            {result.overall_score.note && <p>{result.overall_score.note}</p>}
          </section>
        )}

        {result.processing_ms && (
          <div className="panel-footer">
            <small>⏱️ Xử lý trong {result.processing_ms}ms</small>
          </div>
        )}
      </div>
    </div>
  );
}
