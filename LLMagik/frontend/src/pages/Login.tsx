// src/pages/Login.tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import "./Login.css";

export default function Login() {
  const navigate = useNavigate();
  const { login, register, isLoading, error, clearError } = useAuthStore();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    nickname: "",
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
            Hiểu sâu hơn về<br />
            <span className="auth-left-highlight">mọi văn bản</span>
          </h2>
          <p className="auth-left-desc">
            Phân tích, tóm tắt, chat và viết lại văn bản với sức mạnh của trí tuệ nhân tạo.
            Hỗ trợ đa ngôn ngữ.
          </p>

          <ul className="auth-features">
            {[
              { icon: "🧠", text: "Phân tích AI chuyên sâu" },
              { icon: "💬", text: "Chat trực tiếp với tài liệu" },
              { icon: "✍️", text: "Viết lại & cải thiện văn phong" },
              { icon: "🌐", text: "Kết quả đa ngôn ngữ" },
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
              Đăng nhập
            </button>
            <button
              className={`auth-tab ${mode === "register" ? "active" : ""}`}
              onClick={() => { setMode("register"); clearError(); }}
            >
              Đăng ký
            </button>
          </div>

          <h1 className="auth-form-title">
            {mode === "login" ? "Chào mừng trở lại 👋" : "Tạo tài khoản mới 🚀"}
          </h1>
          <p className="auth-form-subtitle">
            {mode === "login"
              ? "Đăng nhập để tiếp tục phân tích văn bản"
              : "Miễn phí, không cần thẻ tín dụng"}
          </p>

          <form onSubmit={handleSubmit} className="auth-form" noValidate>
            {/* Username */}
            <div className="auth-field">
              <label htmlFor="username">
                <span className="auth-field-icon">👤</span> Tên đăng nhập
              </label>
              <input
                id="username"
                type="text"
                placeholder="Nhập username..."
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
                    <span className="auth-field-icon">😊</span> Tên hiển thị
                  </label>
                  <input
                    id="nickname"
                    type="text"
                    placeholder="Tên bạn muốn hiển thị..."
                    value={formData.nickname}
                    onChange={update("nickname")}
                    required
                  />
                </div>
              </>
            )}

            {/* Password */}
            <div className="auth-field">
              <label htmlFor="password">
                <span className="auth-field-icon">🔒</span> Mật khẩu
              </label>
              <input
                id="password"
                type="password"
                placeholder={mode === "register" ? "Tối thiểu 6 ký tự..." : "Nhập mật khẩu..."}
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
                  Đang xử lý...
                </span>
              ) : mode === "login" ? (
                "Đăng nhập →"
              ) : (
                "Tạo tài khoản →"
              )}
            </button>
          </form>

          <p className="auth-switch">
            {mode === "login" ? "Chưa có tài khoản?" : "Đã có tài khoản?"}{" "}
            <button
              className="auth-switch-btn"
              onClick={() => { setMode(mode === "login" ? "register" : "login"); clearError(); }}
            >
              {mode === "login" ? "Đăng ký ngay" : "Đăng nhập"}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
