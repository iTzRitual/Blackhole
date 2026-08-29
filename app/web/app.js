(() => {
  "use strict";

  const viewNames = ["capture", "attention", "memory", "ask"];
  const memorySections = [
    ["subscriptions", "Subscriptions", "Current price and status, with history below."],
    ["subscription_history", "Price history", "Earlier supported values are kept as history."],
    ["tasks", "Tasks", "Owners, deadlines, cancellation, and reassignment."],
    ["services", "Recurring costs", "Observed totals and periods without invented zeros."],
    ["merchants", "Purchases", "Directly observed purchase facts only."],
    ["unknown", "Still unknown", "Missing or unresolved information stays explicit."],
    ["recent_changes", "Recent changes", "Corrections and material changes with evidence."],
    ["duplicates", "Duplicates", "Duplicate counts and linked captures."],
  ];

  const $ = (selector) => document.querySelector(selector);
  const escapeHtml = (value) => String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

  const pretty = (value) => String(value || "")
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());

  const formatValue = (value) => {
    if (value === null || value === undefined) return "—";
    if (typeof value === "boolean") return value ? "Yes" : "No";
    if (Array.isArray(value)) return value.length ? value.map(formatValue).join(", ") : "—";
    if (typeof value === "object") {
      const amount = value.amount ?? value.total;
      if (amount !== undefined) {
        const money = `${amount} ${value.currency || ""}`.trim();
        const period = value.billing_period ? ` / ${value.billing_period}` : "";
        return `${money}${period}`;
      }
      return Object.entries(value).map(([key, item]) => `${pretty(key)}: ${formatValue(item)}`).join(" · ");
    }
    return String(value);
  };

  const assertionHtml = (item, attention = false) => {
    const status = item.knowledge_status || "unknown";
    const value = status === "unknown"
      ? `Unknown · ${pretty(item.unknown_reason || "missing")}`
      : formatValue(item.value);
    const refs = Array.isArray(item.source_refs) && item.source_refs.length
      ? `Evidence ${item.source_refs.join(", ")}`
      : "No source reference";
    return `<article class="assertion${attention ? " is-attention" : ""}">
      <div class="assertion-head"><span class="assertion-name">${escapeHtml(pretty(item.subject))} · ${escapeHtml(pretty(item.predicate))}</span><span class="status-tag ${escapeHtml(status)}">${escapeHtml(status)}</span></div>
      <p class="assertion-value${status === "unknown" ? " is-unknown" : ""}">${escapeHtml(value)}</p>
      <div class="assertion-meta"><span class="evidence">${escapeHtml(refs)}</span></div>
    </article>`;
  };

  const renderList = (element, assertions, emptyText, attention = false) => {
    if (!assertions || !assertions.length) {
      element.innerHTML = `<div class="empty-state"><span class="empty-icon">✓</span><p>${escapeHtml(emptyText)}</p></div>`;
      return;
    }
    element.innerHTML = assertions.map((item) => assertionHtml(item, attention)).join("");
  };

  const renderProvider = (provider) => {
    const element = $("#provider-status");
    element.textContent = provider?.available ? "Codex CLI available" : "Codex CLI not detected";
    element.title = provider?.message || "Provider status is informational only.";
    element.classList.toggle("is-ready", Boolean(provider?.available));
  };

  const renderCaptures = (captures) => {
    const element = $("#recent-captures");
    if (!captures || !captures.length) {
      element.innerHTML = `<div class="empty-state"><span class="empty-icon">∅</span><p>No captures yet.</p></div>`;
      return;
    }
    element.innerHTML = captures.map((capture) => `<div class="capture-row">
      <span class="capture-seq">#${escapeHtml(capture.sequence)}</span>
      <div><p class="capture-text">${escapeHtml(capture.text || "Untitled capture")}</p><div class="capture-date">${escapeHtml(capture.observed_at || "date unknown")} · ${escapeHtml(capture.source_type || "source")}</div></div>
    </div>`).join("");
  };

  const renderState = (state) => {
    renderProvider(state.provider);
    renderCaptures(state.recent_captures);
    const attention = state.attention || [];
    $("#attention-count").textContent = attention.length;
    $("#nav-attention").textContent = attention.length || "";
    $("#capture-count").textContent = `${state.counts?.captures || 0} captures`;
    renderList($("#attention-list"), attention, "Nothing needs attention right now.", true);

    const memory = state.memory || {};
    $("#memory-sections").innerHTML = memorySections.map(([key, title, description]) => `<section class="memory-section">
      <h3>${escapeHtml(title)}</h3><p>${escapeHtml(description)}</p><div id="memory-${escapeHtml(key)}"></div>
    </section>`).join("");
    memorySections.forEach(([key]) => renderList($(`#memory-${key}`), memory[key] || [], "No supported observations here."));
  };

  const api = async (url, options = {}) => {
    const response = await fetch(url, { headers: { "Content-Type": "application/json" }, ...options });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Request failed");
    return payload;
  };

  const refreshState = async () => {
    const payload = await api("/api/state");
    renderState(payload.state);
  };

  const showView = (name) => {
    viewNames.forEach((view) => {
      const active = view === name;
      const element = $(`#view-${view}`);
      element.hidden = !active;
      element.classList.toggle("is-active", active);
      $(`.nav-item[data-view="${view}"]`).classList.toggle("is-active", active);
    });
  };

  document.querySelectorAll(".nav-item").forEach((button) => button.addEventListener("click", () => showView(button.dataset.view)));
  document.querySelectorAll(".example-chip").forEach((button) => button.addEventListener("click", () => {
    $("#capture-input").value = button.dataset.example || "";
    $("#capture-input").focus();
  }));

  $("#file-input").addEventListener("change", async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const feedback = $("#capture-feedback");
    if (file.size > 256 * 1024) {
      feedback.textContent = "Choose a text file under 256 KB for this demo.";
      feedback.classList.add("is-error");
      event.target.value = "";
      return;
    }
    try {
      $("#capture-input").value = await file.text();
      $("#capture-input").dataset.filename = file.name;
      feedback.textContent = `${file.name} ready to save.`;
      feedback.classList.remove("is-error");
    } catch (_error) {
      feedback.textContent = "That file could not be read as text.";
      feedback.classList.add("is-error");
    }
  });

  $("#capture-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const input = $("#capture-input");
    const feedback = $("#capture-feedback");
    const button = event.submitter;
    if (!input.value.trim()) return;
    button.disabled = true;
    feedback.textContent = "";
    feedback.classList.remove("is-error");
    try {
      await api("/api/capture", { method: "POST", body: JSON.stringify({ text: input.value, source_type: input.dataset.filename ? "document" : "text", filename: input.dataset.filename || null }) });
      feedback.textContent = "Saved.";
      input.value = "";
      delete input.dataset.filename;
      $("#file-input").value = "";
      await refreshState();
    } catch (error) {
      feedback.textContent = error.message;
      feedback.classList.add("is-error");
    } finally {
      button.disabled = false;
    }
  });

  $("#reset-demo").addEventListener("click", async () => {
    if (!window.confirm("Reset the local demo to its seeded state?")) return;
    const feedback = $("#capture-feedback");
    try {
      await api("/api/reset", { method: "POST", body: "{}" });
      feedback.textContent = "Demo reset.";
      feedback.classList.remove("is-error");
      await refreshState();
    } catch (error) {
      feedback.textContent = error.message;
      feedback.classList.add("is-error");
    }
  });

  const ask = async (question) => {
    if (!question.trim()) return;
    const output = $("#answer-output");
    output.innerHTML = `<div class="empty-state"><span class="empty-icon">…</span><p>Looking at the current state.</p></div>`;
    try {
      const payload = await api(`/api/query?q=${encodeURIComponent(question)}`);
      const answer = payload.answer;
      output.innerHTML = `<p class="answer-heading">${escapeHtml(answer.mode.replaceAll("_", " "))}</p>${answer.sections.map((section) => `<section class="answer-section"><h3>${escapeHtml(section.title)}</h3>${section.assertions.map((item) => assertionHtml(item)).join("") || `<div class="empty-state"><p>No supported observations.</p></div>`}</section>`).join("")}`;
    } catch (error) {
      output.innerHTML = `<div class="empty-state"><span class="empty-icon">!</span><p>${escapeHtml(error.message)}</p></div>`;
    }
  };

  $("#ask-form").addEventListener("submit", (event) => {
    event.preventDefault();
    ask($("#ask-input").value);
  });
  document.querySelectorAll(".question-chip").forEach((button) => button.addEventListener("click", () => {
    $("#ask-input").value = button.dataset.question || "";
    ask($("#ask-input").value);
  }));

  refreshState().catch((error) => {
    $("#capture-feedback").textContent = error.message;
    $("#capture-feedback").classList.add("is-error");
  });
})();
