// src/pages/History.tsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useHistoryStore } from "@/store/historyStore";
import { useAuthStore } from "@/store/authStore";
import { useUiPreferences } from "@/lib/uiPreferences";
import "./History.css";

export default function History() {
  const navigate = useNavigate();
  useAuthStore();
  const { t, dateLocale } = useUiPreferences();
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
        return t("Phân tích", "Analysis");
      case "rewrite":
        return t("Viết lại", "Rewrite");
      case "chat":
        return "Chat";
      default:
        return t("Hoạt động", "Activity");
    }
  };

  return (
    <div className="history-page">
      <header className="history-header">
        <button onClick={() => navigate("/")} className="btn-back">
          ← {t("Về trang chủ", "Back home")}
        </button>
        <h1>{t("Lịch sử hoạt động", "Activity history")}</h1>
      </header>

      <main className="history-main">
        <div className="history-filters">
          <button
            className={filter === "all" ? "filter-btn active" : "filter-btn"}
            onClick={() => setFilter("all")}
          >
            {t("Tất cả", "All")}
          </button>
          <button
            className={filter === "analysis" ? "filter-btn active" : "filter-btn"}
            onClick={() => setFilter("analysis")}
          >
            📊 {t("Phân tích", "Analysis")}
          </button>
          <button
            className={filter === "rewrite" ? "filter-btn active" : "filter-btn"}
            onClick={() => setFilter("rewrite")}
          >
            ✏️ {t("Viết lại", "Rewrite")}
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
            <p>{t("Đang tải lịch sử...", "Loading history...")}</p>
          </div>
        )}

        {!isLoading && filteredEntries.length === 0 && (
          <div className="history-empty">
            <p>{t("Chưa có hoạt động nào", "No activity yet")}</p>
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
                  {new Date(entry.timestamp).toLocaleString(dateLocale)}
                </p>

                {/* Show additional data based on activity type */}
                {entry.activity_type === "analysis" && entry.data.mode && (
                  <p className="history-meta">
                    {t("Chế độ", "Mode")}: {entry.data.mode === "reader" ? t("Người đọc", "Reader") : t("Người viết", "Writer")}
                  </p>
                )}

                {entry.activity_type === "rewrite" && entry.data.goal && (
                  <p className="history-meta">{t("Mục tiêu", "Goal")}: {entry.data.goal}</p>
                )}

                {entry.activity_type === "chat" && (
                  <p className="history-meta">
                    {entry.data.message_count || 0} {t("tin nhắn", "messages")}
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
                {t("Xem", "View")}
              </button>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
