// src/components/LanguageSwitcher.tsx
import { useState } from "react";
import { useAuthStore } from "@/store/authStore";
import {
  applyTheme,
  getStoredTheme,
  saveLanguage,
  saveTheme,
  ThemeMode,
  useUiPreferences,
} from "@/lib/uiPreferences";
import "./LanguageSwitcher.css";

const LANGUAGES = [
  { code: "vi", name: "Tiếng Việt", flag: "🇻🇳" },
  { code: "en", name: "English", flag: "🇬🇧" },
];

export default function LanguageSwitcher() {
  const { user, updateProfile } = useAuthStore();
  const { language: currentLang, t } = useUiPreferences();
  const [isOpen, setIsOpen] = useState(false);
  const [theme, setTheme] = useState<ThemeMode>(getStoredTheme());

  const currentLanguage = LANGUAGES.find((lang) => lang.code === currentLang) || LANGUAGES[0];

  const handleLanguageChange = async (langCode: string) => {
    setIsOpen(false);
    const normalized = saveLanguage(langCode);
    document.documentElement.lang = normalized;

    // On login/register screen (not authenticated), only persist locally.
    if (!user) return;

    try {
      await updateProfile({ language: normalized });
    } catch (error) {
      console.error("Failed to update language:", error);
    }
  };

  const handleThemeChange = (nextTheme: ThemeMode) => {
    setTheme(nextTheme);
    saveTheme(nextTheme);
    applyTheme(nextTheme);
  };

  return (
    <div className="language-switcher">
      <button
        className="language-switcher-button"
        onClick={() => setIsOpen(!isOpen)}
        title={t("Tùy chọn giao diện", "UI preferences")}
      >
        <span className="language-flag">{currentLanguage.flag}</span>
        <span className="language-code">{currentLanguage.code.toUpperCase()}</span>
      </button>

      {isOpen && (
        <div className="language-dropdown">
          <div className="language-section-title">{t("Ngôn ngữ giao diện", "UI language")}</div>
          {LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              className={`language-option ${lang.code === currentLang ? "active" : ""}`}
              onClick={() => handleLanguageChange(lang.code)}
            >
              <span className="language-option-flag">{lang.flag}</span>
              <span className="language-option-name">{lang.name}</span>
              {lang.code === currentLang && <span className="language-option-check">✓</span>}
            </button>
          ))}

          <div className="language-section-title theme-title">{t("Độ tương phản", "Contrast mode")}</div>
          <div className="theme-options">
            <button
              className={`theme-option ${theme === "light" ? "active" : ""}`}
              onClick={() => handleThemeChange("light")}
            >
              {t("Light", "Light")}
            </button>
            <button
              className={`theme-option ${theme === "dark" ? "active" : ""}`}
              onClick={() => handleThemeChange("dark")}
            >
              {t("Dark", "Dark")}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
