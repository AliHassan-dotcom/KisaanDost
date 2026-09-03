const API_PREFIX = "/api/v1";

const i18n = {
  en: {
    greeting: "Good day, farmer",
    weather: "Weather",
    farmHealth: "Farm Health",
    market: "Market Rates",
    satellite: "Satellite Status",
    quickActions: "Quick Actions",
    scanCrop: "Scan crop",
    pestAlerts: "Pest alerts",
    settings: "Settings",
    logout: "Logout",
    login: "Login",
    save: "Save",
    submit: "Submit",
    loading: "Loading...",
    error: "Something went wrong",
    mock: "Offline preview",
    live: "Live",
    uncertain: "Uncertain result",
    advisoryDisclaimer: "Always consult an extension worker before applying pesticides.",
  },
  ur: {
    greeting: "خوش آمدید، کسان",
    weather: "موسم",
    farmHealth: "فصل کی صحت",
    market: "منڈی کے بھاؤ",
    satellite: "سیٹلائٹ حالت",
    quickActions: "فوری اقدامات",
    scanCrop: "فصل سکین کریں",
    pestAlerts: "کیڑے الرٹ",
    settings: "ترتیبات",
    logout: "لاگ آؤٹ",
    login: "لاگ ان",
    save: "محفوظ کریں",
    submit: "جمع کرائیں",
    loading: "لوڈ ہو رہا ہے...",
    error: "کچھ غلط ہو گیا",
    mock: "آف لائن پیش نظارہ",
    live: "براہ راست",
    uncertain: "غیر یقینی نتیجہ",
    advisoryDisclaimer: "کسی بھی کیڑے مار دوا لگانے سے پہلے مقامی توسیع کارکن سے مشورہ کریں۔",
  },
};

function getToken() {
  return localStorage.getItem("kd_token") || "";
}

function setLanguage(lang) {
  localStorage.setItem("kd_lang", lang);
  document.body.classList.toggle("ur", lang === "ur");
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (i18n[lang][key]) el.textContent = i18n[lang][key];
  });
}

function getLanguage() {
  return localStorage.getItem("kd_lang") || "en";
}

async function apiFetch(path, options = {}) {
  const url = `${API_PREFIX}${path}`;
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const resp = await fetch(url, { ...options, headers });
  if (resp.status === 401) {
    localStorage.removeItem("kd_token");
    window.location.href = "/login.html";
    return null;
  }
  return resp;
}

function showError(container, message) {
  const el = document.createElement("div");
  el.className = "error";
  el.textContent = message || i18n[getLanguage()].error;
  container.innerHTML = "";
  container.appendChild(el);
}

function statusPill(status, isMock) {
  const cls = isMock ? "status-mock" : "status-live";
  const label = isMock ? i18n[getLanguage()].mock : i18n[getLanguage()].live;
  return `<span class="status-pill ${cls}">${label}</span>`;
}

function renderNav(active) {
  const html = `
    <nav class="nav">
      <a href="/" class="${active === "home" ? "active" : ""}">🏠<br><span data-i18n="greeting">Home</span></a>
      <a href="/scan.html" class="${active === "scan" ? "active" : ""}">📷<br><span data-i18n="scanCrop">Scan</span></a>
      <a href="/weather.html" class="${active === "weather" ? "active" : ""}">🌤<br><span data-i18n="weather">Weather</span></a>
      <a href="/settings.html" class="${active === "settings" ? "active" : ""}">⚙️<br><span data-i18n="settings">Settings</span></a>
    </nav>
  `;
  const nav = document.createElement("div");
  nav.innerHTML = html;
  document.body.appendChild(nav);
}

function bindLanguageSelect() {
  const sel = document.getElementById("lang");
  if (!sel) return;
  sel.value = getLanguage();
  sel.addEventListener("change", (e) => setLanguage(e.target.value));
}

function logout() {
  localStorage.removeItem("kd_token");
  window.location.href = "/login.html";
}

(function init() {
  setLanguage(getLanguage());
  bindLanguageSelect();
})();
