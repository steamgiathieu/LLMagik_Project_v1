import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import "./Profile.css";

export default function Profile() {
  const navigate = useNavigate();
  const { user, profile, updateProfile, logout, isLoading } = useAuthStore();

  const [formData, setFormData] = useState({
    language: profile?.language || "vi",
    role: profile?.role || "reader",
    age_group: profile?.age_group || "adult",
  });

  const [message, setMessage] = useState("");

  useEffect(() => {
    if (profile) {
      setFormData({
        language: profile.language,
        role: profile.role,
        age_group: profile.age_group,
      });
    }
  }, [profile]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage("");

    try {
      await updateProfile(formData);
      setMessage("✅ Đã cập nhật hồ sơ");
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
          ← Trang chủ
        </button>
        <h1>Hồ sơ người dùng</h1>
        <button onClick={handleLogout} className="btn-logout">
          Đăng xuất
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
            <h3>Cài đặt</h3>

            <div className="form-group">
              <label htmlFor="language">Ngôn ngữ</label>
              <select
                id="language"
                value={formData.language}
                onChange={(e) => setFormData({ ...formData, language: e.target.value })}
              >
                <option value="vi">Tiếng Việt</option>
                <option value="en">English</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="role">Vai trò</label>
              <select
                id="role"
                value={formData.role}
                onChange={(e) =>
                  setFormData({ ...formData, role: e.target.value as any })
                }
              >
                <option value="reader">Người đọc</option>
                <option value="writer">Người viết</option>
                <option value="both">Cả hai</option>
              </select>
              <p className="form-hint">
                Vai trò mặc định khi phân tích văn bản
              </p>
            </div>

            <div className="form-group">
              <label htmlFor="age_group">Độ tuổi</label>
              <select
                id="age_group"
                value={formData.age_group}
                onChange={(e) => setFormData({ ...formData, age_group: e.target.value })}
              >
                <option value="teen">Thanh thiếu niên (13-18)</option>
                <option value="adult">Người lớn (18+)</option>
                <option value="senior">Cao niên (60+)</option>
              </select>
            </div>

            {message && (
              <div className={`profile-message ${message.startsWith("✅") ? "success" : "error"}`}>
                {message}
              </div>
            )}

            <button type="submit" disabled={isLoading} className="btn-save">
              {isLoading ? "Đang lưu..." : "Lưu thay đổi"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
