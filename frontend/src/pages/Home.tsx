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

  return (
    <div className="home-page">
      <header className="home-header">
        <h1>InfoLen AI</h1>
        <div className="home-header-right">
          <span className="user-badge">{user?.nickname}</span>
          <button onClick={() => navigate("/history")} className="btn-secondary">
            Lịch sử
          </button>
          <button onClick={handleLogout} className="btn-secondary">
            Đăng xuất
          </button>
        </div>
      </header>

      <main className="home-main">
        <div className="home-hero">
          <h2>Phân tích văn bản thông minh</h2>
          <p>Upload văn bản để bắt đầu phân tích với AI</p>
          <button onClick={() => setShowUpload(true)} className="btn-primary-large">
            + Upload văn bản
          </button>
        </div>

        <section className="documents-section">
          <h3>Tài liệu của bạn ({documents.length})</h3>

          {isLoading && <p className="loading">Đang tải...</p>}

          {!isLoading && documents.length === 0 && (
            <p className="empty-state">Chưa có tài liệu nào. Upload để bắt đầu!</p>
          )}

          <div className="documents-grid">
            {documents.map((doc) => (
              <div
                key={doc.document_id}
                className="document-card"
                onClick={() => handleDocumentClick(doc.document_id)}
              >
                <div className="doc-card-header">
                  <span className={`doc-type doc-type-${doc.source_type}`}>
                    {doc.source_type === "text" && "📝"}
                    {doc.source_type === "url" && "🔗"}
                    {doc.source_type === "file" && "📄"}
                  </span>
                  <button
                    className="doc-delete"
                    onClick={(e) => handleDelete(e, doc.document_id)}
                    title="Xóa"
                  >
                    ×
                  </button>
                </div>

                <h4 className="doc-title">{doc.title || "Không có tiêu đề"}</h4>
                <p className="doc-meta">
                  {doc.paragraph_count} đoạn · {new Date(doc.created_at).toLocaleDateString("vi-VN")}
                </p>
              </div>
            ))}
          </div>
        </section>
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
