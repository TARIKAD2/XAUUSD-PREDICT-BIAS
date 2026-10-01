"use client";

import { LanguageProvider } from "../context/LanguageContext";

export default function Providers({ children }) {
  return <LanguageProvider>{children}</LanguageProvider>;
}
