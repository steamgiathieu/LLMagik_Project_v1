import { useEffect, useMemo, useState } from "react";

export type SupportedLanguage = "vi" | "en";
export type ThemeMode = "light" | "dark";

const LANGUAGE_KEY = "ui_language";
const THEME_KEY = "ui_theme";
const LANGUAGE_CHANGE_EVENT = "ui:language-changed";

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

export function getStoredLanguageOrNull(): SupportedLanguage | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(LANGUAGE_KEY);
  return raw ? normalizeLanguage(raw) : null;
}

export function saveLanguage(lang: string): SupportedLanguage {
  const normalized = normalizeLanguage(lang);
  if (typeof window !== "undefined") {
    window.localStorage.setItem(LANGUAGE_KEY, normalized);
    window.dispatchEvent(new CustomEvent(LANGUAGE_CHANGE_EVENT, { detail: { language: normalized } }));
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
  const resolveLanguage = () => {
    const stored = getStoredLanguageOrNull();
    return stored || "vi";
  };
  const [language, setLanguage] = useState<SupportedLanguage>(resolveLanguage);

  useEffect(() => {
    setLanguage(resolveLanguage());
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const onLanguageChange = () => setLanguage(resolveLanguage());
    window.addEventListener(LANGUAGE_CHANGE_EVENT, onLanguageChange);
    return () => window.removeEventListener(LANGUAGE_CHANGE_EVENT, onLanguageChange);
  }, []);

  return useMemo(() => {
    const isVi = language === "vi";
    const t = (vi: string, en: string) => (isVi ? vi : en);
    const dateLocale = isVi ? "vi-VN" : "en-US";
    return { language, isVi, t, dateLocale };
  }, [language]);
}
