"use client";

import { useTranslation } from "../context/LanguageContext";

export default function LanguageSwitcher() {
  const { locale, setLocale, languages, t } = useTranslation();

  return (
    <div className="language-switcher-wrapper">
      <label className="language-switcher" htmlFor="terminal-language">
        <svg
          className="language-switcher-icon"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="2" y1="12" x2="22" y2="12" />
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1 4-10z" />
        </svg>
        <select
          id="terminal-language"
          className="language-switcher-select"
          value={locale}
          onChange={(event) => setLocale(event.target.value)}
          aria-label={t("switcher.select_language")}
          title={t("switcher.select_language")}
        >
          {languages.map(({ code }) => (
            <option key={code} value={code}>
              {t(`switcher.${code}`)}
            </option>
          ))}
        </select>
        <span className="language-dropdown-arrow">▼</span>
      </label>
    </div>
  );
}
