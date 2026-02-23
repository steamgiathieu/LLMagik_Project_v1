// src/pages/Home.tsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { useDocumentStore } from "@/store/documentStore";
import UploadModal from "@/components/UploadModal";
import "./Home.css";

export default function Home() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { documents, fetchDocuments, deleteDocument, isLoading } = useDocumentStore();
  const [showUpload, setShowUpload] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleDocumentClick = (docId: string) => {
    navigate(`/reader/${docId}`);
  };

  const handleDelete = async (e: React.MouseEvent, docId: string) => {
    e.stopPropagation();
    if (confirm("Xóa tài liệu này?")) {
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
    zh: "🇨🇳",
    ja: "🇯🇵",
    fr: "🇫🇷",
  };

  const recentDocs = documents.slice(0, 4);

  return (
    <div className="dashboard-page">
      {/* ── Top Navigation ── */}
      <header className="dashboard-header">
        <div className="dashboard-header-left">
          <div className="dashboard-brand">
            <span className="dashboard-brand-icon">✨</span>
            <span className="dashboard-brand-name">InfoLen AI</span>
          </div>
        </div>

        <div className="dashboard-header-right">
          <button
            onClick={() => navigate("/history")}
            className="dashboard-header-btn"
            title="Lịch sử hoạt động"
          >
            <span>📊</span> Lịch sử
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
                {langFlags[user?.language || "vi"]} {user?.language?.toUpperCase()}
              </span>
            </div>
          </button>
          <button onClick={handleLogout} className="dashboard-logout-btn" title="Đăng xuất">
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
              Chào {user?.nickname} 👋
            </h1>
            <p className="dashboard-welcome-subtitle">
              Sẵn sàng phân tích văn bản với AI? Hãy chọn một tính năng bên dưới để bắt đầu.
            </p>
          </div>
          <div className="dashboard-welcome-actions">
            <button
              onClick={() => setShowUpload(true)}
              className="dashboard-action-btn dashboard-action-primary"
            >
              <span className="dashboard-action-icon">📄</span>
              <span className="dashboard-action-text">
                <strong>Upload tài liệu</strong>
                <small>Phân tích ngay</small>
              </span>
              <span className="dashboard-action-arrow">→</span>
            </button>
          </div>
        </section>

        {/* Quick Actions Grid */}
        <section className="dashboard-actions">
          <h2 className="dashboard-section-title">🚀 Khám phá tính năng</h2>
          <div className="dashboard-actions-grid">
            <button
              className="dashboard-feature-card"
              onClick={() => setShowUpload(true)}
            >
              <div className="dashboard-feature-icon">🧠</div>
              <h3>Phân tích AI</h3>
              <p>Phân tích chuyên sâu nội dung, trích xuất thông tin quan trọng</p>
              <span className="dashboard-feature-link">
                Bắt đầu <span className="dashboard-feature-arrow">→</span>
              </span>
            </button>

            <button
              className="dashboard-feature-card"
              onClick={() => navigate("/chat")}
            >
              <div className="dashboard-feature-icon">💬</div>
              <h3>Chat với AI</h3>
              <p>Trò chuyện trực tiếp với tài liệu, hỏi đáp thông minh</p>
              <span className="dashboard-feature-link">
                Mở chat <span className="dashboard-feature-arrow">→</span>
              </span>
            </button>

            <button
              className="dashboard-feature-card"
              onClick={() => navigate("/rewrite")}
            >
              <div className="dashboard-feature-icon">✍️</div>
              <h3>Viết lại</h3>
              <p>Cải thiện văn phong, paraphrasing thông minh</p>
              <span className="dashboard-feature-link">
                Thử ngay <span className="dashboard-feature-arrow">→</span>
              </span>
            </button>

            <button
              className="dashboard-feature-card"
              onClick={() => navigate("/history")}
            >
              <div className="dashboard-feature-icon">📚</div>
              <h3>Lịch sử</h3>
              <p>Xem lại các lần phân tích và hoạt động trước đó</p>
              <span className="dashboard-feature-link">
                Xem ngay <span className="dashboard-feature-arrow">→</span>
              </span>
            </button>
          </div>
        </section>

        {/* Recent Documents */}
        <section className="dashboard-documents">
          <div className="dashboard-documents-header">
            <h2 className="dashboard-section-title">📄 Tài liệu gần đây</h2>
            <button
              onClick={() => setShowUpload(true)}
              className="dashboard-add-btn"
            >
              + Thêm mới
            </button>
          </div>

          {isLoading && (
            <div className="dashboard-loading">
              <div className="dashboard-spinner"></div>
              <p>Đang tải tài liệu...</p>
            </div>
          )}

          {!isLoading && documents.length === 0 && (
            <div className="dashboard-empty">
              <div className="dashboard-empty-icon">📭</div>
              <h3>Chưa có tài liệu nào</h3>
              <p>Upload tài liệu đầu tiên để bắt đầu phân tích với AI</p>
              <button onClick={() => setShowUpload(true)} className="dashboard-empty-btn">
                Upload tài liệu
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
                      title="Xóa tài liệu"
                    >
                      🗑️
                    </button>
                  </div>

                  <h4 className="dashboard-doc-title">
                    {doc.title || "Không có tiêu đề"}
                  </h4>
                  <p className="dashboard-doc-meta">
                    {doc.paragraph_count} đoạn · {new Date(doc.created_at).toLocaleDateString("vi-VN")}
                  </p>

                  <div className="dashboard-doc-actions">
                    <span className="dashboard-doc-action">Đọc tiếp →</span>
                  </div>
                </div>
              ))}

              {documents.length > 4 && (
                <button
                  className="dashboard-view-more"
                  onClick={() => navigate("/history")}
                >
                  <span>Xem tất cả {documents.length} tài liệu</span>
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
                <span className="dashboard-stat-label">Tài liệu</span>
              </div>
            </div>
            <div className="dashboard-stat-card">
              <span className="dashboard-stat-icon">📝</span>
              <div className="dashboard-stat-content">
                <span className="dashboard-stat-value">
                  {documents.reduce((acc, doc) => acc + (doc.paragraph_count || 0), 0)}
                </span>
                <span className="dashboard-stat-label">Đoạn văn</span>
              </div>
            </div>
            <div className="dashboard-stat-card">
              <span className="dashboard-stat-icon">🌐</span>
              <div className="dashboard-stat-content">
                <span className="dashboard-stat-value">
                  {langFlags[user?.language || "vi"]}
                </span>
                <span className="dashboard-stat-label">Ngôn ngữ</span>
              </div>
            </div>
          </section>
        )}
      </main>

      {showUpload && (
        <UploadModal
          onClose={() => setShowUpload(false)}
          onSuccess={(docId) => {
            setShowUpload(false);
            navigate(`/reader/${docId}`);
          }}
        />
      )}
    </div>
  );
}
