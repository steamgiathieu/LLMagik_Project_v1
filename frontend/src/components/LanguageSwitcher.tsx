// src/components/LanguageSwitcher.tsx
import { useState } from "react";
import { useAuthStore } from "@/store/authStore";
import "./LanguageSwitcher.css";

const LANGUAGES = [
  { code: "vi", name: "Tiếng Việt", flag: "🇻🇳" },
  { code: "en", name: "English", flag: "🇬🇧" },
  { code: "zh", name: "中文", flag: "🇨🇳" },
  { code: "ja", name: "日本語", flag: "🇯🇵" },
  { code: "fr", name: "Français", flag: "🇫🇷" },
];

export default function LanguageSwitcher() {
  const { user, updateProfile } = useAuthStore();
  const [isOpen, setIsOpen] = useState(false);
  const currentLang = user?.language || "vi";

  const currentLanguage = LANGUAGES.find((lang) => lang.code === currentLang) || LANGUAGES[0];

  const handleLanguageChange = async (langCode: string) => {
    setIsOpen(false);
    try {
      await updateProfile({ language: langCode });
    } catch (error) {
      console.error("Failed to update language:", error);
    }
  };

  return (
    <div className="language-switcher">
      <button
        className="language-switcher-button"
        onClick={() => setIsOpen(!isOpen)}
        title="Change language"
      >
        <span className="language-flag">{currentLanguage.flag}</span>
        <span className="language-code">{currentLanguage.code.toUpperCase()}</span>
      </button>

      {isOpen && (
        <div className="language-dropdown">
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
        </div>
      )}
    </div>
  );
}