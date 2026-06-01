(function () {
  const params = new URLSearchParams(window.location.search);
  const fromQuery = params.get("api");
  const fromStorage = localStorage.getItem("aura_api_base");
  const fromGlobal = window.AURA_API_BASE;
  const base = (fromQuery || fromStorage || fromGlobal || "http://127.0.0.1:8000").replace(/\/$/, "");
  window.API_BASE = base;
  window.API_V1 = `${base}/api/v1`;
})();
