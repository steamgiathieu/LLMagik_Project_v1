import { useEffect, useRef, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { useAuthStore } from "./store/authStore";
import { authApi, tokenHelper } from "@/api/client";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Home from "./pages/Home";
import Reader from "./pages/Reader";
import History from "./pages/History";
import Profile from "./pages/Profile";
import Rewrite from "./pages/Rewrite";
import LanguageSwitcher from "./components/LanguageSwitcher";

function LoginRouteGate() {
  const { user } = useAuthStore();
  const location = useLocation();

  if (!user) return <Login />;

  const params = new URLSearchParams(location.search);
  const next = params.get("next");
  const safeNext = next && next.startsWith("/") ? next : "/";
  return <Navigate to={safeNext} replace />;
}

function ProtectedRoute({
  children,
  authReady,
}: {
  children: React.ReactNode;
  authReady: boolean;
}) {
  const location = useLocation();
  const { user, isLoading } = useAuthStore();

  if (!authReady || isLoading) {
    return (
      <div style={{ padding: 24, textAlign: "center" }}>
        Đang khôi phục phiên đăng nhập...
      </div>
    );
  }

  if (!user) {
    const next = encodeURIComponent(`${location.pathname}${location.search}`);
    return <Navigate to={`/login?next=${next}`} replace />;
  }

  return <>{children}</>;
}

export default function App() {
  const { fetchMe, user, logout } = useAuthStore();
  const initRef = useRef(false);
  const [authReady, setAuthReady] = useState(false);

  useEffect(() => {
    // Restore session on app load (only once)
    if (!initRef.current) {
      initRef.current = true;

      const bootstrap = async () => {
        // Only fetch user if token exists (user previously logged in)
        if (tokenHelper.exists()) {
          try {
            await fetchMe();
          } finally {
            setAuthReady(true);
          }
          return;
        }
        setAuthReady(true);
      };

      bootstrap();
    }
  }, []); // Empty dependency - run only once on mount

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
        <Route path="/login" element={<LoginRouteGate />} />
        <Route
          path="/"
          element={
            <ProtectedRoute authReady={authReady}>
              <Home />
              <LanguageSwitcher />
            </ProtectedRoute>
          }
        />
        <Route
          path="/reader/:docId"
          element={
            <ProtectedRoute authReady={authReady}>
              <Reader />
              <LanguageSwitcher />
            </ProtectedRoute>
          }
        />
        <Route
          path="/rewrite"
          element={
            <ProtectedRoute authReady={authReady}>
              <Rewrite />
              <LanguageSwitcher />
            </ProtectedRoute>
          }
        />
        <Route
          path="/history"
          element={
            <ProtectedRoute authReady={authReady}>
              <History />
              <LanguageSwitcher />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute authReady={authReady}>
              <Profile />
              <LanguageSwitcher />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
