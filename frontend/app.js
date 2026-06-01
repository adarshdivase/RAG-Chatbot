/** Aura Enterprise RAG — demo-ready client */

const DEMO_QUESTIONS = [
  "What is explainable AI (XAI) and why does it matter?",
  "Compare cloud MLOps platforms on AWS, Azure, and GCP.",
  "What are best practices for scalable ML model deployment?",
  "What ethical considerations apply to generative AI?",
  "How does Kubernetes support cloud-native MLOps?",
];

const state = {
  sessionId: sessionStorage.getItem("aura_session") || `sess_${crypto.randomUUID().slice(0, 12)}`,
  loading: false,
  transcript: [],
  backendReady: false,
};

sessionStorage.setItem("aura_session", state.sessionId);

function headers(json = true) {
  const h = {};
  if (json) h["Content-Type"] = "application/json";
  const key = localStorage.getItem("aura_api_key");
  if (key) h["X-API-Key"] = key;
  return h;
}

async function api(path, options = {}) {
  const url = path.startsWith("http") ? path : `${window.API_V1}${path}`;
  const isForm = options.body instanceof FormData;
  const res = await fetch(url, {
    ...options,
    headers: { ...headers(!isForm && options.method !== "GET"), ...options.headers },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const err = await res.json();
      detail = err.detail;
      if (typeof detail === "object") detail = detail.message || JSON.stringify(detail);
    } catch (_) {}
    throw new Error(typeof detail === "string" ? detail : "Request failed");
  }
  return res.json();
}

function el(id) {
  return document.getElementById(id);
}

function escapeHtml(text) {
  const d = document.createElement("div");
  d.textContent = text;
  return d.innerHTML;
}

function renderMarkdown(text) {
  let html = escapeHtml(text);
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
  html = html.replace(/^- (.+)$/gm, "<li>$1</li>");
  if (html.includes("<li>")) html = `<ul>${html}</ul>`;
  html = html.replace(/\n/g, "<br>");
  return html;
}

function setIndexingBanner(show, text) {
  const banner = el("indexing-banner");
  if (text) el("indexing-text").textContent = text;
  banner.classList.toggle("hidden", !show);
}

function addMessage(content, role, meta = {}) {
  const wrap = document.createElement("div");
  wrap.className = `msg ${role}`;
  wrap.innerHTML = role === "bot" ? renderMarkdown(content) : escapeHtml(content);

  if (meta.latency_ms) {
    const m = document.createElement("div");
    m.className = "msg-meta";
    m.textContent = `${meta.model || "model"} · ${meta.latency_ms}ms`;
    wrap.appendChild(m);
  }

  if (meta.sources?.length) {
    const details = document.createElement("details");
    details.className = "sources";
    details.innerHTML = `<summary>${meta.sources.length} source(s)</summary>`;
    meta.sources.forEach((s) => {
      const card = document.createElement("div");
      card.className = "source-card";
      card.innerHTML = `<strong>${escapeHtml(s.title)}</strong><p>${escapeHtml(s.snippet)}</p>`;
      details.appendChild(card);
    });
    wrap.appendChild(details);
  }

  el("messages").appendChild(wrap);
  el("messages").scrollTop = el("messages").scrollHeight;

  state.transcript.push({
    role,
    content,
    sources: meta.sources,
    time: new Date().toISOString(),
  });
}

function setLoading(on) {
  state.loading = on;
  el("send-btn").disabled = on || !state.backendReady;
  el("user-input").disabled = on || !state.backendReady;
  el("loading").classList.toggle("hidden", !on);
  document.querySelectorAll(".suggestion-chip").forEach((b) => (b.disabled = on || !state.backendReady));
}

function setSuggestionsEnabled(enabled) {
  document.querySelectorAll(".suggestion-chip").forEach((b) => (b.disabled = !enabled));
  el("send-btn").disabled = !enabled || state.loading;
  el("user-input").disabled = !enabled || state.loading;
}

