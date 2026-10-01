"use client";
import { createContext, useContext, useState, useEffect, useCallback, useMemo } from "react";
import en from "../locales/en.json";
import fr from "../locales/fr.json";
import ar from "../locales/ar.json";

const translations = { en, fr, ar };

export const LANGUAGES = [
  { code: "en", name: "English", label: "EN", flag: "🇺🇸" },
  { code: "fr", name: "Français", label: "FR", flag: "🇫🇷" },
  { code: "ar", name: "العربية", label: "AR", flag: "🇸🇦", dir: "rtl" },
];

const STORAGE_KEY = "terminal_locale";

const EVENT_NAME_KEYS = {
  "US Initial Jobless Claims": "initial_jobless_claims",
  "US Consumer Price Index (CPI)": "consumer_price_index",
  "US Unemployment Rate": "unemployment_rate",
  "US Nonfarm Payrolls (NFP)": "nonfarm_payrolls",
  "Federal Funds Effective Rate": "federal_funds_rate",
  "US Gross Domestic Product (GDP)": "gross_domestic_product",
  "US Retail Sales": "retail_sales",
  "US Producer Price Index (PPI)": "producer_price_index",
  "US JOLTS Job Openings": "jolts_job_openings",
  "US PCE Price Index": "pce_price_index",
  "US Labor Productivity": "labor_productivity",
};

const LanguageContext = createContext({
  locale: "en",
  setLocale: () => {},
  t: (key, replacements) => key,
  isRTL: false,
  languages: LANGUAGES,
});

function getNestedValue(obj, keyPath) {
  if (!obj || !keyPath) return undefined;
  const keys = keyPath.split(".");
  let current = obj;
  for (const k of keys) {
    if (current == null || typeof current !== "object") return undefined;
    current = current[k];
  }
  return current;
}

export function LanguageProvider({ children }) {
  const [locale, setLocaleState] = useState("en");
  const [mounted, setMounted] = useState(false);

  // Restore saved locale on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved && translations[saved]) {
        setLocaleState(saved);
      }
    } catch {
      // LocalStorage unavailable (e.g. security sandbox)
    }
    setMounted(true);
  }, []);

  // Update HTML tag dir and lang attributes when locale changes
  useEffect(() => {
    if (typeof document !== "undefined") {
      const isArabic = locale === "ar";
      document.documentElement.lang = locale;
      document.documentElement.dir = isArabic ? "rtl" : "ltr";
      if (isArabic) {
        document.body.classList.add("rtl");
      } else {
        document.body.classList.remove("rtl");
      }
    }
  }, [locale]);

  const setLocale = useCallback((newLocale) => {
    if (!translations[newLocale]) return;
    setLocaleState(newLocale);
    try {
      localStorage.setItem(STORAGE_KEY, newLocale);
    } catch {
      // Ignore localStorage write failure
    }
  }, []);

  const t = useCallback(
    (keyPath, replacements = {}) => {
      const currentDict = translations[locale] || translations.en;
      let text = getNestedValue(currentDict, keyPath);

      // Fallback to English if missing in selected locale
      if (text === undefined && locale !== "en") {
        text = getNestedValue(translations.en, keyPath);
      }

      if (text === undefined) {
        return keyPath;
      }

      if (typeof text !== "string") {
        return text;
      }

      // Replace variables formatted as {name}
      if (replacements && typeof replacements === "object") {
        return Object.entries(replacements).reduce(
          (acc, [k, v]) => acc.replace(new RegExp(`\\{${k}\\}`, "g"), String(v)),
          text
        );
      }

      return text;
    },
    [locale]
  );

  const isRTL = locale === "ar";

  const contextValue = useMemo(
    () => ({
      locale,
      setLocale,
      t,
      isRTL,
      languages: LANGUAGES,
      mounted,
    }),
    [locale, setLocale, t, isRTL, mounted]
  );

  return (
    <LanguageContext.Provider value={contextValue}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useTranslation() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useTranslation must be used within a LanguageProvider");
  }
  return context;
}

export function localizeEventName(name, t) {
  if (!name || typeof name !== "string") return name;
  const key = EVENT_NAME_KEYS[name.trim()];
  return key ? t(`event_names.${key}`) : name;
}
