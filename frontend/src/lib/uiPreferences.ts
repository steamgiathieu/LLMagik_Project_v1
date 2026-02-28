import { useMemo } from "react";
import { useAuthStore } from "@/store/authStore";

export type SupportedLanguage = "vi" | "en";
export type ThemeMode = "light" | "dark";

const LANGUAGE_KEY = "ui_language";
const THEME_KEY = "ui_theme";

const SUPPORTED_LANGUAGES: SupportedLanguage[] = ["vi", "en"];

export function normalizeLanguage(value?: string | null): SupportedLanguage {
  if (!value) return "vi";
  const code = value.toLowerCase() as SupportedLanguage;
  return SUPPORTED_LANGUAGES.includes(code) ? code : "vi";
}

export function getStoredLanguage(): SupportedLanguage {
  if (typeof window === "undefined") return "vi";
  return normalizeLanguage(window.localStorage.getItem(LANGUAGE_KEY));
}

export function saveLanguage(lang: string): SupportedLanguage {
  const normalized = normalizeLanguage(lang);
  if (typeof window !== "undefined") {
    window.localStorage.setItem(LANGUAGE_KEY, normalized);
  }
  return normalized;
}

export function getStoredTheme(): ThemeMode {
  if (typeof window === "undefined") return "light";
  const value = window.localStorage.getItem(THEME_KEY);
  return value === "dark" ? "dark" : "light";
}

export function saveTheme(theme: ThemeMode): ThemeMode {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(THEME_KEY, theme);
  }
  return theme;
}

export function applyTheme(theme: ThemeMode): void {
  if (typeof document === "undefined") return;
  document.documentElement.setAttribute("data-theme", theme);
}

export function useUiPreferences() {
  const { profile, user } = useAuthStore();
  return useMemo(() => {
    const language = normalizeLanguage(profile?.language || user?.language || getStoredLanguage());
    const isVi = language === "vi";
    const t = (vi: string, en: string) => (isVi ? vi : en);
    const dateLocale = isVi ? "vi-VN" : "en-US";
    return { language, isVi, t, dateLocale };
  }, [profile?.language, user?.language]);
}
