import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ChatBox from "@/components/ChatBox";
import { useDocumentStore } from "@/store/documentStore";
import { useChatStore } from "@/store/chatStore";
import { useUiPreferences } from "@/lib/uiPreferences";
import "./Chat.css";

export default function Chat() {
  const navigate = useNavigate();
  const { t, dateLocale } = useUiPreferences();
  const { documents, fetchDocuments, isLoading } = useDocumentStore();
  const { startNewSession } = useChatStore();
  const [selectedDocId, setSelectedDocId] = useState("");

  useEffect(() => {
    fetchDocuments().catch(() => {});
  }, [fetchDocuments]);

  useEffect(() => {
    if (documents.length === 0 || selectedDocId) return;
    setSelectedDocId(documents[0].document_id);
  }, [documents, selectedDocId]);

  useEffect(() => {
    startNewSession();
  }, [selectedDocId, startNewSession]);

  return (
    <div className="chat-page">
      <header className="chat-page-header">
        <button onClick={() => navigate("/")} className="chat-back-btn">
          ← {t("Về trang chủ", "Back home")}
        </button>
        <h1>{t("Chat với AI", "Chat with AI")}</h1>
      </header>

      <div className="chat-page-layout">
        <aside className="chat-page-sidebar">
          <h3>{t("Nguồn ngữ liệu", "Context source")}</h3>
          <p>{t("Bạn có thể chat theo tài liệu đã upload hoặc chuyển sang ngữ liệu tự nhập trong khung chat.", "You can chat using uploaded documents or switch to custom context inside the chat panel.")}</p>

          <label htmlFor="chat-doc-select">{t("Tài liệu mặc định", "Default document")}</label>
          <select
            id="chat-doc-select"
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
            disabled={isLoading || documents.length === 0}
            className="chat-doc-select"
          >
            {documents.length === 0 && (
              <option value="">{t("Chưa có tài liệu", "No documents yet")}</option>
            )}
            {documents.map((doc) => (
              <option key={doc.document_id} value={doc.document_id}>
                {(doc.title || t("Không tiêu đề", "Untitled"))} - {new Date(doc.created_at).toLocaleDateString(dateLocale)}
              </option>
            ))}
          </select>
        </aside>

        <section className="chat-page-main">
          <ChatBox documentId={selectedDocId || undefined} allowCustomContext />
        </section>
      </div>
    </div>
  );
}
