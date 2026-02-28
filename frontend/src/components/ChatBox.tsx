// src/components/ChatBox.tsx
import { useState } from "react";
import { useChatStore } from "@/store/chatStore";
import { useUiPreferences } from "@/lib/uiPreferences";
import "./ChatBox.css";

interface ChatBoxProps {
  documentId?: string;
  allowCustomContext?: boolean;
}

export default function ChatBox({ documentId, allowCustomContext = true }: ChatBoxProps) {
  const { t } = useUiPreferences();
  const { messages, sendMessage, isLoading, error, clearError, startNewSession } = useChatStore();
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<"document" | "custom">(documentId ? "document" : "custom");
  const [contextText, setContextText] = useState("");
  const [localError, setLocalError] = useState("");

  const handleSend = async () => {
    if (!input.trim()) return;
    const usingDocument = mode === "document" && !!documentId;
    if (!usingDocument && contextText.trim().length < 10) {
      setLocalError(t("Vui lòng nhập ngữ liệu ít nhất 10 ký tự", "Please provide at least 10 characters of context"));
      return;
    }

    const question = input;
    setInput("");
    clearError();
    setLocalError("");

    try {
      await sendMessage({
        question,
        documentId: usingDocument ? documentId : undefined,
        contextText: usingDocument ? undefined : contextText,
      });
    } catch (err) {
      // Error already set in store
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-box">
      {allowCustomContext && (
        <div className="chat-context-panel">
          <div className="chat-context-modes">
            <button
              className={mode === "document" ? "active" : ""}
              disabled={!documentId}
              onClick={() => {
                setMode("document");
                setLocalError("");
                clearError();
                startNewSession();
              }}
            >
              {t("Theo tài liệu", "Use document")}
            </button>
            <button
              className={mode === "custom" ? "active" : ""}
              onClick={() => {
                setMode("custom");
                setLocalError("");
                clearError();
                startNewSession();
              }}
            >
              {t("Ngữ liệu tự nhập", "Custom context")}
            </button>
          </div>

          {mode === "custom" && (
            <textarea
              value={contextText}
              onChange={(e) => setContextText(e.target.value)}
              disabled={isLoading}
              rows={3}
              className="chat-context-textarea"
              placeholder={t(
                "Dán ngữ liệu muốn AI dựa vào để trả lời...",
                "Paste the source text that AI should use to answer..."
              )}
            />
          )}
        </div>
      )}

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <p>{t("💬 Hỏi AI để bắt đầu hội thoại", "💬 Ask AI to start the conversation")}</p>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.message_id} className={`chat-message chat-${msg.role}`}>
            <div className="chat-content">
              <p>{msg.content}</p>

              {msg.role === "assistant" && msg.referenced_paragraphs && msg.referenced_paragraphs.length > 0 && (
                <div className="chat-references">
                  <small>
                    📌 Tham khảo: {msg.referenced_paragraphs.join(", ")}
                  </small>
                </div>
              )}

              {msg.role === "assistant" && msg.out_of_scope && (
                <div className="chat-out-of-scope">
                  <small>⚠️ Câu hỏi ngoài phạm vi tài liệu</small>
                </div>
              )}

              {msg.role === "assistant" && msg.confidence && (
                <div className="chat-confidence">
                  <small>🎯 Độ tin cậy: {msg.confidence}</small>
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="chat-message chat-assistant">
            <div className="chat-loading">
              <div className="spinner-small" />
              <p>Đang suy nghĩ...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="chat-error">
            <p>❌ {error}</p>
          </div>
        )}
        {localError && (
          <div className="chat-error">
            <p>❌ {localError}</p>
          </div>
        )}
      </div>

      <div className="chat-input-area">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={t("Nhập câu hỏi của bạn...", "Type your question...")}
          rows={2}
          disabled={isLoading}
            className="chat-textarea"
        />
        <button
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
          className="btn-send"
        >
          {isLoading ? "..." : "Gửi"}
        </button>
      </div>
    </div>
  );
}