async function pollReady(maxAttempts = 40) {
  setIndexingBanner(true, "Indexing knowledge base — first startup may take up to a minute…");
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const res = await fetch(`${window.API_BASE}/ready`);
      if (res.ok) {
        const data = await res.json();
        setIndexingBanner(false);
        return data;
      }
      if (res.status === 503) {
        const err = await res.json().catch(() => ({}));
        const d = err.detail || {};
        if (d.chunk_count > 0) {
          setIndexingBanner(true, `Finishing setup… ${d.chunk_count} chunks indexed`);
        }
      }
    } catch (_) {
      setIndexingBanner(true, "Waiting for API to start…");
    }
    await new Promise((r) => setTimeout(r, 2000));
  }
  setIndexingBanner(true, "Still starting — check GOOGLE_API_KEY in backend/.env");
  return null;
}

async function checkHealth() {
  const pill = el("status-pill");
  const label = pill.querySelector("span:last-child");

  try {
    const live = await fetch(`${window.API_BASE}/live`);
    if (!live.ok) throw new Error("API down");

    const readyRes = await fetch(`${window.API_BASE}/ready`);
    if (readyRes.ok) {
      const ready = await readyRes.json();
      state.backendReady = true;
      pill.className = "status-pill online";
      label.textContent = "Connected";
      el("stat-docs").textContent = ready.document_count;
      el("stat-chunks").textContent = ready.chunk_count;
      el("stat-sessions").textContent = ready.active_sessions;
      setIndexingBanner(false);
      setSuggestionsEnabled(true);
      return true;
    }

    if (readyRes.status === 503) {
      pill.className = "status-pill offline";
      label.textContent = "Indexing…";
      state.backendReady = false;
      setSuggestionsEnabled(false);
      setIndexingBanner(true);
      return false;
    }
  } catch (_) {}

  pill.className = "status-pill offline";
  label.textContent = "Offline";
  state.backendReady = false;
  setSuggestionsEnabled(false);
  return false;
}

async function loadDocuments() {
  const list = el("doc-list");
  if (!state.backendReady) {
    list.innerHTML = '<li class="muted">Connect to API to load files</li>';
    return;
  }
  try {
    const data = await api("/documents");
    list.innerHTML = "";
    if (!data.documents.length) {
      list.innerHTML = '<li class="muted">No documents — upload or add files to data/</li>';
      return;
    }
    data.documents.forEach((d) => {
      const li = document.createElement("li");
      li.innerHTML = `<span>${escapeHtml(d.filename)}</span><span>${(d.size_bytes / 1024).toFixed(0)} KB</span>`;
      list.appendChild(li);
    });
  } catch (e) {
    list.innerHTML = `<li class="muted">${escapeHtml(e.message)}</li>`;
  }
}

async function sendMessage(textOverride) {
  const input = el("user-input");
  const text = (textOverride || input.value).trim();
  if (!text || state.loading || !state.backendReady) return;

  addMessage(text, "user");
  input.value = "";
  setLoading(true);

  try {
    const data = await api("/chat", {
      method: "POST",
      body: JSON.stringify({ message: text, session_id: state.sessionId, include_sources: true }),
    });
    addMessage(data.response, "bot", {
      sources: data.sources,
      latency_ms: data.latency_ms,
      model: data.model,
    });
  } catch (e) {
    addMessage(`Error: ${e.message}`, "error");
  } finally {
    setLoading(false);
  }
}

async function reindex() {
  if (!confirm("Reindex the entire knowledge base? All chat sessions will be reset.")) return;
  setLoading(true);
  setIndexingBanner(true, "Reindexing all documents…");
  try {
    const data = await api("/documents/reindex", { method: "POST" });
    addMessage(`Reindexed ${data.documents_loaded} documents (${data.chunks_indexed} chunks) in ${data.duration_ms}ms.`, "bot");
    await loadDocuments();
    await checkHealth();
  } catch (e) {
    addMessage(`Reindex failed: ${e.message}`, "error");
  } finally {
    setLoading(false);
    setIndexingBanner(false);
  }
}

