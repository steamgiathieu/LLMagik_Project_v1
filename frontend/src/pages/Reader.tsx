// src/pages/Reader.tsx
import { useEffect, useState } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { useDocumentStore } from "@/store/documentStore";
import { useAnalysisStore } from "@/store/analysisStore";
import { useChatStore } from "@/store/chatStore";
import { ReaderView } from "@/components/Reader";
import AnalysisPanel from "@/components/AnalysisPanel";
import ChatBox from "@/components/ChatBox";
import RewritePanel from "@/components/RewritePanel";
import "./Reader.css";

export default function Reader() {
  const { docId } = useParams<{ docId: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const { currentDocument, selectedParagraphId, fetchDocument, setSelectedParagraph, isLoading } =
    useDocumentStore();
  const { analyze, currentResult, mode, setMode, isAnalyzing } = useAnalysisStore();
  const { startNewSession } = useChatStore();

  const requestedTab = searchParams.get("tab");
  const defaultTab: "analysis" | "chat" | "rewrite" =
    requestedTab === "chat" || requestedTab === "rewrite" ? requestedTab : "analysis";
  const [activeTab, setActiveTab] = useState<"analysis" | "chat" | "rewrite">(defaultTab);

  useEffect(() => {
    const tab = searchParams.get("tab");
    if (tab === "chat" || tab === "rewrite" || tab === "analysis") {
      setActiveTab(tab);
      return;
    }
    setActiveTab("analysis");
  }, [searchParams]);

  useEffect(() => {
    if (docId) {
      fetchDocument(docId);
      startNewSession(); // Reset chat when entering new doc
    }
  }, [docId]);

  useEffect(() => {
    if (activeTab !== "rewrite") return;
    if (!currentDocument || currentDocument.paragraphs.length === 0) return;
    if (selectedParagraphId) return;
    setSelectedParagraph(currentDocument.paragraphs[0].id);
  }, [activeTab, currentDocument, selectedParagraphId, setSelectedParagraph]);

  const handleAnalyze = async () => {
    if (!currentDocument) return;
    await analyze(currentDocument.document_id, mode, currentDocument.paragraphs);
  };

  if (isLoading) {
    return (
      <div className="reader-loading">
        <div className="spinner" />
        <p>Đang tải tài liệu...</p>
      </div>
    );
  }

  if (!currentDocument) {
    return (
      <div className="reader-error">
        <p>Không tìm thấy tài liệu</p>
        <button onClick={() => navigate("/")} className="btn-primary">
          Về trang chủ
        </button>
      </div>
    );
  }

  const selectedParagraph =
    currentDocument.paragraphs.find((p) => p.id === selectedParagraphId) ?? null;

  return (
    <div className="reader-page">
      {/* Header */}
      <header className="reader-header">
        <button onClick={() => navigate("/")} className="btn-back">
          ← Về trang chủ
        </button>
        <h1 className="reader-doc-title">{currentDocument.title || "Tài liệu"}</h1>
        <div className="reader-actions">
          <select value={mode} onChange={(e) => setMode(e.target.value as any)} className="mode-select">
            <option value="reader">Chế độ Người đọc</option>
            <option value="writer">Chế độ Người viết</option>
          </select>
          <button onClick={handleAnalyze} disabled={isAnalyzing} className="btn-analyze">
            {isAnalyzing ? "Đang phân tích..." : "🔍 Phân tích"}
          </button>
        </div>
      </header>

      {/* Main layout: 2 columns */}
      <div className="reader-layout">
        {/* Left: Text content */}
        <div className="reader-content">
          <ReaderView
            paragraphs={currentDocument.paragraphs}
            title={currentDocument.title || undefined}
            selectedId={selectedParagraphId}
            onSelectParagraph={setSelectedParagraph}
          />
        </div>

        {/* Right: Analysis / Chat */}
        <aside className="reader-sidebar">
          <div className="sidebar-tabs">
            <button
              className={activeTab === "analysis" ? "active" : ""}
              onClick={() => setActiveTab("analysis")}
            >
              📊 Phân tích
            </button>
            <button
              className={activeTab === "chat" ? "active" : ""}
              onClick={() => setActiveTab("chat")}
            >
              💬 Chat
            </button>
            <button
              className={activeTab === "rewrite" ? "active" : ""}
              onClick={() => setActiveTab("rewrite")}
            >
              ✏️ Viết lại
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
            {activeTab === "rewrite" &&
              (selectedParagraph ? (
                <RewritePanel
                  paragraphId={selectedParagraph.id}
                  originalText={selectedParagraph.text}
                  documentId={currentDocument.document_id}
                />
              ) : (
                <div className="panel-empty">
                  <p>Chưa chọn đoạn văn</p>
                  <p className="hint">Hãy chọn một đoạn ở khung bên trái để viết lại</p>
                </div>
              ))}
          </div>
        </aside>
      </div>
    </div>
  );
}
