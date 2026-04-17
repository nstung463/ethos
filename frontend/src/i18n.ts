import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import LanguageDetector from "i18next-browser-languagedetector";

import en from "./locales/en.json";
import vi from "./locales/vi.json";
// import ja from "./locales/ja.json";
// import es from "./locales/es.json";
// import fr from "./locales/fr.json";

const resources = {
  en: { translation: en },
  vi: { translation: vi },
  // ja: { translation: ja },
  // es: { translation: es },
  // fr: { translation: fr },
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: "en",
    interpolation: {
      escapeValue: false, // react already safes from xss
    },
  });

export default i18n;