async function uploadFile(file) {
  setLoading(true);
  setIndexingBanner(true, `Uploading ${file.name} and reindexing…`);
  const fd = new FormData();
  fd.append("file", file);
  try {
    const key = localStorage.getItem("aura_api_key");
    const h = {};
    if (key) h["X-API-Key"] = key;
    const res = await fetch(`${window.API_V1}/documents/upload`, { method: "POST", body: fd, headers: h });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Upload failed");
    }
    const data = await res.json();
    addMessage(data.message, "bot");
    await loadDocuments();
    await checkHealth();
  } catch (e) {
    addMessage(`Upload failed: ${e.message}`, "error");
  } finally {
    setLoading(false);
    setIndexingBanner(false);
    el("file-input").value = "";
  }
}

async function clearSession() {
  try {
    await api(`/sessions/${state.sessionId}`, { method: "DELETE" });
  } catch (_) {}
  state.sessionId = `sess_${crypto.randomUUID().slice(0, 12)}`;
  sessionStorage.setItem("aura_session", state.sessionId);
  el("session-label").textContent = state.sessionId;
  state.transcript = [];
  el("messages").innerHTML = "";
  showWelcome();
}

function showWelcome() {
  addMessage(
    "Welcome to **Aura Enterprise**. Ask about MLOps, deployment, or ethics — or click a suggested question below. Every answer includes **source citations** from your knowledge base.",
    "bot"
  );
}

function exportChat() {
  if (!state.transcript.length) {
    alert("No messages to export.");
    return;
  }
  let md = `# Aura Enterprise Chat Export\n\nSession: ${state.sessionId}\nExported: ${new Date().toISOString()}\n\n---\n\n`;
  state.transcript.forEach((m) => {
    const who = m.role === "user" ? "You" : m.role === "bot" ? "Aura" : "System";
    md += `## ${who}\n\n${m.content}\n\n`;
    if (m.sources?.length) {
      md += "**Sources:**\n";
      m.sources.forEach((s, i) => {
        md += `${i + 1}. ${s.title} — ${s.snippet}\n`;
      });
      md += "\n";
    }
  });
  const blob = new Blob([md], { type: "text/markdown" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `aura-chat-${state.sessionId}.md`;
  a.click();
  URL.revokeObjectURL(a.href);
}

function renderSuggestions() {
  const container = el("suggestions");
  container.innerHTML = "";
  DEMO_QUESTIONS.forEach((q) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "suggestion-chip";
    btn.textContent = q.length > 48 ? q.slice(0, 45) + "…" : q;
    btn.title = q;
    btn.disabled = true;
    btn.addEventListener("click", () => sendMessage(q));
    container.appendChild(btn);
  });
}

function initTheme() {
  const saved = localStorage.getItem("aura_theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);
}

function toggleTheme() {
  const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("aura_theme", next);
}

async function bootstrap() {
  initTheme();
  renderSuggestions();
  el("session-label").textContent = state.sessionId;

  el("send-btn").addEventListener("click", () => sendMessage());
  el("user-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  el("reindex-btn").addEventListener("click", reindex);
  el("upload-btn").addEventListener("click", () => el("file-input").click());
  el("export-btn").addEventListener("click", exportChat);
  el("clear-btn").addEventListener("click", clearSession);
  el("theme-toggle").addEventListener("click", toggleTheme);
  el("file-input").addEventListener("change", (e) => {
    if (e.target.files[0]) uploadFile(e.target.files[0]);
  });

  el("api-url").value = localStorage.getItem("aura_api_base") || window.API_BASE;
  el("api-key").value = localStorage.getItem("aura_api_key") || "";
  el("save-config").addEventListener("click", () => {
    localStorage.setItem("aura_api_base", el("api-url").value.replace(/\/$/, ""));
    localStorage.setItem("aura_api_key", el("api-key").value);
    location.reload();
  });

  showWelcome();
  setSuggestionsEnabled(false);

  const ready = await pollReady();
  if (ready) {
    await checkHealth();
    await loadDocuments();
  } else {
    await checkHealth();
  }

  setInterval(checkHealth, 12000);
}

document.addEventListener("DOMContentLoaded", bootstrap);
