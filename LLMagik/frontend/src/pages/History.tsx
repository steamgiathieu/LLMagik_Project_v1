// src/pages/History.tsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useHistoryStore } from "@/store/historyStore";
import { useAuthStore } from "@/store/authStore";
import "./History.css";

export default function History() {
  const navigate = useNavigate();
  useAuthStore();
  const { entries, isLoading, fetchHistory, filter, setFilter } = useHistoryStore();
  const [filteredEntries, setFilteredEntries] = useState(entries);

  useEffect(() => {
    fetchHistory();
  }, []);

  useEffect(() => {
    if (filter === "all") {
      setFilteredEntries(entries);
    } else {
      setFilteredEntries(entries.filter((e) => e.activity_type === filter));
    }
  }, [entries, filter]);

  const getActivityIcon = (type: string) => {
    switch (type) {
      case "analysis":
        return "📊";
      case "rewrite":
        return "✏️";
      case "chat":
        return "💬";
      default:
        return "📝";
    }
  };

  const getActivityLabel = (type: string) => {
    switch (type) {
      case "analysis":
        return "Phân tích";
      case "rewrite":
        return "Viết lại";
      case "chat":
        return "Chat";
      default:
        return "Hoạt động";
    }
  };

  return (
    <div className="history-page">
      <header className="history-header">
        <button onClick={() => navigate("/")} className="btn-back">
          ← Về trang chủ
        </button>
        <h1>Lịch sử hoạt động</h1>
      </header>

      <main className="history-main">
        <div className="history-filters">
          <button
            className={filter === "all" ? "filter-btn active" : "filter-btn"}
            onClick={() => setFilter("all")}
          >
            Tất cả
          </button>
          <button
            className={filter === "analysis" ? "filter-btn active" : "filter-btn"}
            onClick={() => setFilter("analysis")}
          >
            📊 Phân tích
          </button>
          <button
            className={filter === "rewrite" ? "filter-btn active" : "filter-btn"}
            onClick={() => setFilter("rewrite")}
          >
            ✏️ Viết lại
          </button>
          <button
            className={filter === "chat" ? "filter-btn active" : "filter-btn"}
            onClick={() => setFilter("chat")}
          >
            💬 Chat
          </button>
        </div>

        {isLoading && (
          <div className="history-loading">
            <div className="spinner" />
            <p>Đang tải lịch sử...</p>
          </div>
        )}

        {!isLoading && filteredEntries.length === 0 && (
          <div className="history-empty">
            <p>Chưa có hoạt động nào</p>
          </div>
        )}

        <div className="history-list">
          {filteredEntries.map((entry) => (
            <div key={entry.history_id} className="history-item">
              <div className="history-icon">
                {getActivityIcon(entry.activity_type)}
              </div>
              <div className="history-content">
                <h3>
                  {getActivityLabel(entry.activity_type)}
                  {entry.document_title && (
                    <span className="history-doc-title">
                      — {entry.document_title}
                    </span>
                  )}
                </h3>
                <p className="history-timestamp">
                  {new Date(entry.timestamp).toLocaleString("vi-VN")}
                </p>

                {/* Show additional data based on activity type */}
                {entry.activity_type === "analysis" && entry.data.mode && (
                  <p className="history-meta">
                    Chế độ: {entry.data.mode === "reader" ? "Người đọc" : "Người viết"}
                  </p>
                )}

                {entry.activity_type === "rewrite" && entry.data.goal && (
                  <p className="history-meta">Mục tiêu: {entry.data.goal}</p>
                )}

                {entry.activity_type === "chat" && (
                  <p className="history-meta">
                    {entry.data.message_count || 0} tin nhắn
                  </p>
                )}
              </div>

              <button
                className="btn-view-history"
                onClick={() => {
                  if (entry.document_id) {
                    navigate(`/reader/${entry.document_id}`);
                  }
                }}
              >
                Xem
              </button>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
