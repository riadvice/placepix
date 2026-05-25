/**
 * PlacePix i18n Engine
 * - localStorage preference takes priority on return visits
 * - First visit: auto-detect from navigator.language
 * - Falls back to 'en' for unknown/partial locales
 * - Toggles <html dir="rtl"> for Arabic
 * - Marks active language in the selector
 */
(function () {
  'use strict';

  const STORAGE_KEY = 'placepix_lang';
  const DEFAULT_LANG = 'en';
  const RTL_LANGS = ['ar'];

  const SUPPORTED = [
    'ar', 'bn', 'zh-CN', 'zh-TW', 'cs', 'nl', 'en', 'fil',
    'fr', 'de', 'el', 'hi', 'id', 'it', 'ja', 'ko',
    'no', 'pl', 'pt-BR', 'pt-PT', 'ru', 'es', 'sv',
    'th', 'tr', 'uk', 'vi'
  ];

  let _translations = {};
  let _currentLang = DEFAULT_LANG;

  /**
   * Resolve the best matching supported language code for a browser locale string.
   * e.g. "zh-Hans-CN" -> "zh-CN", "pt-BR" -> "pt-BR", "fr-BE" -> "fr"
   */
  function _resolve(raw) {
    if (!raw) return null;
    const norm = raw.trim();
    // Exact match first
    if (SUPPORTED.includes(norm)) return norm;
    // Try known sub-tags (pt-BR, zh-CN, zh-TW)
    const lower = norm.toLowerCase();
    if (lower.startsWith('zh')) {
      if (lower.includes('tw') || lower.includes('hant')) return 'zh-TW';
      return 'zh-CN';
    }
    if (lower.startsWith('pt')) {
      if (lower.includes('br')) return 'pt-BR';
      return 'pt-PT';
    }
    // Generic base language match (e.g. "fr-BE" -> "fr")
    const base = norm.split('-')[0];
    if (SUPPORTED.includes(base)) return base;
    return null;
  }

  /**
   * Detect language: localStorage first, then navigator preferences, then default.
   */
  function _detect() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && SUPPORTED.includes(stored)) return stored;

    const candidates = navigator.languages
      ? Array.from(navigator.languages)
      : [navigator.language || ''];

    for (const lang of candidates) {
      const resolved = _resolve(lang);
      if (resolved) return resolved;
    }
    return DEFAULT_LANG;
  }

  /**
   * Fetch a locale JSON file. Returns {} on failure.
   */
  async function _fetch(lang) {
    try {
      const resp = await fetch(`/static/locales/${lang}.json?v=1`);
      if (!resp.ok) throw new Error(resp.status);
      return await resp.json();
    } catch (_) {
      return {};
    }
  }

  /**
   * Apply loaded translations to all [data-i18n] elements.
   */
  function _apply(translations) {
    _translations = translations;

    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      const val = translations[key];
      if (!val) return;
      // data-i18n-attr lets us translate attributes like placeholder, title, aria-label
      const attr = el.getAttribute('data-i18n-attr');
      if (attr) {
        el.setAttribute(attr, val);
      } else {
        el.textContent = val;
      }
    });

    // Update <html lang> and dir
    document.documentElement.lang = _currentLang;
    document.documentElement.dir = RTL_LANGS.includes(_currentLang) ? 'rtl' : 'ltr';

    // Mark active language in the selector
    document.querySelectorAll('[data-lang]').forEach(el => {
      el.classList.toggle('lang-active', el.getAttribute('data-lang') === _currentLang);
    });

    // Update trigger button label
    const trigger = document.getElementById('lang-trigger-label');
    if (trigger && LANG_META[_currentLang]) {
      const m = LANG_META[_currentLang];
      trigger.innerHTML = `<span class="fi fi-${m.flag}" style="border-radius:2px;"></span> ${m.native}`;
    }
  }

  /**
   * Public: switch language, persist, and re-apply.
   */
  async function setLanguage(lang) {
    if (!SUPPORTED.includes(lang)) return;
    _currentLang = lang;
    localStorage.setItem(STORAGE_KEY, lang);

    // Close dropdown immediately on selection, before async fetch
    const dd = document.getElementById('lang-dropdown');
    if (dd) dd.classList.remove('lang-dd-open');
    const btn = document.getElementById('lang-trigger');
    if (btn) btn.setAttribute('aria-expanded', 'false');

    let data = await _fetch(lang);
    // If locale file is essentially empty or missing keys, fall back to English
    if (!data || Object.keys(data).length < 5) {
      data = await _fetch(DEFAULT_LANG);
    }
    _apply(data);
  }

  /**
   * Reveal the body (called after translations applied, or on timeout).
   */
  function _reveal() {
    document.body.classList.add('i18n-ready');
  }

  /**
   * Initialize: detect language and apply on DOM ready.
   */
  async function init() {
    // Safety: always reveal within 800ms even if fetch fails (locale files are tiny)
    const safetyTimer = setTimeout(_reveal, 800);

    _currentLang = _detect();

    if (_currentLang === DEFAULT_LANG) {
      // English — no fetch needed, just reveal
      const data = await _fetch(DEFAULT_LANG);
      _apply(data);
    } else {
      const data = await _fetch(_currentLang);
      if (Object.keys(data).length >= 5) {
        _apply(data);
      } else {
        _apply(await _fetch(DEFAULT_LANG));
      }
    }

    clearTimeout(safetyTimer);
    _reveal();
  }

  // Language metadata: flag ISO code + native name
  const LANG_META = {
    'ar':    { flag: 'sa', native: 'العربية' },
    'bn':    { flag: 'bd', native: 'বাংলা' },
    'zh-CN': { flag: 'cn', native: '中文 (简体)' },
    'zh-TW': { flag: 'tw', native: '中文 (繁體)' },
    'cs':    { flag: 'cz', native: 'Čeština' },
    'nl':    { flag: 'nl', native: 'Nederlands' },
    'en':    { flag: 'gb', native: 'English' },
    'fil':   { flag: 'ph', native: 'Filipino' },
    'fr':    { flag: 'fr', native: 'Français' },
    'de':    { flag: 'de', native: 'Deutsch' },
    'el':    { flag: 'gr', native: 'Ελληνικά' },
    'hi':    { flag: 'in', native: 'हिन्दी' },
    'id':    { flag: 'id', native: 'Bahasa Indonesia' },
    'it':    { flag: 'it', native: 'Italiano' },
    'ja':    { flag: 'jp', native: '日本語' },
    'ko':    { flag: 'kr', native: '한국어' },
    'no':    { flag: 'no', native: 'Norsk' },
    'pl':    { flag: 'pl', native: 'Polski' },
    'pt-BR': { flag: 'br', native: 'Português (Brasil)' },
    'pt-PT': { flag: 'pt', native: 'Português (Portugal)' },
    'ru':    { flag: 'ru', native: 'Русский' },
    'es':    { flag: 'es', native: 'Español' },
    'sv':    { flag: 'se', native: 'Svenska' },
    'th':    { flag: 'th', native: 'ไทย' },
    'tr':    { flag: 'tr', native: 'Türkçe' },
    'uk':    { flag: 'ua', native: 'Українська' },
    'vi':    { flag: 'vn', native: 'Tiếng Việt' },
  };

  /**
   * Public: get translation by key
   */
  function get(key) {
    return _translations[key] || key;
  }

  // Expose globally
  window.i18n = { init, setLanguage, get, LANG_META, SUPPORTED };

  // Auto-init when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
