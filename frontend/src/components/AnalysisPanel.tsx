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
  const formatLegacyDifficulty = (difficulty: string) => {
    const normalized = difficulty.trim().toLowerCase();
    if (normalized === "easy") return "Dễ";
    if (normalized === "medium") return "Trung bình";
    if (normalized === "hard") return "Khó";
    return difficulty;
  };

  const supportLevelLabel = (level?: string | null) => {
    const normalized = (level || "").toLowerCase();
    if (normalized === "supported") return "Có cơ sở";
    if (normalized === "weak") return "Cơ sở yếu";
    if (normalized === "unsupported") return "Chưa có cơ sở";
    return level || "N/A";
  };

  const issueTypeLabel = (type: string) => {
    switch (type) {
      case "fallacy":
        return "Lỗi lập luận";
      case "conclusion_jump":
        return "Nhảy kết luận";
      case "fear_appeal":
        return "Sử dụng nỗi sợ";
      case "spelling_grammar":
        return "Chính tả/Ngữ pháp";
      default:
        return type;
    }
  };

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
          <p className="hint">Hệ thống đang chuẩn bị hoặc chưa đủ dữ liệu để hiển thị phân tích</p>
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
            <h3>📋 Tóm tắt tổng quan</h3>
            <p>{result.summary}</p>
          </section>
        )}

        {result.reader_summary_breakdown && (
          <section className="panel-section">
            <h3>🧭 Tóm tắt nội dung chính</h3>
            {result.reader_summary_breakdown.main_points && result.reader_summary_breakdown.main_points.length > 0 && (
              <>
                <p><strong>Ý chính</strong></p>
                <ul>
                  {result.reader_summary_breakdown.main_points.map((point, i) => (
                    <li key={`mp-${i}`}>{point}</li>
                  ))}
                </ul>
              </>
            )}
            {result.reader_summary_breakdown.figures && result.reader_summary_breakdown.figures.length > 0 && (
              <>
                <p><strong>Số liệu (nếu có)</strong></p>
                <ul>
                  {result.reader_summary_breakdown.figures.map((figure, i) => (
                    <li key={`fig-${i}`}>{figure}</li>
                  ))}
                </ul>
              </>
            )}
            {result.reader_summary_breakdown.argument_flow && result.reader_summary_breakdown.argument_flow.length > 0 && (
              <>
                <p><strong>Mạch lập luận</strong></p>
                <ul>
                  {result.reader_summary_breakdown.argument_flow.map((step, i) => (
                    <li key={`flow-${i}`}>{step}</li>
                  ))}
                </ul>
              </>
            )}
          </section>
        )}

        {/* Tone Analysis */}
        {result.tone_analysis && (
          <section className="panel-section">
            <h3>🎨 Giọng văn</h3>
            <p>
              <strong>Tổng thể:</strong> {result.tone_analysis.overall_tone}
            </p>
            <p>
              <strong>Cảm xúc:</strong> {result.tone_analysis.sentiment}
            </p>
          </section>
        )}

        {result.deep_style_analysis && (
          <section className="panel-section">
            <h3>🧪 Phân tích sâu văn phong</h3>
            <p>
              <strong>Tông cảm xúc:</strong> {result.deep_style_analysis.emotional_tone || "N/A"}
            </p>
            <p>
              <strong>Tần số ngôn từ kích động:</strong>{" "}
              {result.deep_style_analysis.inflammatory_word_frequency || "N/A"}
            </p>
            <p>
              <strong>Độ thiên lệch nhóm:</strong> {result.deep_style_analysis.group_bias_level || "N/A"}
            </p>
            {result.deep_style_analysis.notes && (
              <p>
                <strong>Nhận xét:</strong> {result.deep_style_analysis.notes}
              </p>
            )}
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

        {(result.readability_metrics || result.reading_difficulty) && (
          <section className="panel-section">
            <h3>📖 Khả năng tiếp cận văn bản</h3>
            {result.readability_metrics ? (
              <>
                <p>
                  <strong>Chỉ số tiếp cận:</strong>{" "}
                  <span className="readability-score">
                    {result.readability_metrics.accessibility_score ?? "N/A"}/100
                  </span>{" "}
                  {result.readability_metrics.accessibility_label
                    ? `(${result.readability_metrics.accessibility_label})`
                    : ""}
                </p>
                <p>
                  <strong>Độ dài câu trung bình:</strong>{" "}
                  {result.readability_metrics.avg_sentence_length_words ?? "N/A"} từ/câu
                </p>
                <p>
                  <strong>Tỷ lệ câu dài:</strong>{" "}
                  {result.readability_metrics.long_sentence_ratio != null
                    ? `${Math.round(result.readability_metrics.long_sentence_ratio * 100)}%`
                    : "N/A"}
                </p>
                <p>
                  <strong>Độ đa dạng từ vựng:</strong>{" "}
                  {result.readability_metrics.lexical_diversity != null
                    ? `${Math.round(result.readability_metrics.lexical_diversity * 100)}%`
                    : "N/A"}
                </p>
                <p>
                  <strong>Phù hợp với đối tượng:</strong>{" "}
                  {result.readability_metrics.recommended_reader_profile || "N/A"}
                </p>
                {result.readability_metrics.note && (
                  <p>
                    <strong>Giải thích:</strong> {result.readability_metrics.note}
                  </p>
                )}
              </>
            ) : (
              <p>
                <strong>Mức độ (legacy):</strong> {formatLegacyDifficulty(result.reading_difficulty!)}
              </p>
            )}
          </section>
        )}

        {result.claim_checks && result.claim_checks.length > 0 && (
          <section className="panel-section">
            <h3>🔎 Kiểm chứng phát biểu chính</h3>
            {result.claim_checks.map((claim, i) => (
              <div key={i} className="issue-card">
                <p>
                  <strong>{claim.paragraph_id}</strong> · {supportLevelLabel(claim.support_level)}
                </p>
                <p>
                  <strong>Phát biểu:</strong> {claim.claim}
                </p>
                {claim.evidence_in_text && (
                  <p>
                    <strong>Dấu hiệu chứng cứ:</strong> {claim.evidence_in_text}
                  </p>
                )}
                {claim.risk_if_believed && (
                  <p>
                    <strong>Rủi ro nếu tin ngay:</strong> {claim.risk_if_believed}
                  </p>
                )}
                {claim.verification_prompt && (
                  <p>
                    <strong>Câu hỏi kiểm chứng:</strong> {claim.verification_prompt}
                  </p>
                )}
              </div>
            ))}
          </section>
        )}

        {result.critical_reading_guard && (
          <section className="panel-section">
            <h3>🛡️ Chốt an toàn nhận thức</h3>
            <p>
              <strong>Mức rủi ro bị dẫn dắt:</strong>{" "}
              {result.critical_reading_guard.persuasion_risk || "N/A"}
            </p>

            {result.critical_reading_guard.manipulation_signals &&
              result.critical_reading_guard.manipulation_signals.length > 0 && (
                <>
                  <p><strong>Dấu hiệu thao túng</strong></p>
                  <ul>
                    {result.critical_reading_guard.manipulation_signals.map((s, i) => (
                      <li key={`ms-${i}`}>{s}</li>
                    ))}
                  </ul>
                </>
              )}

            {result.critical_reading_guard.missing_context_flags &&
              result.critical_reading_guard.missing_context_flags.length > 0 && (
                <>
                  <p><strong>Điểm thiếu bối cảnh</strong></p>
                  <ul>
                    {result.critical_reading_guard.missing_context_flags.map((s, i) => (
                      <li key={`mc-${i}`}>{s}</li>
                    ))}
                  </ul>
                </>
              )}

            {result.critical_reading_guard.fact_check_actions &&
              result.critical_reading_guard.fact_check_actions.length > 0 && (
                <>
                  <p><strong>Hành động kiểm chứng nên làm</strong></p>
                  <ul>
                    {result.critical_reading_guard.fact_check_actions.map((s, i) => (
                      <li key={`fa-${i}`}>{s}</li>
                    ))}
                  </ul>
                </>
              )}

            {result.critical_reading_guard.alternative_views &&
              result.critical_reading_guard.alternative_views.length > 0 && (
                <>
                  <p><strong>Góc nhìn thay thế cần xem</strong></p>
                  <ul>
                    {result.critical_reading_guard.alternative_views.map((s, i) => (
                      <li key={`av-${i}`}>{s}</li>
                    ))}
                  </ul>
                </>
              )}

            {result.critical_reading_guard.do_not_conclude_yet &&
              result.critical_reading_guard.do_not_conclude_yet.length > 0 && (
                <>
                  <p><strong>Chưa nên kết luận vội</strong></p>
                  <ul>
                    {result.critical_reading_guard.do_not_conclude_yet.map((s, i) => (
                      <li key={`dc-${i}`}>{s}</li>
                    ))}
                  </ul>
                </>
              )}
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

        {result.logic_diagnostics && result.logic_diagnostics.length > 0 && (
          <section className="panel-section">
            <h3>🧠 Chẩn đoán logic và ngôn ngữ</h3>
            {result.logic_diagnostics.map((diag, i) => (
              <div key={i} className={`issue-card issue-${diag.severity || "low"}`}>
                <p>
                  <strong>{diag.paragraph_id}</strong> · {issueTypeLabel(diag.issue_type)}
                </p>
                <p>{diag.description}</p>
                {diag.evidence && (
                  <p>
                    <strong>Dấu hiệu:</strong> {diag.evidence}
                  </p>
                )}
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
