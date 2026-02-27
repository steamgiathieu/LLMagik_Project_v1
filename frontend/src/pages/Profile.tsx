import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { useUiPreferences } from "@/lib/uiPreferences";
import "./Profile.css";

export default function Profile() {
  const navigate = useNavigate();
  const { user, profile, updateProfile, logout, fetchMe, isLoading } = useAuthStore();
  const { t } = useUiPreferences();

  const [formData, setFormData] = useState({
    language: profile?.language || user?.language || "vi",
    role: profile?.role || "reader",
    age_group: profile?.age_group || "adult",
  });

  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!profile) {
      fetchMe();
    }
  }, [profile, fetchMe]);

  useEffect(() => {
    if (profile) {
      setFormData({
        language: profile.language,
        role: profile.role,
        age_group: profile.age_group,
      });
      return;
    }

    if (user?.language) {
      setFormData((prev) => ({ ...prev, language: user.language ?? "vi" }));
    }
  }, [profile, user?.language]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage("");

    try {
      await updateProfile(formData);
      setMessage(t("✅ Đã cập nhật hồ sơ", "✅ Profile updated"));
    } catch (err: any) {
      setMessage("❌ " + err.message);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <div className="profile-page">
      <header className="profile-header">
        <button onClick={() => navigate("/")} className="btn-back">
          ← {t("Trang chủ", "Home")}
        </button>
        <h1>{t("Hồ sơ người dùng", "User profile")}</h1>
        <button onClick={handleLogout} className="btn-logout">
          {t("Đăng xuất", "Sign out")}
        </button>
      </header>

      <main className="profile-main">
        <div className="profile-card">
          <div className="profile-info">
            <div className="profile-avatar">
              {user?.nickname.charAt(0).toUpperCase()}
            </div>
            <div>
              <h2>{user?.nickname}</h2>
              <p className="profile-email">{user?.email}</p>
              <p className="profile-username">@{user?.username}</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="profile-form">
            <h3>{t("Cài đặt", "Settings")}</h3>

            <div className="form-group">
              <label htmlFor="language">🌐 {t("Ngôn ngữ nhận kết quả phân tích", "Language for system outputs")}</label>
              <select
                id="language"
                value={formData.language}
                onChange={(e) => setFormData({ ...formData, language: e.target.value })}
              >
                <option value="vi">🇻🇳 Tiếng Việt</option>
                <option value="en">🇬🇧 English</option>
                <option value="zh">🇨🇳 中文 (Chinese)</option>
                <option value="ja">🇯🇵 日本語 (Japanese)</option>
                <option value="fr">🇫🇷 Français (French)</option>
              </select>
              <p className="form-hint">{t("AI sẽ trả lời phân tích, chat và viết lại bằng ngôn ngữ này", "AI analysis, chat and rewrite outputs follow this language")}</p>
            </div>

            <div className="form-group">
              <label htmlFor="role">{t("Vai trò", "Role")}</label>
              <select
                id="role"
                value={formData.role}
                onChange={(e) =>
                  setFormData({ ...formData, role: e.target.value as any })
                }
              >
                <option value="reader">{t("Người đọc", "Reader")}</option>
                <option value="writer">{t("Người viết", "Writer")}</option>
                <option value="both">{t("Cả hai", "Both")}</option>
              </select>
              <p className="form-hint">
                {t("Vai trò mặc định khi phân tích văn bản", "Default role when analyzing text")}
              </p>
            </div>

            <div className="form-group">
              <label htmlFor="age_group">{t("Độ tuổi", "Age group")}</label>
              <select
                id="age_group"
                value={formData.age_group}
                onChange={(e) => setFormData({ ...formData, age_group: e.target.value })}
              >
                <option value="teen">{t("Thanh thiếu niên (13-18)", "Teen (13-18)")}</option>
                <option value="adult">{t("Người lớn (18+)", "Adult (18+)")}</option>
                <option value="senior">{t("Cao niên (60+)", "Senior (60+)")}</option>
              </select>
            </div>

            {message && (
              <div className={`profile-message ${message.startsWith("✅") ? "success" : "error"}`}>
                {message}
              </div>
            )}

            <button type="submit" disabled={isLoading} className="btn-save">
              {isLoading ? t("Đang lưu...", "Saving...") : t("Lưu thay đổi", "Save changes")}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
