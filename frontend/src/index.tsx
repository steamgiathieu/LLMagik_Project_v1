import { type AnalysisResult } from "@/api/client";
import "./AnalysisPanel.css";

interface Props {
  result: AnalysisResult | null;
  selectedParagraphId: string | null;
  isAnalyzing: boolean;
}

export default function AnalysisPanel({ result, selectedParagraphId, isAnalyzing }: Props) {
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
            <h3>📝 Tóm tắt</h3>
            <p>{result.summary}</p>
          </section>
        )}

        {/* Tone */}
        {result.tone_analysis && (
          <section className="panel-section">
            <h3>🎭 Giọng văn</h3>
            <div className="tone-grid">
              <div className="tone-item">
                <span className="label">Tông</span>
                <span className="value">{result.tone_analysis.overall_tone}</span>
              </div>
              <div className="tone-item">
                <span className="label">Cảm xúc</span>
                <span className="value">{result.tone_analysis.sentiment}</span>
              </div>
              <div className="tone-item">
                <span className="label">Độ tin cậy</span>
                <span className="value">
                  {(result.tone_analysis.confidence_score * 100).toFixed(0)}%
                </span>
              </div>
            </div>
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

        {result.overall_score && (
          <section className="panel-section">
            <h3>📊 Điểm tổng</h3>
            <div className="score-grid">
              <div className="score-item">
                <span className="label">Rõ ràng</span>
                <span className="value">{result.overall_score.clarity}/10</span>
              </div>
              <div className="score-item">
                <span className="label">Mạch lạc</span>
                <span className="value">{result.overall_score.coherence}/10</span>
              </div>
              <div className="score-item">
                <span className="label">Văn phong</span>
                <span className="value">{result.overall_score.style}/10</span>
              </div>
            </div>
            <p className="score-note">{result.overall_score.note}</p>
          </section>
        )}
      </div>
    </div>
  );
}
