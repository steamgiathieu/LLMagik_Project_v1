import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDocumentStore } from "@/store/documentStore";
import RewritePanel from "@/components/RewritePanel";
import { useUiPreferences } from "@/lib/uiPreferences";
import "./Rewrite.css";

export default function Rewrite() {
  const navigate = useNavigate();
  const { t, dateLocale } = useUiPreferences();
  const {
    documents,
    currentDocument,
    selectedParagraphId,
    isLoading,
    fetchDocuments,
    fetchDocument,
    setSelectedParagraph,
  } = useDocumentStore();

  const [selectedDocId, setSelectedDocId] = useState("");

  useEffect(() => {
    fetchDocuments().catch(() => {});
  }, [fetchDocuments]);

  useEffect(() => {
    if (documents.length === 0) return;
    if (selectedDocId) return;
    setSelectedDocId(documents[0].document_id);
  }, [documents, selectedDocId]);

  useEffect(() => {
    if (!selectedDocId) return;
    fetchDocument(selectedDocId).catch(() => {});
  }, [selectedDocId, fetchDocument]);

  useEffect(() => {
    if (!currentDocument?.paragraphs?.length) return;
    if (selectedParagraphId) return;
    setSelectedParagraph(currentDocument.paragraphs[0].id);
  }, [currentDocument, selectedParagraphId, setSelectedParagraph]);

  const selectedParagraph = useMemo(() => {
    if (!currentDocument || !selectedParagraphId) return null;
    return currentDocument.paragraphs.find((p) => p.id === selectedParagraphId) ?? null;
  }, [currentDocument, selectedParagraphId]);

  if (isLoading && !currentDocument) {
    return (
      <div className="rewrite-page rewrite-center">
        <div className="spinner" />
        <p>{t("Đang tải dữ liệu...", "Loading data...")}</p>
      </div>
    );
  }

  return (
    <div className="rewrite-page">
      <header className="rewrite-header">
        <button onClick={() => navigate("/")} className="rewrite-back-btn">
          ← {t("Về trang chủ", "Back home")}
        </button>
        <h1>{t("Viết lại đoạn văn", "Rewrite paragraph")}</h1>
      </header>

      {documents.length === 0 ? (
        <div className="rewrite-empty">
          <h3>{t("Chưa có tài liệu", "No documents yet")}</h3>
          <p>{t("Hãy tải tài liệu lên trước khi dùng tính năng viết lại.", "Upload a document before using rewrite.")}</p>
          <button onClick={() => navigate("/")} className="rewrite-go-home">
            {t("Đi tới trang chủ", "Go to home")}
          </button>
        </div>
      ) : (
        <div className="rewrite-layout">
          <aside className="rewrite-sidebar">
            <label htmlFor="rewrite-doc-select">{t("Tài liệu", "Document")}</label>
            <select
              id="rewrite-doc-select"
              value={selectedDocId}
              onChange={(e) => {
                setSelectedDocId(e.target.value);
                setSelectedParagraph(null);
              }}
              className="rewrite-select"
            >
              {documents.map((doc) => (
                <option key={doc.document_id} value={doc.document_id}>
                  {(doc.title || t("Không tiêu đề", "Untitled"))} - {new Date(doc.created_at).toLocaleDateString(dateLocale)}
                </option>
              ))}
            </select>

            <div className="rewrite-paragraphs">
              {(currentDocument?.paragraphs ?? []).map((p) => (
                <button
                  key={p.id}
                  onClick={() => setSelectedParagraph(p.id)}
                  className={selectedParagraphId === p.id ? "rewrite-para-btn active" : "rewrite-para-btn"}
                >
                  <span>{p.id}</span>
                  <p>{p.text}</p>
                </button>
              ))}
            </div>
          </aside>

          <section className="rewrite-main">
            {currentDocument && selectedParagraph ? (
              <RewritePanel
                paragraphId={selectedParagraph.id}
                originalText={selectedParagraph.text}
                documentId={currentDocument.document_id}
              />
            ) : (
              <div className="rewrite-placeholder">
                {t("Chọn tài liệu và đoạn văn để bắt đầu viết lại.", "Select a document and paragraph to start rewriting.")}
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
