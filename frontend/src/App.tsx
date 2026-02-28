import { useEffect, useRef } from "react";
import { HashRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { useAuthStore } from "./store/authStore";
import { authApi, tokenHelper } from "@/api/client";
import { applyTheme, getStoredLanguageOrNull, getStoredTheme, saveLanguage } from "@/lib/uiPreferences";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Home from "./pages/Home";
import Reader from "./pages/Reader";
import Rewrite from "./pages/Rewrite";
import Chat from "./pages/Chat";
import History from "./pages/History";
import Profile from "./pages/Profile";
import LanguageSwitcher from "./components/LanguageSwitcher";
import CreditFooter from "./components/CreditFooter";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user } = useAuthStore();
  return user ? <>{children}</> : <Navigate to="/login" />;
}

export default function App() {
  return (
    <HashRouter>
      <AppShell />
    </HashRouter>
  );
}

function AppShell() {
  const { fetchMe, user, logout } = useAuthStore();
  const navigate = useNavigate();
  const initRef = useRef(false);

  useEffect(() => {
    // Restore session on app load (only once)
    if (!initRef.current) {
      initRef.current = true;
      // Only fetch user if token exists (user previously logged in)
      if (tokenHelper.exists()) {
        void fetchMe({ background: true });
      }
    }
  }, []); // Empty dependency - run only once on mount

  useEffect(() => {
    const theme = getStoredTheme();
    applyTheme(theme);
  }, []);

  useEffect(() => {
    const stored = getStoredLanguageOrNull();
    const language = stored || "vi";
    if (!stored) {
      saveLanguage(language);
    }
    document.documentElement.lang = language;
  }, []);

  useEffect(() => {
    // Auto-refresh token every 25 minutes (token expires in 30 minutes)
    if (!user) return;

    const refreshInterval = setInterval(async () => {
      try {
        const res = await authApi.refresh();
        // Update token in localStorage
        tokenHelper.save(res.access_token);
        console.log("Token refreshed successfully");
      } catch (error) {
        console.error("Token refresh failed:", error);
        // Token refresh failed - logout user
        await logout();
        navigate("/login", { replace: true });
      }
    }, 25 * 60 * 1000); // 25 minutes

    return () => clearInterval(refreshInterval);
  }, [user, logout, navigate]);

  useEffect(() => {
    // Listen for logout events (401 from API)
    const handleLogout = () => {
      navigate("/login", { replace: true });
    };
    window.addEventListener("auth:logout", handleLogout);
    return () => window.removeEventListener("auth:logout", handleLogout);
  }, [navigate]);

  return (
    <>
      <Routes>
        <Route path="/landing" element={<Landing />} />
        <Route
          path="/login"
          element={user ? <Navigate to="/" /> : (
            <>
              <Login />
              <LanguageSwitcher />
            </>
          )}
        />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Home />
              <LanguageSwitcher />
            </ProtectedRoute>
          }
        />
        <Route
          path="/reader/:docId"
          element={
            <ProtectedRoute>
              <Reader />
              <LanguageSwitcher />
            </ProtectedRoute>
          }
        />
        <Route
          path="/rewrite"
          element={
            <ProtectedRoute>
              <Rewrite />
              <LanguageSwitcher />
            </ProtectedRoute>
          }
        />
        <Route
          path="/chat"
          element={
            <ProtectedRoute>
              <Chat />
              <LanguageSwitcher />
            </ProtectedRoute>
          }
        />
        <Route
          path="/history"
          element={
            <ProtectedRoute>
              <History />
              <LanguageSwitcher />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Profile />
              <LanguageSwitcher />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
      <CreditFooter />
    </>
  );
}
