// src/components/ChatBox.tsx
import { useState } from "react";
import { useChatStore } from "@/store/chatStore";
import "./ChatBox.css";

interface ChatBoxProps {
  documentId: string;
}

export default function ChatBox({ documentId }: ChatBoxProps) {
  const { messages, sendMessage, isLoading, error, clearError } = useChatStore();
  const [input, setInput] = useState("");

  const handleSend = async () => {
    if (!input.trim()) return;

    const question = input;
    setInput("");
    clearError();

    try {
      await sendMessage(documentId, question);
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
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <p>💬 Hỏi về tài liệu hoặc nhắn chào để bắt đầu</p>
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
      </div>

      <div className="chat-input-area">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Hỏi về tài liệu hoặc nhắn 'hello'..."
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
