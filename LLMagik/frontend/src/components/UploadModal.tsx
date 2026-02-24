// src/components/UploadModal.tsx
import { useState } from "react";
import { textsApi } from "@/api/client";
import "./UploadModal.css";

interface UploadModalProps {
  onClose: () => void;
  onSuccess: (documentId: string) => void;
}

export default function UploadModal({ onClose, onSuccess }: UploadModalProps) {
  const [mode, setMode] = useState<"text" | "url" | "file">("text");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Text mode
  const [text, setText] = useState("");

  // URL mode
  const [url, setUrl] = useState("");

  // File mode
  const [file, setFile] = useState<File | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      let response: any;

      if (mode === "text") {
        if (!text.trim()) {
          throw new Error("Vui lòng nhập văn bản");
        }
        response = await textsApi.uploadText({ text });
      } else if (mode === "url") {
        if (!url.trim()) {
          throw new Error("Vui lòng nhập URL");
        }
        response = await textsApi.uploadUrl({ url });
      } else if (mode === "file") {
        if (!file) {
          throw new Error("Vui lòng chọn file");
        }
        response = await textsApi.uploadFile(file);
      }

      onSuccess(response.document_id);
    } catch (err: any) {
      setError(err.message || "Có lỗi xảy ra");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-modal-overlay" onClick={onClose}>
      <div className="upload-modal" onClick={(e) => e.stopPropagation()}>
        <header className="upload-modal-header">
          <h2>Upload Văn bản</h2>
          <button className="btn-close" onClick={onClose}>
            ×
          </button>
        </header>

        <div className="upload-tabs">
          <button
            className={mode === "text" ? "active" : ""}
            onClick={() => setMode("text")}
          >
            📝 Văn bản
          </button>
          <button
            className={mode === "url" ? "active" : ""}
            onClick={() => setMode("url")}
          >
            🔗 URL
          </button>
          <button
            className={mode === "file" ? "active" : ""}
            onClick={() => setMode("file")}
          >
            📄 File
          </button>
        </div>

        <form onSubmit={handleSubmit} className="upload-form">
          {mode === "text" && (
            <textarea
              placeholder="Dán văn bản của bạn tại đây..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={6}
              className="upload-textarea"
            />
          )}

          {mode === "url" && (
            <input
              type="url"
              placeholder="https://example.com/article"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="upload-input"
            />
          )}

          {mode === "file" && (
            <div className="upload-file-area">
              <input
                type="file"
                accept=".pdf,.docx,.doc"
                onChange={(e) => setFile(e.currentTarget.files?.[0] || null)}
                className="upload-file-input"
              />
              <p className="upload-file-hint">Hỗ trợ: PDF, DOCX (tối đa 10MB)</p>
              {file && <p className="upload-file-name">✓ {file.name}</p>}
            </div>
          )}

          {error && <div className="upload-error">{error}</div>}

          <div className="upload-actions">
            <button type="button" onClick={onClose} className="btn-secondary">
              Hủy
            </button>
            <button type="submit" disabled={loading} className="btn-primary">
              {loading ? "Đang xử lý..." : "Upload"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
