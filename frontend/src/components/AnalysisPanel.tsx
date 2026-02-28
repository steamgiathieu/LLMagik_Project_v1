// src/components/AnalysisPanel.tsx
import { AnalysisResult } from "@/api/client";
import { useUiPreferences } from "@/lib/uiPreferences";
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
  const { t } = useUiPreferences();

  const formatLegacyDifficulty = (difficulty: string) => {
    const normalized = difficulty.trim().toLowerCase();
    if (normalized === "easy") return t("Dễ", "Easy");
    if (normalized === "medium") return t("Trung bình", "Medium");
    if (normalized === "hard") return t("Khó", "Hard");
    return difficulty;
  };

  const supportLevelLabel = (level?: string | null) => {
    const normalized = (level || "").toLowerCase();
    if (normalized === "supported") return t("Có cơ sở", "Supported");
    if (normalized === "weak") return t("Cơ sở yếu", "Weak support");
    if (normalized === "unsupported") return t("Chưa có cơ sở", "Unsupported");
    return level || "N/A";
  };

  const issueTypeLabel = (type: string) => {
    switch (type) {
      case "fallacy":
        return t("Lỗi lập luận", "Logical fallacy");
      case "conclusion_jump":
        return t("Nhảy kết luận", "Jumped conclusion");
      case "fear_appeal":
        return t("Sử dụng nỗi sợ", "Fear appeal");
      case "spelling_grammar":
        return t("Chính tả/Ngữ pháp", "Spelling/Grammar");
      default:
        return type;
    }
  };

  if (isAnalyzing) {
    return (
      <div className="analysis-panel">
        <div className="panel-loading">
          <div className="spinner" />
          <p>{t("Đang phân tích...", "Analyzing...")}</p>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="analysis-panel">
        <div className="panel-empty">
          <p>{t("Chưa có kết quả phân tích", "No analysis result yet")}</p>
          <p className="hint">{t("Hệ thống đang chuẩn bị hoặc chưa đủ dữ liệu để hiển thị phân tích", "The system is preparing or there is not enough data to display analysis")}</p>
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
            <h3>📋 {t("Tóm tắt tổng quan", "Overview summary")}</h3>
            <p>{result.summary}</p>
          </section>
        )}

        {result.reader_summary_breakdown && (
          <section className="panel-section">
            <h3>🧭 {t("Tóm tắt nội dung chính", "Main content summary")}</h3>
            {result.reader_summary_breakdown.main_points && result.reader_summary_breakdown.main_points.length > 0 && (
              <>
                <p><strong>{t("Ý chính", "Key points")}</strong></p>
                <ul>
                  {result.reader_summary_breakdown.main_points.map((point, i) => (
                    <li key={`mp-${i}`}>{point}</li>
                  ))}
                </ul>
              </>
            )}
            {result.reader_summary_breakdown.figures && result.reader_summary_breakdown.figures.length > 0 && (
              <>
                <p><strong>{t("Số liệu (nếu có)", "Figures (if any)")}</strong></p>
                <ul>
                  {result.reader_summary_breakdown.figures.map((figure, i) => (
                    <li key={`fig-${i}`}>{figure}</li>
                  ))}
                </ul>
              </>
            )}
            {result.reader_summary_breakdown.argument_flow && result.reader_summary_breakdown.argument_flow.length > 0 && (
              <>
                <p><strong>{t("Mạch lập luận", "Argument flow")}</strong></p>
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
            <h3>🎨 {t("Giọng văn", "Tone")}</h3>
            <p>
              <strong>{t("Tổng thể", "Overall")}:</strong> {result.tone_analysis.overall_tone}
            </p>
            <p>
              <strong>{t("Cảm xúc", "Sentiment")}:</strong> {result.tone_analysis.sentiment}
            </p>
          </section>
        )}

        {result.deep_style_analysis && (
          <section className="panel-section">
            <h3>🧪 {t("Phân tích sâu văn phong", "Deep style analysis")}</h3>
            <p>
              <strong>{t("Tông cảm xúc", "Emotional tone")}:</strong> {result.deep_style_analysis.emotional_tone || "N/A"}
            </p>
            <p>
              <strong>{t("Tần số ngôn từ kích động", "Inflammatory wording frequency")}:</strong>{" "}
              {result.deep_style_analysis.inflammatory_word_frequency || "N/A"}
            </p>
            <p>
              <strong>{t("Độ thiên lệch nhóm", "Group bias level")}:</strong> {result.deep_style_analysis.group_bias_level || "N/A"}
            </p>
            {result.deep_style_analysis.notes && (
              <p>
                <strong>{t("Nhận xét", "Notes")}:</strong> {result.deep_style_analysis.notes}
              </p>
            )}
          </section>
        )}

        {/* Selected paragraph annotation */}
        {annotation && (
          <section className="panel-section panel-highlight">
            <h3>💡 {t("Đoạn", "Paragraph")} {annotation.paragraph_id}</h3>
            <p>
              <strong>{t("Ý chính", "Main idea")}:</strong> {annotation.main_idea}
            </p>
            <p>
              <strong>{t("Ghi chú", "Notes")}:</strong> {annotation.notes}
            </p>
          </section>
        )}

        {/* Reader mode specifics */}
        {result.key_takeaways && result.key_takeaways.length > 0 && (
          <section className="panel-section">
            <h3>⭐ {t("Điểm chính", "Key takeaways")}</h3>
            <ul>
              {result.key_takeaways.map((t, i) => (
                <li key={i}>{t}</li>
              ))}
            </ul>
          </section>
        )}

        {(result.readability_metrics || result.reading_difficulty) && (
          <section className="panel-section">
            <h3>📖 {t("Khả năng tiếp cận văn bản", "Readability")}</h3>
            {result.readability_metrics ? (
              <>
                <p>
                  <strong>{t("Chỉ số tiếp cận", "Accessibility score")}:</strong>{" "}
                  <span className="readability-score">
                    {result.readability_metrics.accessibility_score ?? "N/A"}/100
                  </span>{" "}
                  {result.readability_metrics.accessibility_label
                    ? `(${result.readability_metrics.accessibility_label})`
                    : ""}
                </p>
                <p>
                  <strong>{t("Độ dài câu trung bình", "Average sentence length")}:</strong>{" "}
                  {result.readability_metrics.avg_sentence_length_words ?? "N/A"} {t("từ/câu", "words/sentence")}
                </p>
                <p>
                  <strong>{t("Tỷ lệ câu dài", "Long sentence ratio")}:</strong>{" "}
                  {result.readability_metrics.long_sentence_ratio != null
                    ? `${Math.round(result.readability_metrics.long_sentence_ratio * 100)}%`
                    : "N/A"}
                </p>
                <p>
                  <strong>{t("Độ đa dạng từ vựng", "Lexical diversity")}:</strong>{" "}
                  {result.readability_metrics.lexical_diversity != null
                    ? `${Math.round(result.readability_metrics.lexical_diversity * 100)}%`
                    : "N/A"}
                </p>
                <p>
                  <strong>{t("Phù hợp với đối tượng", "Recommended reader profile")}:</strong>{" "}
                  {result.readability_metrics.recommended_reader_profile || "N/A"}
                </p>
                {result.readability_metrics.note && (
                  <p>
                    <strong>{t("Giải thích", "Explanation")}:</strong> {result.readability_metrics.note}
                  </p>
                )}
              </>
            ) : (
              <p>
                <strong>{t("Mức độ (legacy)", "Legacy difficulty")}:</strong> {formatLegacyDifficulty(result.reading_difficulty!)}
              </p>
            )}
          </section>
        )}

        {result.claim_checks && result.claim_checks.length > 0 && (
          <section className="panel-section">
            <h3>🔎 {t("Kiểm chứng phát biểu chính", "Claim checks")}</h3>
            {result.claim_checks.map((claim, i) => (
              <div key={i} className="issue-card">
                <p>
                  <strong>{claim.paragraph_id}</strong> · {supportLevelLabel(claim.support_level)}
                </p>
                <p>
                  <strong>{t("Phát biểu", "Claim")}:</strong> {claim.claim}
                </p>
                {claim.evidence_in_text && (
                  <p>
                    <strong>{t("Dấu hiệu chứng cứ", "Evidence in text")}:</strong> {claim.evidence_in_text}
                  </p>
                )}
                {claim.risk_if_believed && (
                  <p>
                    <strong>{t("Rủi ro nếu tin ngay", "Risk if accepted too quickly")}:</strong> {claim.risk_if_believed}
                  </p>
                )}
                {claim.verification_prompt && (
                  <p>
                    <strong>{t("Câu hỏi kiểm chứng", "Verification prompt")}:</strong> {claim.verification_prompt}
                  </p>
                )}
              </div>
            ))}
          </section>
        )}

        {result.critical_reading_guard && (
          <section className="panel-section">
            <h3>🛡️ {t("Chốt an toàn nhận thức", "Critical reading guard")}</h3>
            <p>
              <strong>{t("Mức rủi ro bị dẫn dắt", "Persuasion risk")}:</strong>{" "}
              {result.critical_reading_guard.persuasion_risk || "N/A"}
            </p>

            {result.critical_reading_guard.manipulation_signals &&
              result.critical_reading_guard.manipulation_signals.length > 0 && (
                <>
                  <p><strong>{t("Dấu hiệu thao túng", "Manipulation signals")}</strong></p>
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
                  <p><strong>{t("Điểm thiếu bối cảnh", "Missing context flags")}</strong></p>
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
                  <p><strong>{t("Hành động kiểm chứng nên làm", "Recommended fact-check actions")}</strong></p>
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
                  <p><strong>{t("Góc nhìn thay thế cần xem", "Alternative views to consider")}</strong></p>
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
                  <p><strong>{t("Chưa nên kết luận vội", "Do not conclude yet")}</strong></p>
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
            <h3>⚠️ {t("Vấn đề logic", "Logic issues")}</h3>
            {result.logic_issues.map((issue, i) => (
              <div key={i} className="issue-card">
                <strong>{issue.paragraph_id}:</strong> {issue.issue}
              </div>
            ))}
          </section>
        )}

        {result.logic_diagnostics && result.logic_diagnostics.length > 0 && (
          <section className="panel-section">
            <h3>🧠 {t("Chẩn đoán logic và ngôn ngữ", "Logic and language diagnostics")}</h3>
            {result.logic_diagnostics.map((diag, i) => (
              <div key={i} className={`issue-card issue-${diag.severity || "low"}`}>
                <p>
                  <strong>{diag.paragraph_id}</strong> · {issueTypeLabel(diag.issue_type)}
                </p>
                <p>{diag.description}</p>
                {diag.evidence && (
                  <p>
                    <strong>{t("Dấu hiệu", "Evidence")}:</strong> {diag.evidence}
                  </p>
                )}
              </div>
            ))}
          </section>
        )}

        {/* Writer mode specifics */}
        {result.style_issues && result.style_issues.length > 0 && (
          <section className="panel-section">
            <h3>✏️ {t("Vấn đề văn phong", "Style issues")}</h3>
            {result.style_issues.map((issue, i) => (
              <div key={i} className={`issue-card issue-${issue.severity}`}>
                <strong>{issue.paragraph_id}:</strong> {issue.issue}
              </div>
            ))}
          </section>
        )}

        {result.rewrite_suggestions && result.rewrite_suggestions.length > 0 && (
          <section className="panel-section">
            <h3>💭 {t("Đề xuất viết lại", "Rewrite suggestions")}</h3>
            {result.rewrite_suggestions.map((s, i) => (
              <div key={i} className="suggestion-card">
                <p>
                  <strong>{t("Gốc", "Original")}:</strong> {s.original}
                </p>
                <p>
                  <strong>{t("Đề xuất", "Suggestion")}:</strong> {s.suggestion}
                </p>
              </div>
            ))}
          </section>
        )}

        {result.overall_score && (
          <section className="panel-section">
            <h3>📊 {t("Điểm tổng", "Overall score")}</h3>
            <table className="score-table">
              <tbody>
                <tr>
                  <td>{t("Rõ ràng", "Clarity")}</td>
                  <td className="score">{result.overall_score.clarity}/10</td>
                </tr>
                <tr>
                  <td>{t("Mạch lạc", "Coherence")}</td>
                  <td className="score">{result.overall_score.coherence}/10</td>
                </tr>
                <tr>
                  <td>{t("Văn phong", "Style")}</td>
                  <td className="score">{result.overall_score.style}/10</td>
                </tr>
              </tbody>
            </table>
            {result.overall_score.note && <p>{result.overall_score.note}</p>}
          </section>
        )}

        {result.processing_ms && (
          <div className="panel-footer">
            <small>⏱️ {t("Xử lý trong", "Processed in")} {result.processing_ms}ms</small>
          </div>
        )}
      </div>
    </div>
  );
}
