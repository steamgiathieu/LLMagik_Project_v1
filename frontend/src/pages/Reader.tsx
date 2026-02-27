// src/pages/Reader.tsx
import { useEffect, useMemo, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useDocumentStore } from "@/store/documentStore";
import { useAnalysisStore } from "@/store/analysisStore";
import { useChatStore } from "@/store/chatStore";
import { ReaderView } from "@/components/Reader";
import AnalysisPanel from "@/components/AnalysisPanel";
import ChatBox from "@/components/ChatBox";
import { useUiPreferences } from "@/lib/uiPreferences";
import "./Reader.css";

export default function Reader() {
  const { docId } = useParams<{ docId: string }>();
  const navigate = useNavigate();

  const { currentDocument, selectedParagraphId, fetchDocument, setSelectedParagraph, isLoading } =
    useDocumentStore();
  const { analyze, currentResult, mode, setMode, isAnalyzing, error: analysisError } = useAnalysisStore();
  const { startNewSession } = useChatStore();
  const { t } = useUiPreferences();

  const [activeTab, setActiveTab] = useState<"analysis" | "chat">("analysis");
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  useEffect(() => {
    if (docId) {
      fetchDocument(docId);
      startNewSession();
    }
  }, [docId, fetchDocument, startNewSession]);

  const analysisKey = useMemo(() => {
    if (!currentDocument) return null;
    return `${currentDocument.document_id}:${mode}`;
  }, [currentDocument, mode]);

  useEffect(() => {
    if (!currentDocument || !analysisKey) return;
    analyze(currentDocument.document_id, mode, currentDocument.paragraphs).catch(() => {});
  }, [analysisKey, currentDocument, mode, analyze]);

  const selectedParagraphText = useMemo(() => {
    if (!selectedParagraphId || !currentDocument) return null;
    return currentDocument.paragraphs.find((p) => p.id === selectedParagraphId) ?? null;
  }, [currentDocument, selectedParagraphId]);

  if (isLoading) {
    return (
      <div className="reader-loading">
        <div className="spinner" />
        <p>{t("Đang tải tài liệu...", "Loading document...")}</p>
      </div>
    );
  }

  if (!currentDocument) {
    return (
      <div className="reader-error">
        <p>{t("Không tìm thấy tài liệu", "Document not found")}</p>
        <button onClick={() => navigate("/")} className="btn-primary">
          {t("Về trang chủ", "Back home")}
        </button>
      </div>
    );
  }

  return (
    <div className="reader-page">
      <header className="reader-header">
        <button onClick={() => navigate("/")} className="btn-back">
          ← {t("Về trang chủ", "Back home")}
        </button>
        <h1 className="reader-doc-title">{currentDocument.title || t("Tài liệu", "Document")}</h1>
        <div className="reader-actions">
          <select value={mode} onChange={(e) => setMode(e.target.value as any)} className="mode-select">
            <option value="reader">{t("Chế độ Người đọc", "Reader mode")}</option>
            <option value="writer">{t("Chế độ Người viết", "Writer mode")}</option>
          </select>
          <button onClick={() => setIsPreviewOpen(true)} className="btn-analyze">
            {t("Mở toàn văn bản", "Open full document")}
          </button>
        </div>
      </header>

      <div className="reader-layout">
        <aside className="reader-sidebar reader-sidebar-left">
          <div className="sidebar-tabs">
            <button
              className={activeTab === "analysis" ? "active" : ""}
              onClick={() => setActiveTab("analysis")}
            >
              📊 {t("Phân tích", "Analysis")}
            </button>
            <button
              className={activeTab === "chat" ? "active" : ""}
              onClick={() => setActiveTab("chat")}
            >
              💬 Chat
            </button>
          </div>

          <div className="sidebar-content">
            {activeTab === "analysis" && (
              <AnalysisPanel
                result={currentResult}
                selectedParagraphId={selectedParagraphId}
                isAnalyzing={isAnalyzing}
              />
            )}
            {activeTab === "chat" && <ChatBox documentId={currentDocument.document_id} />}
          </div>
        </aside>

        <section className="reader-preview">
          <div className="preview-card">
            <div className="preview-head">
              <h2>Đọc lướt nhanh</h2>
              <p>
                {selectedParagraphId
                  ? `${t("Đang chọn", "Selected")} ${selectedParagraphId}`
                  : t("Chọn một đoạn để xem nhanh ở đây", "Pick a paragraph to preview here")}
              </p>
            </div>

            <div className="preview-body">
              <div className="preview-paragraph-list">
                {currentDocument.paragraphs.slice(0, 8).map((paragraph) => (
                  <button
                    key={paragraph.id}
                    className={`preview-paragraph-item ${selectedParagraphId === paragraph.id ? "active" : ""}`}
                    onClick={() => setSelectedParagraph(paragraph.id)}
                  >
                    <span>{paragraph.id}</span>
                    <p>{paragraph.text}</p>
                  </button>
                ))}
              </div>

              {selectedParagraphText ? (
                <div className="preview-snippet">
                  <span>Đang chọn: {selectedParagraphText.id}</span>
                  <p>{selectedParagraphText.text}</p>
                </div>
              ) : (
                <div className="preview-empty">
                  <p>{t("Chọn một đoạn trong danh sách để đọc lướt nhanh.", "Select a paragraph from the list for quick reading.")}</p>
                </div>
              )}
            </div>

            <button onClick={() => setIsPreviewOpen(true)} className="btn-open-reader">
              {t("Đọc rõ toàn bộ văn bản", "Read full document clearly")}
            </button>
          </div>
        </section>
      </div>

      {analysisError && (
        <div className="reader-inline-error">
          <p>{t("Không thể phân tích tài liệu", "Cannot analyze document")}: {analysisError}</p>
        </div>
      )}

      {isAnalyzing && !currentResult && (
        <div className="reader-analysis-overlay" role="status" aria-live="polite">
          <div className="reader-analysis-modal">
            <div className="spinner" />
            <h3>{t("AI đang phân tích chuyên sâu", "AI is running deep analysis")}</h3>
            <p>{t("Đang tổng hợp nội dung, tone, vấn đề logic và gợi ý theo ngữ cảnh của bạn...", "Generating summary, tone, logical issues and suggestions based on your context...")}</p>
          </div>
        </div>
      )}

      {isPreviewOpen && (
        <div
          className="reader-popup-backdrop"
          onClick={() => setIsPreviewOpen(false)}
          role="presentation"
        >
          <div className="reader-popup" onClick={(e) => e.stopPropagation()}>
            <div className="reader-popup-header">
              <h2>{currentDocument.title || t("Tài liệu", "Document")}</h2>
              <button onClick={() => setIsPreviewOpen(false)} className="btn-close-popup">
                {t("Đóng", "Close")}
              </button>
            </div>
            <ReaderView
              paragraphs={currentDocument.paragraphs}
              title={currentDocument.title || undefined}
              selectedId={selectedParagraphId}
              onSelectParagraph={setSelectedParagraph}
            />
          </div>
        </div>
      )}
    </div>
  );
}
