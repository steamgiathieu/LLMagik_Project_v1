// src/components/Navbar.tsx
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import "./Navbar.css";

export default function Navbar() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <h1 onClick={() => navigate("/")} className="brand-title">
          TextAnalyzer
        </h1>
      </div>

      <div className="navbar-content">
        <div className="navbar-user">
          {user && (
            <>
              <span className="user-name">{user.nickname}</span>
              <button
                onClick={() => navigate("/profile")}
                className="nav-link"
              >
                ⚙️ Hồ sơ
              </button>
              <button
                onClick={() => navigate("/history")}
                className="nav-link"
              >
                📊 Lịch sử
              </button>
              <button onClick={() => logout()} className="nav-link logout">
                Đăng xuất
              </button>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
