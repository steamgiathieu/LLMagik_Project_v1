// src/pages/Home.tsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { useDocumentStore } from "@/store/documentStore";
import UploadModal from "@/components/UploadModal";
import { useUiPreferences } from "@/lib/uiPreferences";
import "./Home.css";

export default function Home() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { documents, fetchDocuments, deleteDocument, isLoading } = useDocumentStore();
  const { t, dateLocale, language: currentLang } = useUiPreferences();
  const [showUpload, setShowUpload] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleDocumentClick = (docId: string) => {
    navigate(`/reader/${docId}`);
  };

  const handleDelete = async (e: React.MouseEvent, docId: string) => {
    e.stopPropagation();
    if (confirm(t("Xóa tài liệu này?", "Delete this document?"))) {
      await deleteDocument(docId);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  // Get language flag
  const langFlags: Record<string, string> = {
    vi: "🇻🇳",
    en: "🇬🇧",
  };

  const recentDocs = documents.slice(0, 4);

  return (
    <div className="dashboard-page">
      {/* ── Top Navigation ── */}
      <header className="dashboard-header">
        <div className="dashboard-header-left">
          <div className="dashboard-brand">
            <span className="dashboard-brand-icon">✨</span>
            <span className="dashboard-brand-name">InfoLens AI</span>
          </div>
        </div>

        <div className="dashboard-header-right">
          <button
            onClick={() => navigate("/history")}
            className="dashboard-header-btn"
            title={t("Lịch sử hoạt động", "Activity history")}
          >
            <span>📊</span> {t("Lịch sử", "History")}
          </button>
          <button
            onClick={() => navigate("/profile")}
            className="dashboard-header-btn dashboard-profile"
          >
            <div className="dashboard-avatar">
              {user?.nickname?.charAt(0).toUpperCase() || "U"}
            </div>
            <div className="dashboard-profile-info">
              <span className="dashboard-profile-name">{user?.nickname}</span>
              <span className="dashboard-profile-lang">
                {langFlags[currentLang]} {currentLang.toUpperCase()}
              </span>
            </div>
          </button>
          <button onClick={handleLogout} className="dashboard-logout-btn" title={t("Đăng xuất", "Sign out")}>
            <span>🚪</span>
          </button>
        </div>
      </header>

      {/* ── Main Content ── */}
      <main className="dashboard-main">
        {/* Welcome Section */}
        <section className="dashboard-welcome">
          <div className="dashboard-welcome-content">
            <h1 className="dashboard-welcome-title">
              {t("Chào", "Hello")} {user?.nickname} 👋
            </h1>
            <p className="dashboard-welcome-subtitle">
              {t(
                "Sẵn sàng phân tích văn bản với AI? Hãy chọn một tính năng bên dưới để bắt đầu.",
                "Ready to analyze text with AI? Pick a feature below to begin."
              )}
            </p>
          </div>
          <div className="dashboard-welcome-actions">
            <button
              onClick={() => setShowUpload(true)}
              className="dashboard-action-btn dashboard-action-primary"
            >
              <span className="dashboard-action-icon">📄</span>
              <span className="dashboard-action-text">
                <strong>{t("Upload tài liệu", "Upload document")}</strong>
                <small>{t("Phân tích ngay", "Analyze now")}</small>
              </span>
              <span className="dashboard-action-arrow">→</span>
            </button>
          </div>
        </section>

        {/* Quick Actions Grid */}
        <section className="dashboard-actions">
          <h2 className="dashboard-section-title">🚀 {t("Khám phá tính năng", "Explore features")}</h2>
          <div className="dashboard-actions-grid">
            <button
              className="dashboard-feature-card"
              onClick={() => setShowUpload(true)}
            >
              <div className="dashboard-feature-icon">🧠</div>
              <h3>{t("Phân tích AI", "AI Analysis")}</h3>
              <p>{t("Phân tích chuyên sâu nội dung, trích xuất thông tin quan trọng", "Deeply analyze content and extract key information")}</p>
              <span className="dashboard-feature-link">
                {t("Bắt đầu", "Start")} <span className="dashboard-feature-arrow">→</span>
              </span>
            </button>

            <button
              className="dashboard-feature-card"
              onClick={() => navigate("/chat")}
            >
              <div className="dashboard-feature-icon">💬</div>
              <h3>{t("Chat với AI", "Chat with AI")}</h3>
              <p>{t("Trò chuyện trực tiếp với tài liệu, hỏi đáp thông minh", "Talk directly with documents and ask smart questions")}</p>
              <span className="dashboard-feature-link">
                {t("Mở chat", "Open chat")} <span className="dashboard-feature-arrow">→</span>
              </span>
            </button>

            <button
              className="dashboard-feature-card"
              onClick={() => navigate("/rewrite")}
            >
              <div className="dashboard-feature-icon">✍️</div>
              <h3>{t("Viết lại", "Rewrite")}</h3>
              <p>{t("Cải thiện văn phong, paraphrasing thông minh", "Improve writing style with smart paraphrasing")}</p>
              <span className="dashboard-feature-link">
                {t("Thử ngay", "Try now")} <span className="dashboard-feature-arrow">→</span>
              </span>
            </button>

            <button
              className="dashboard-feature-card"
              onClick={() => navigate("/history")}
            >
              <div className="dashboard-feature-icon">📚</div>
              <h3>{t("Lịch sử", "History")}</h3>
              <p>{t("Xem lại các lần phân tích và hoạt động trước đó", "Review past analyses and activities")}</p>
              <span className="dashboard-feature-link">
                {t("Xem ngay", "View now")} <span className="dashboard-feature-arrow">→</span>
              </span>
            </button>
          </div>
        </section>

        {/* Recent Documents */}
        <section className="dashboard-documents">
          <div className="dashboard-documents-header">
            <h2 className="dashboard-section-title">📄 {t("Tài liệu gần đây", "Recent documents")}</h2>
            <button
              onClick={() => setShowUpload(true)}
              className="dashboard-add-btn"
            >
              + {t("Thêm mới", "Add new")}
            </button>
          </div>

          {isLoading && (
            <div className="dashboard-loading">
              <div className="dashboard-spinner"></div>
              <p>{t("Đang tải tài liệu...", "Loading documents...")}</p>
            </div>
          )}

          {!isLoading && documents.length === 0 && (
            <div className="dashboard-empty">
              <div className="dashboard-empty-icon">📭</div>
              <h3>{t("Chưa có tài liệu nào", "No documents yet")}</h3>
              <p>{t("Upload tài liệu đầu tiên để bắt đầu phân tích với AI", "Upload your first document to start analyzing with AI")}</p>
              <button onClick={() => setShowUpload(true)} className="dashboard-empty-btn">
                {t("Upload tài liệu", "Upload document")}
              </button>
            </div>
          )}

          {!isLoading && documents.length > 0 && (
            <div className="dashboard-documents-grid">
              {recentDocs.map((doc) => (
                <div
                  key={doc.document_id}
                  className="dashboard-document-card"
                  onClick={() => handleDocumentClick(doc.document_id)}
                >
                  <div className="dashboard-doc-card-header">
                    <span className="dashboard-doc-type">
                      {doc.source_type === "text" && "📝"}
                      {doc.source_type === "url" && "🔗"}
                      {doc.source_type === "file" && "📄"}
                    </span>
                    <button
                      className="dashboard-doc-delete"
                      onClick={(e) => handleDelete(e, doc.document_id)}
                      title={t("Xóa tài liệu", "Delete document")}
                    >
                      🗑️
                    </button>
                  </div>

                  <h4 className="dashboard-doc-title">
                    {doc.title || t("Không có tiêu đề", "Untitled")}
                  </h4>
                  <p className="dashboard-doc-meta">
                    {doc.paragraph_count} {t("đoạn", "paragraphs")} · {new Date(doc.created_at).toLocaleDateString(dateLocale)}
                  </p>

                  <div className="dashboard-doc-actions">
                    <span className="dashboard-doc-action">{t("Đọc tiếp", "Continue reading")} →</span>
                  </div>
                </div>
              ))}

              {documents.length > 4 && (
                <button
                  className="dashboard-view-more"
                  onClick={() => navigate("/history")}
                >
                  <span>{t("Xem tất cả", "View all")} {documents.length} {t("tài liệu", "documents")}</span>
                  <span>→</span>
                </button>
              )}
            </div>
          )}
        </section>

        {/* Stats Section */}
        {documents.length > 0 && (
          <section className="dashboard-stats">
            <div className="dashboard-stat-card">
              <span className="dashboard-stat-icon">📄</span>
              <div className="dashboard-stat-content">
                <span className="dashboard-stat-value">{documents.length}</span>
                <span className="dashboard-stat-label">{t("Tài liệu", "Documents")}</span>
              </div>
            </div>
            <div className="dashboard-stat-card">
              <span className="dashboard-stat-icon">📝</span>
              <div className="dashboard-stat-content">
                <span className="dashboard-stat-value">
                  {documents.reduce((acc, doc) => acc + (doc.paragraph_count || 0), 0)}
                </span>
                <span className="dashboard-stat-label">{t("Đoạn văn", "Paragraphs")}</span>
              </div>
            </div>
            <div className="dashboard-stat-card">
              <span className="dashboard-stat-icon">🌐</span>
              <div className="dashboard-stat-content">
                <span className="dashboard-stat-value">
                  {langFlags[currentLang]}
                </span>
                <span className="dashboard-stat-label">{t("Ngôn ngữ", "Language")}</span>
              </div>
            </div>
          </section>
        )}
      </main>

      {showUpload && (
        <UploadModal
          onClose={() => setShowUpload(false)}
          onSuccess={() => {
            setShowUpload(false);
            fetchDocuments().catch(() => {});
          }}
        />
      )}
    </div>
  );
}

