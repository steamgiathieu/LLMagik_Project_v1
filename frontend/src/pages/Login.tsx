// src/pages/Login.tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { useUiPreferences } from "@/lib/uiPreferences";
import "./Login.css";

export default function Login() {
  const navigate = useNavigate();
  const { login, register, isLoading, error, clearError } = useAuthStore();
  const { t } = useUiPreferences();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    nickname: "",
    language: "vi",
    age_group: "adult",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    try {
      if (mode === "login") {
        await login(formData.username, formData.password);
      } else {
        await register({
          username: formData.username,
          email: formData.email,
          password: formData.password,
          nickname: formData.nickname,
          language: formData.language,
          age_group: formData.age_group,
        });
      }
      navigate("/");
    } catch (_) {
      // Error already set in store
    }
  };

  const update = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setFormData((prev) => ({ ...prev, [field]: e.target.value }));

  return (
    <div className="auth-page">
      {/* ── Left panel: branding ── */}
      <div className="auth-left">
        <div className="auth-left-content">
          <div className="auth-brand">
            <div className="auth-brand-icon">✨</div>
            <span className="auth-brand-name">InfoLen AI</span>
          </div>

          <h2 className="auth-left-title">
            {t("Hiểu sâu hơn về", "Understand")}<br />
            <span className="auth-left-highlight">{t("mọi văn bản", "every text")}</span>
          </h2>
          <p className="auth-left-desc">
            {t(
              "Phân tích, tóm tắt, chat và viết lại văn bản với sức mạnh của trí tuệ nhân tạo. Hỗ trợ đa ngôn ngữ.",
              "Analyze, summarize, chat and rewrite text with AI power. Multilingual support."
            )}
          </p>

          <ul className="auth-features">
            {[
              { icon: "🧠", text: t("Phân tích AI chuyên sâu", "Deep AI analysis") },
              { icon: "💬", text: t("Chat trực tiếp với tài liệu", "Chat directly with documents") },
              { icon: "✍️", text: t("Viết lại & cải thiện văn phong", "Rewrite and improve writing style") },
              { icon: "🌐", text: t("Kết quả đa ngôn ngữ", "Multilingual outputs") },
            ].map((f) => (
              <li key={f.text} className="auth-feature-item">
                <span className="auth-feature-icon">{f.icon}</span>
                <span>{f.text}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* ── Right panel: form ── */}
      <div className="auth-right">
        <div className="auth-form-wrap">
          {/* Tabs */}
          <div className="auth-tabs">
            <button
              className={`auth-tab ${mode === "login" ? "active" : ""}`}
              onClick={() => { setMode("login"); clearError(); }}
            >
              {t("Đăng nhập", "Sign in")}
            </button>
            <button
              className={`auth-tab ${mode === "register" ? "active" : ""}`}
              onClick={() => { setMode("register"); clearError(); }}
            >
              {t("Đăng ký", "Register")}
            </button>
          </div>

          <h1 className="auth-form-title">
            {mode === "login" ? t("Chào mừng trở lại 👋", "Welcome back 👋") : t("Tạo tài khoản mới 🚀", "Create a new account 🚀")}
          </h1>
          <p className="auth-form-subtitle">
            {mode === "login"
              ? t("Đăng nhập để tiếp tục phân tích văn bản", "Sign in to continue analyzing your text")
              : t("Miễn phí, không cần thẻ tín dụng", "Free to use, no credit card required")}
          </p>

          <form onSubmit={handleSubmit} className="auth-form" noValidate>
            {/* Username */}
            <div className="auth-field">
              <label htmlFor="username">
                <span className="auth-field-icon">👤</span> {t("Tên đăng nhập", "Username")}
              </label>
              <input
                id="username"
                type="text"
                placeholder={t("Nhập username...", "Enter username...")}
                value={formData.username}
                onChange={update("username")}
                required
                autoComplete="username"
                autoFocus
              />
            </div>

            {/* Register-only fields */}
            {mode === "register" && (
              <>
                <div className="auth-field">
                  <label htmlFor="email">
                    <span className="auth-field-icon">📧</span> Email
                  </label>
                  <input
                    id="email"
                    type="email"
                    placeholder="your@email.com"
                    value={formData.email}
                    onChange={update("email")}
                    required
                    autoComplete="email"
                  />
                </div>

                <div className="auth-field">
                  <label htmlFor="nickname">
                    <span className="auth-field-icon">😊</span> {t("Tên hiển thị", "Display name")}
                  </label>
                  <input
                    id="nickname"
                    type="text"
                    placeholder={t("Tên bạn muốn hiển thị...", "Name to show...")}
                    value={formData.nickname}
                    onChange={update("nickname")}
                    required
                  />
                </div>

                <div className="auth-field">
                  <label htmlFor="language">
                    <span className="auth-field-icon">🌐</span> {t("Ngôn ngữ phản hồi", "Output language")}
                  </label>
                  <select
                    id="language"
                    value={formData.language}
                    onChange={update("language")}
                    required
                  >
                    <option value="vi">Tiếng Việt</option>
                    <option value="en">English</option>
                    <option value="zh">中文</option>
                    <option value="ja">日本語</option>
                    <option value="fr">Français</option>
                  </select>
                </div>

                <div className="auth-field">
                  <label htmlFor="age_group">
                    <span className="auth-field-icon">🎂</span> {t("Độ tuổi", "Age group")}
                  </label>
                  <select
                    id="age_group"
                    value={formData.age_group}
                    onChange={update("age_group")}
                    required
                  >
                    <option value="teen">{t("Thanh thiếu niên (13-18)", "Teen (13-18)")}</option>
                    <option value="adult">{t("Người lớn (18+)", "Adult (18+)")}</option>
                    <option value="senior">{t("Cao niên (60+)", "Senior (60+)")}</option>
                  </select>
                </div>
              </>
            )}

            {/* Password */}
            <div className="auth-field">
              <label htmlFor="password">
                <span className="auth-field-icon">🔒</span> {t("Mật khẩu", "Password")}
              </label>
              <input
                id="password"
                type="password"
                placeholder={mode === "register" ? t("Tối thiểu 6 ký tự...", "At least 6 characters...") : t("Nhập mật khẩu...", "Enter password...")}
                value={formData.password}
                onChange={update("password")}
                required
                minLength={6}
                autoComplete={mode === "login" ? "current-password" : "new-password"}
              />
            </div>

            {/* Error */}
            {error && (
              <div className="auth-error">
                <span>⚠️</span> {error}
              </div>
            )}

            {/* Submit */}
            <button type="submit" disabled={isLoading} className="auth-submit">
              {isLoading ? (
                <span className="auth-loading">
                  <span className="auth-spinner" />
                  {t("Đang xử lý...", "Processing...")}
                </span>
              ) : mode === "login" ? (
                `${t("Đăng nhập", "Sign in")} →`
              ) : (
                `${t("Tạo tài khoản", "Create account")} →`
              )}
            </button>
          </form>

          <p className="auth-switch">
            {mode === "login" ? t("Chưa có tài khoản?", "No account yet?") : t("Đã có tài khoản?", "Already have an account?")}{" "}
            <button
              className="auth-switch-btn"
              onClick={() => { setMode(mode === "login" ? "register" : "login"); clearError(); }}
            >
              {mode === "login" ? t("Đăng ký ngay", "Register now") : t("Đăng nhập", "Sign in")}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
