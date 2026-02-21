// src/pages/Reader.tsx
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useDocumentStore } from "@/store/documentStore";
import { useAnalysisStore } from "@/store/analysisStore";
import { useChatStore } from "@/store/chatStore";
import { ReaderView } from "@/components/Reader";
import AnalysisPanel from "@/components/AnalysisPanel";
import ChatBox from "@/components/ChatBox";
import "./Reader.css";

export default function Reader() {
  const { docId } = useParams<{ docId: string }>();
  const navigate = useNavigate();

  const { currentDocument, selectedParagraphId, fetchDocument, setSelectedParagraph, isLoading } =
    useDocumentStore();
  const { analyze, currentResult, mode, setMode, isAnalyzing } = useAnalysisStore();
  const { startNewSession } = useChatStore();

  const [activeTab, setActiveTab] = useState<"analysis" | "chat">("analysis");

  useEffect(() => {
    if (docId) {
      fetchDocument(docId);
      startNewSession(); // Reset chat when entering new doc
    }
  }, [docId]);

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
            title={currentDocument.title}
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
      </div>
    </div>
  );
}
