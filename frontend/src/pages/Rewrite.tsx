import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  rewriteApi,
  textsApi,
  type Document,
  type DocumentSummary,
  type RewriteResult,
} from "@/api/client";
import UploadModal from "@/components/UploadModal";
import RewritePanel from "@/components/RewritePanel";
import "./Rewrite.css";

export default function Rewrite() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [currentDocument, setCurrentDocument] = useState<Document | null>(null);
  const [selectedParagraphId, setSelectedParagraphId] = useState<string | null>(null);

  const [history, setHistory] = useState<RewriteResult[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [loadingDoc, setLoadingDoc] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showUpload, setShowUpload] = useState(false);

  const selectedParagraph = useMemo(
    () => currentDocument?.paragraphs.find((p) => p.id === selectedParagraphId) ?? null,
    [currentDocument, selectedParagraphId]
  );

  const loadRewriteHistory = async () => {
    setLoadingHistory(true);
    try {
      const items = await rewriteApi.history(8, 0);
      setHistory(items);
    } catch {
      setHistory([]);
    } finally {
      setLoadingHistory(false);
    }
  };

  const loadDocument = async (docId: string) => {
    setLoadingDoc(true);
    setError(null);
    try {
      const doc = await textsApi.get(docId);
      setCurrentDocument(doc);

      let nextParagraphId = doc.paragraphs[0]?.id ?? null;
      const queryParagraph = searchParams.get("paragraphId");
      if (queryParagraph && doc.paragraphs.some((p) => p.id === queryParagraph)) {
        nextParagraphId = queryParagraph;
      }
      setSelectedParagraphId(nextParagraphId);

      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.set("docId", docId);
        if (nextParagraphId) {
          next.set("paragraphId", nextParagraphId);
        } else {
          next.delete("paragraphId");
        }
        return next;
      });
    } catch (err: any) {
      setError(err.message || "Không thể tải tài liệu");
      setCurrentDocument(null);
      setSelectedParagraphId(null);
    } finally {
      setLoadingDoc(false);
    }
  };

  const loadDocuments = async (preferredDocId?: string) => {
    setLoadingDocs(true);
    setError(null);
    try {
      const docs = await textsApi.list();
      setDocuments(docs);

      if (docs.length === 0) {
        setCurrentDocument(null);
        setSelectedParagraphId(null);
        return;
      }

      const queryDocId = preferredDocId || searchParams.get("docId") || docs[0].document_id;
      const docExists = docs.some((d) => d.document_id === queryDocId);
      await loadDocument(docExists ? queryDocId : docs[0].document_id);
    } catch (err: any) {
      setError(err.message || "Không thể tải danh sách tài liệu");
      setDocuments([]);
      setCurrentDocument(null);
      setSelectedParagraphId(null);
    } finally {
      setLoadingDocs(false);
    }
  };

  useEffect(() => {
    loadDocuments();
    loadRewriteHistory();
  }, []);

  const handleSelectParagraph = (paragraphId: string) => {
    setSelectedParagraphId(paragraphId);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set("paragraphId", paragraphId);
      return next;
    });
  };

  return (
    <div className="rewrite-page">
      <header className="rewrite-page-header">
        <button className="btn-back" onClick={() => navigate("/")}>← Trang chủ</button>
        <h1>✍️ Rewrite văn bản</h1>
        <button className="btn-primary" onClick={() => setShowUpload(true)}>
          + Upload tài liệu
        </button>
      </header>

      <main className="rewrite-layout">
        <aside className="rewrite-sidebar">
          <section className="rewrite-card">
            <h3>Tài liệu</h3>
            {loadingDocs && <p className="rewrite-muted">Đang tải tài liệu...</p>}
            {!loadingDocs && documents.length === 0 && (
              <div className="rewrite-empty">
                <p>Chưa có tài liệu để rewrite.</p>
                <button className="btn-primary" onClick={() => setShowUpload(true)}>
                  Upload ngay
                </button>
              </div>
            )}
            {!loadingDocs && documents.length > 0 && (
              <div className="rewrite-doc-list">
                {documents.map((doc) => (
                  <button
                    key={doc.document_id}
                    className={`rewrite-doc-item ${currentDocument?.document_id === doc.document_id ? "active" : ""}`}
                    onClick={() => loadDocument(doc.document_id)}
                  >
                    <strong>{doc.title || "Không tiêu đề"}</strong>
                    <span>{doc.paragraph_count} đoạn</span>
                  </button>
                ))}
              </div>
            )}
          </section>

          <section className="rewrite-card">
            <h3>Đoạn văn</h3>
            {!currentDocument && <p className="rewrite-muted">Chọn tài liệu để bắt đầu.</p>}
            {currentDocument && currentDocument.paragraphs.length === 0 && (
              <p className="rewrite-muted">Tài liệu này chưa có đoạn văn hợp lệ.</p>
            )}
            {currentDocument && currentDocument.paragraphs.length > 0 && (
              <div className="rewrite-para-list">
                {currentDocument.paragraphs.map((p) => (
                  <button
                    key={p.id}
                    className={`rewrite-para-item ${selectedParagraphId === p.id ? "active" : ""}`}
                    onClick={() => handleSelectParagraph(p.id)}
                  >
                    <span className="rewrite-para-id">{p.id}</span>
                    <span className="rewrite-para-preview">{p.text}</span>
                  </button>
                ))}
              </div>
            )}
          </section>
        </aside>

        <section className="rewrite-workspace">
          {error && <div className="error">{error}</div>}

          {loadingDoc && (
            <div className="rewrite-center">
              <div className="spinner" />
              <p>Đang tải nội dung tài liệu...</p>
            </div>
          )}

          {!loadingDoc && !currentDocument && (
            <div className="rewrite-center">
              <p>Bạn chưa có tài liệu nào để rewrite.</p>
              <button className="btn-primary" onClick={() => setShowUpload(true)}>
                Upload tài liệu
              </button>
            </div>
          )}

          {!loadingDoc && currentDocument && !selectedParagraph && (
            <div className="rewrite-center">
              <p>Hãy chọn một đoạn văn ở bên trái để rewrite.</p>
            </div>
          )}

          {!loadingDoc && selectedParagraph && (
            <RewritePanel
              paragraphId={selectedParagraph.id}
              originalText={selectedParagraph.text}
              documentId={currentDocument?.document_id}
            />
          )}

          <section className="rewrite-history-card">
            <h3>🕘 Rewrite gần đây</h3>
            {loadingHistory && <p className="rewrite-muted">Đang tải lịch sử...</p>}
            {!loadingHistory && history.length === 0 && (
              <p className="rewrite-muted">Chưa có lượt rewrite nào.</p>
            )}
            {!loadingHistory && history.length > 0 && (
              <div className="rewrite-history-list">
                {history.map((item) => (
                  <div key={item.rewrite_id} className="rewrite-history-item">
                    <div>
                      <strong>{item.goal}</strong>
                      <p>{item.paragraph_id} · {new Date(item.created_at).toLocaleString("vi-VN")}</p>
                    </div>
                    <span>{item.ai_provider || "ai"}</span>
                  </div>
                ))}
              </div>
            )}
          </section>
        </section>
      </main>

      {showUpload && (
        <UploadModal
          onClose={() => setShowUpload(false)}
          onSuccess={async (docId) => {
            setShowUpload(false);
            await loadDocuments(docId);
          }}
        />
      )}
    </div>
  );
}
