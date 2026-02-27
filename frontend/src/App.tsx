import { useEffect, useRef } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "./store/authStore";
import { authApi, tokenHelper } from "@/api/client";
import { applyTheme, getStoredLanguage, getStoredTheme, normalizeLanguage, saveLanguage } from "@/lib/uiPreferences";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Home from "./pages/Home";
import Reader from "./pages/Reader";
import History from "./pages/History";
import Profile from "./pages/Profile";
import LanguageSwitcher from "./components/LanguageSwitcher";
import CreditFooter from "./components/CreditFooter";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user } = useAuthStore();
  return user ? <>{children}</> : <Navigate to="/login" />;
}

export default function App() {
  const { fetchMe, user, profile, logout, updateProfile } = useAuthStore();
  const initRef = useRef(false);

  useEffect(() => {
    // Restore session on app load (only once)
    if (!initRef.current) {
      initRef.current = true;
      // Only fetch user if token exists (user previously logged in)
      if (tokenHelper.exists()) {
        fetchMe();
      }
    }
  }, []); // Empty dependency - run only once on mount

  useEffect(() => {
    const theme = getStoredTheme();
    applyTheme(theme);
  }, []);

  useEffect(() => {
    const language = normalizeLanguage(profile?.language || user?.language || getStoredLanguage());
    saveLanguage(language);
    document.documentElement.lang = language;
  }, [profile?.language, user?.language]);

  useEffect(() => {
    if (!profile?.language) return;
    const normalized = normalizeLanguage(profile.language);
    if (profile.language !== normalized) {
      updateProfile({ language: normalized }).catch(() => {});
    }
  }, [profile?.language, updateProfile]);

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
        window.location.href = "/login";
      }
    }, 25 * 60 * 1000); // 25 minutes

    return () => clearInterval(refreshInterval);
  }, [user, logout]);

  useEffect(() => {
    // Listen for logout events (401 from API)
    const handleLogout = () => {
      window.location.href = "/login";
    };
    window.addEventListener("auth:logout", handleLogout);
    return () => window.removeEventListener("auth:logout", handleLogout);
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/landing" element={<Landing />} />
        <Route path="/login" element={user ? <Navigate to="/" /> : <Login />} />
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
      </Routes>
      <CreditFooter />
    </BrowserRouter>
  );
}
