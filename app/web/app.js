(() => {
  "use strict";

  const viewNames = ["capture", "attention", "memory", "ask"];
  const storageKey = "blackhole.ui.v1";
  const maxAttachmentBytes = 10 * 1024 * 1024;
  const textPreviewBytes = 256 * 1024;
  const milestones = [10, 25, 50, 100, 250, 500, 1000];
  const memorySections = [
    ["subscriptions", "Subscriptions", "Current prices and status, with history when supported."],
    ["subscription_history", "Price history", "Earlier supported values remain visible as history."],
    ["tasks", "Tasks", "Owners, deadlines, and lifecycle changes that are known."],
    ["services", "Bills", "Observed totals and periods without invented zeros."],
    ["merchants", "Purchases", "Directly observed purchase facts."],
    ["recent_changes", "Recent changes", "Corrections, replacements, and material changes."],
    ["duplicates", "Repeated captures", "Duplicate evidence is kept understandable."],
    ["unknown", "Still unknown", "Missing or unresolved information stays explicit."],
  ];

  const $ = (selector, parent = document) => parent.querySelector(selector);
  const $$ = (selector, parent = document) => [...parent.querySelectorAll(selector)];
  const escapeHtml = (value) => String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

  const pretty = (value) => String(value ?? "")
    .replace(/^capture:/, "")
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());

  const formatValue = (value) => {
    if (value === null || value === undefined || value === "") return "—";
    if (typeof value === "boolean") return value ? "Yes" : "No";
    if (Array.isArray(value)) return value.length ? value.map(formatValue).join(", ") : "—";
    if (typeof value === "object") {
      const amount = value.amount ?? value.total;
      if (amount !== undefined) {
        const money = `${amount} ${value.currency || ""}`.trim();
        const period = value.billing_period ? ` / ${value.billing_period}` : "";
        return `${money}${period}`;
      }
      return Object.entries(value)
        .filter(([key]) => !["source_event_id", "target_event_id"].includes(key))
        .map(([key, item]) => `${pretty(key)}: ${formatValue(item)}`)
        .join(" · ") || "—";
    }
    return String(value);
  };

  const readLocalState = () => {
    try {
      const parsed = JSON.parse(window.localStorage.getItem(storageKey) || "{}");
      return {
        localCaptureCount: Number.isFinite(parsed.localCaptureCount) ? parsed.localCaptureCount : 0,
        celebrated: Array.isArray(parsed.celebrated) ? parsed.celebrated : [],
      };
    } catch (_error) {
      return { localCaptureCount: 0, celebrated: [] };
    }
  };

  const localState = readLocalState();
  const state = {
    activeView: "capture",
    attachment: null,
    objectUrl: null,
    installPrompt: null,
    hasRemoteState: false,
    toastTimer: null,
    milestoneTimer: null,
  };

  const persistLocalState = () => {
    try {
      window.localStorage.setItem(storageKey, JSON.stringify({
        localCaptureCount: localState.localCaptureCount,
        celebrated: localState.celebrated,
      }));
    } catch (_error) {
      // Local persistence is a convenience only; capture behavior must still work.
    }
  };

  const setConnectionStatus = (text, mode = "", title = "") => {
    const element = $("#connection-status");
    element.textContent = text;
    element.title = title || text;
    element.classList.toggle("is-online", mode === "online");
    element.classList.toggle("is-offline", mode === "offline");
  };

  const showToast = (message, kind = "") => {
    const region = $("#toast-region");
    window.clearTimeout(state.toastTimer);
    region.innerHTML = `<div class="toast${kind ? ` is-${escapeHtml(kind)}` : ""}" role="status">${escapeHtml(message)}</div>`;
    state.toastTimer = window.setTimeout(() => { region.innerHTML = ""; }, kind === "error" ? 5200 : 3600);
  };

  const setFeedback = (message, kind = "") => {
    const element = $("#capture-feedback");
    element.textContent = message;
    element.className = `inline-feedback${kind ? ` is-${kind}` : ""}`;
  };

  const api = async (url, options = {}) => {
    const response = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    let payload;
    try {
      payload = await response.json();
    } catch (_error) {
      throw new Error("The local demo returned an unreadable response.");
    }
    if (!response.ok) throw new Error(payload.error || "Request failed");
    return payload;
  };

  const statusTag = (status) => {
    const normalized = ["known", "inferred", "unknown"].includes(status) ? status : "unknown";
    return `<span class="status-tag ${normalized}">${escapeHtml(normalized)}</span>`;
  };

  const sourceText = (item) => {
    const refs = Array.isArray(item.source_refs) && item.source_refs.length
      ? `Evidence ${item.source_refs.join(", ")}`
      : "No source reference";
    return refs;
  };

  const cardValue = (item) => {
    const status = item.knowledge_status || "unknown";
    if (status === "unknown") return `Unknown · ${pretty(item.unknown_reason || "not yet known")}`;
    return formatValue(item.value);
  };

  const assertionCardHtml = (item, context = "memory") => {
    const status = item.knowledge_status || "unknown";
    const attention = context === "attention";
    const approval = attention && item.value && item.value.reason === "approval required";
    const value = cardValue(item);
    const subject = pretty(item.subject || "Blackhole");
    const predicate = pretty(item.predicate || "observation");
    let supporting = "";
    if (attention && item.value && typeof item.value === "object") {
      const reason = item.value.reason || "Relevant unresolved item";
      const when = item.value.deadline ? `Deadline ${item.value.deadline}` : "No date stated";
      supporting = `<p class="attention-why"><strong>Why:</strong> ${escapeHtml(pretty(reason))} · <strong>When:</strong> ${escapeHtml(when)}</p>`;
    }
    return `<article class="insight-card${attention ? " is-attention" : ""}${approval ? " is-approval" : ""}${status === "unknown" ? " is-unknown" : ""}">
      <div class="card-top"><span class="card-label">${escapeHtml(subject)} · ${escapeHtml(predicate)}</span>${statusTag(status)}</div>
      <p class="card-value${status === "unknown" ? " is-unknown" : ""}">${escapeHtml(value)}</p>
      ${supporting}
      <div class="card-detail"><span class="evidence">${escapeHtml(sourceText(item))}</span></div>
    </article>`;
  };

  const renderEmpty = (element, message, icon = "check") => {
    element.innerHTML = `<div class="empty-state"><span class="empty-icon"><svg viewBox="0 0 24 24"><use href="#icon-${escapeHtml(icon)}"></use></svg></span><p>${escapeHtml(message)}</p></div>`;
  };

  const renderAttention = (items) => {
    const element = $("#attention-list");
    if (!items || !items.length) {
      renderEmpty(element, "Nothing needs you right now.");
      return;
    }
    element.innerHTML = items.map((item) => assertionCardHtml(item, "attention")).join("");
  };

  const renderMemory = (memory) => {
    const element = $("#memory-sections");
    const usefulSections = memorySections.filter(([key]) => Array.isArray(memory?.[key]) && memory[key].length);
    if (!usefulSections.length) {
      renderEmpty(element, "Memory is quiet for now.");
      return;
    }
    element.innerHTML = usefulSections.map(([key, title, description]) => `<section class="memory-section">
      <div class="memory-section-heading"><div><h3>${escapeHtml(title)}</h3><p class="memory-section-description">${escapeHtml(description)}</p></div><span class="summary-pill">${memory[key].length}</span></div>
      <div class="insight-list">${memory[key].map((item) => assertionCardHtml(item)).join("")}</div>
    </section>`).join("");
  };

  const renderCaptures = (captures) => {
    const element = $("#recent-captures");
    $("#recent-count").textContent = String(captures?.length || 0);
    if (!captures || !captures.length) {
      renderEmpty(element, "No captures yet.");
      return;
    }
    element.innerHTML = captures.map((capture) => `<div class="recent-row">
      <span class="recent-seq">#${escapeHtml(capture.sequence)}</span>
      <div><p class="recent-text">${escapeHtml(capture.text || "Untitled capture")}</p><p class="recent-meta">${escapeHtml(capture.observed_at || "Date unknown")} · ${escapeHtml(pretty(capture.source_type || "source"))}</p></div>
    </div>`).join("");
  };

  const renderMemorySummary = (stateData) => {
    const counts = stateData.counts || {};
    $("#memory-summary").innerHTML = [
      `<span class="summary-pill">${escapeHtml(counts.captures || 0)} captures</span>`,
      `<span class="summary-pill">${escapeHtml(counts.current_facts || 0)} known facts</span>`,
      `<span class="summary-pill">${escapeHtml(counts.relationships || 0)} linked changes</span>`,
    ].join("");
  };

  const renderUnavailableState = () => {
    const badge = $("#nav-attention");
    badge.textContent = "";
    badge.classList.remove("has-count");
    badge.setAttribute("aria-label", "Attention unavailable offline");
    renderEmpty($("#attention-list"), "Attention is unavailable offline.", "attention");
    $("#memory-summary").innerHTML = `<span class="summary-pill">Unavailable offline</span>`;
    renderEmpty($("#memory-sections"), "Memory is unavailable offline.", "attention");
    $("#recent-count").textContent = "—";
    renderEmpty($("#recent-captures"), "Recent captures are unavailable offline.", "attention");
  };

  const renderState = (stateData) => {
    state.hasRemoteState = true;
    const attention = stateData.attention || [];
    const badge = $("#nav-attention");
    badge.textContent = attention.length ? String(attention.length) : "";
    badge.classList.toggle("has-count", attention.length > 0);
    badge.setAttribute("aria-label", `${attention.length} item${attention.length === 1 ? "" : "s"} needing attention`);
    renderAttention(attention);
    renderMemory(stateData.memory || {});
    renderMemorySummary(stateData);
    renderCaptures(stateData.recent_captures || []);
    const provider = stateData.provider || {};
    setConnectionStatus("Local demo", navigator.onLine ? "online" : "offline", provider.message || "The local demo is informational only.");
  };

  const refreshState = async () => {
    try {
      const payload = await api("/api/state");
      renderState(payload.state || {});
      return true;
    } catch (error) {
      setConnectionStatus("Offline shell", "offline", error.message);
      if (!state.hasRemoteState) renderUnavailableState();
      return false;
    }
  };

  const showView = (name, updateHash = true) => {
    if (!viewNames.includes(name)) name = "capture";
    state.activeView = name;
    viewNames.forEach((view) => {
      const active = view === name;
      const element = $(`#view-${view}`);
      const nav = $(`.nav-item[data-view="${view}"]`);
      element.hidden = !active;
      element.classList.toggle("is-active", active);
      nav.classList.toggle("is-active", active);
      if (active) nav.setAttribute("aria-current", "page");
      else nav.removeAttribute("aria-current");
    });
    if (updateHash && window.location.hash !== `#${name}`) history.replaceState(null, "", `#${name}`);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const resizeTextarea = () => {
    const textarea = $("#capture-input");
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 190)}px`;
  };

  const formatBytes = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const clearAttachment = () => {
    if (state.objectUrl) URL.revokeObjectURL(state.objectUrl);
    state.objectUrl = null;
    state.attachment = null;
    $("#file-input").value = "";
    $("#attachment-preview").hidden = true;
    $("#attachment-preview").innerHTML = "";
    $("#composer-note").textContent = "Private by default";
  };

  const renderAttachment = () => {
    const preview = $("#attachment-preview");
    const attachment = state.attachment;
    if (!attachment) {
      preview.hidden = true;
      preview.innerHTML = "";
      $("#composer-note").textContent = "Private by default";
      return;
    }
    const visual = attachment.isImage && state.objectUrl
      ? `<span class="attachment-thumb"><img src="${escapeHtml(state.objectUrl)}" alt="Preview of ${escapeHtml(attachment.name)}"></span>`
      : `<span class="attachment-file-icon"><svg viewBox="0 0 24 24"><use href="#icon-file"></use></svg></span>`;
    preview.innerHTML = `${visual}<span class="attachment-info"><p class="attachment-name">${escapeHtml(attachment.name)}</p><p class="attachment-detail">${escapeHtml(formatBytes(attachment.size))} · bytes stay local in this prototype</p></span><button id="remove-attachment" class="icon-button attachment-remove" type="button" aria-label="Remove ${escapeHtml(attachment.name)}"><svg viewBox="0 0 24 24"><use href="#icon-close"></use></svg></button>`;
    preview.hidden = false;
    $("#composer-note").textContent = "Attachment ready · add a note";
    $("#remove-attachment").addEventListener("click", clearAttachment);
  };

  const isTextLike = (file) => file.type.startsWith("text/") || /\.(txt|md|csv|json|log)$/i.test(file.name);

  const handleAttachment = async (file) => {
    if (!file) return;
    if (file.size > maxAttachmentBytes) {
      setFeedback("That attachment is over 10 MB. Choose a smaller file.", "error");
      $("#file-input").value = "";
      return;
    }
    clearAttachment();
    state.attachment = { name: file.name, size: file.size, type: file.type || "application/octet-stream", isImage: file.type.startsWith("image/") };
    if (state.attachment.isImage) state.objectUrl = URL.createObjectURL(file);
    renderAttachment();
    const input = $("#capture-input");
    if (isTextLike(file) && file.size <= textPreviewBytes && !input.value.trim()) {
      try {
        input.value = await file.text();
        resizeTextarea();
        setFeedback("Text loaded into the note. Selecting the file did not submit it.");
      } catch (_error) {
        setFeedback("File ready. Add a note before saving; its bytes stay local here.");
      }
    } else {
      setFeedback("Attachment ready. Add context if you want, then save the note.");
    }
    input.focus();
  };

  const closeAttachmentMenu = () => {
    const menu = $("#attachment-menu");
    menu.hidden = true;
    $("#attachment-button").setAttribute("aria-expanded", "false");
  };

  const closeTopMenu = () => {
    const menu = $("#top-menu");
    menu.hidden = true;
    $("#menu-button").setAttribute("aria-expanded", "false");
  };

  const selectAttachmentMode = (mode) => {
    const input = $("#file-input");
    input.value = "";
    if (mode === "camera") {
      input.accept = "image/*";
      input.setAttribute("capture", "environment");
    } else if (mode === "photo") {
      input.accept = "image/*";
      input.removeAttribute("capture");
    } else {
      input.accept = "*/*";
      input.removeAttribute("capture");
    }
    input.click();
  };

  const animateCaptureSuccess = async () => {
    const composer = $("#composer");
    const input = $("#capture-input");
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      input.classList.add("is-fading");
      await new Promise((resolve) => window.setTimeout(resolve, 90));
    } else {
      composer.classList.add("is-collapsing");
      await new Promise((resolve) => window.setTimeout(resolve, 330));
    }
    composer.classList.remove("is-collapsing");
    input.classList.remove("is-fading");
  };

  const renderMilestoneProgress = () => {
    const count = localState.localCaptureCount;
    $("#capture-relief-count").textContent = String(count);
    const next = milestones.find((milestone) => milestone > count);
    $("#next-milestone").textContent = next ? `Next: ${next}` : "A lot of room";
  };

  const celebrateMilestoneIfNeeded = () => {
    const count = localState.localCaptureCount;
    if (!milestones.includes(count) || localState.celebrated.includes(count)) return;
    localState.celebrated.push(count);
    persistLocalState();
    $("#milestone-message").textContent = `${count} things off your mind.`;
    $("#milestone-card").hidden = false;
    window.clearTimeout(state.milestoneTimer);
    state.milestoneTimer = window.setTimeout(() => { $("#milestone-card").hidden = true; }, 6200);
  };

  const submitCapture = async (event) => {
    event.preventDefault();
    const input = $("#capture-input");
    const submit = $("#submit-capture");
    const text = input.value.trim();
    if (!text) {
      setFeedback(state.attachment ? "Add a note before saving. Attachment bytes are not uploaded by this demo." : "Write something first, or keep it for later.", "error");
      input.focus();
      return;
    }
    submit.disabled = true;
    setFeedback("");
    const attachment = state.attachment;
    try {
      await api("/api/capture", {
        method: "POST",
        body: JSON.stringify({
          text: input.value,
          source_type: attachment ? (attachment.isImage ? "image" : "document") : "text",
          filename: attachment?.name || null,
        }),
      });
      await animateCaptureSuccess();
      input.value = "";
      resizeTextarea();
      clearAttachment();
      localState.localCaptureCount += 1;
      persistLocalState();
      renderMilestoneProgress();
      celebrateMilestoneIfNeeded();
      setFeedback(attachment ? "Note saved. Attachment bytes were not uploaded." : "Saved.", "success");
      showToast(attachment ? "+1 off your mind · note saved" : "+1 off your mind");
      await refreshState();
    } catch (error) {
      setFeedback(navigator.onLine ? "Couldn't save that. Try again." : "Couldn't save that while offline. Your text is still here.", "error");
      showToast(error.message || "Couldn't save that. Try again.", "error");
    } finally {
      submit.disabled = false;
    }
  };

  const renderAnswerSection = (section) => {
    const assertions = Array.isArray(section.assertions) ? section.assertions : [];
    const cards = assertions.length
      ? assertions.map((item) => assertionCardHtml(item, "answer")).join("")
      : `<div class="empty-state"><p>No supported observations here.</p></div>`;
    return `<section class="answer-section"><h3>${escapeHtml(section.title || "Answer")}</h3><div class="insight-list">${cards}</div></section>`;
  };

  const ask = async (question) => {
    const normalized = question.trim();
    if (!normalized) return;
    const output = $("#answer-output");
    output.setAttribute("aria-busy", "true");
    output.innerHTML = `<div class="empty-state"><span class="empty-icon"><svg viewBox="0 0 24 24"><use href="#icon-orbit"></use></svg></span><p>Looking through your memory…</p></div>`;
    try {
      const payload = await api(`/api/query?q=${encodeURIComponent(normalized)}`);
      const answer = payload.answer || {};
      const sections = Array.isArray(answer.sections) ? answer.sections : [];
      const sectionsHtml = sections.length
        ? sections.map(renderAnswerSection).join("")
        : `<div class="empty-state"><p>No supported observations here.</p></div>`;
      output.innerHTML = `<p class="answer-heading">${escapeHtml(pretty(answer.mode || "current state"))}</p>${sectionsHtml}`;
    } catch (error) {
      output.innerHTML = `<div class="empty-state"><span class="empty-icon"><svg viewBox="0 0 24 24"><use href="#icon-attention"></use></svg></span><p>${escapeHtml(error.message || "Couldn't answer that right now.")}</p></div>`;
    } finally {
      output.removeAttribute("aria-busy");
    }
  };

  const triggerInstall = async () => {
    if (!state.installPrompt) return;
    state.installPrompt.prompt();
    await state.installPrompt.userChoice;
    state.installPrompt = null;
    $("#install-button").hidden = true;
    $("#install-action").hidden = true;
    closeTopMenu();
  };

  const resetDemo = async () => {
    if (!window.confirm("Reset the local demo to its seeded state?")) return;
    try {
      await api("/api/reset", { method: "POST", body: "{}" });
      setFeedback("Demo reset.", "success");
      await refreshState();
    } catch (error) {
      setFeedback(error.message || "Couldn't reset the demo.", "error");
    }
    closeTopMenu();
  };

  $$("[data-view]").forEach((button) => button.addEventListener("click", () => showView(button.dataset.view)));
  $("#capture-input").addEventListener("input", resizeTextarea);
  $("#capture-input").addEventListener("keydown", (event) => {
    if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) $("#capture-form").requestSubmit();
  });
  $("#capture-form").addEventListener("submit", submitCapture);
  $("#attachment-button").addEventListener("click", () => {
    const menu = $("#attachment-menu");
    menu.hidden = !menu.hidden;
    $("#attachment-button").setAttribute("aria-expanded", String(!menu.hidden));
  });
  $$(".attachment-option").forEach((option) => option.addEventListener("click", () => {
    closeAttachmentMenu();
    selectAttachmentMode(option.dataset.attachmentMode);
  }));
  $("#file-input").addEventListener("change", (event) => handleAttachment(event.target.files?.[0]));
  $("#menu-button").addEventListener("click", () => {
    const menu = $("#top-menu");
    menu.hidden = !menu.hidden;
    $("#menu-button").setAttribute("aria-expanded", String(!menu.hidden));
  });
  $("#install-button").addEventListener("click", triggerInstall);
  $("#install-action").addEventListener("click", triggerInstall);
  $("#reset-demo").addEventListener("click", resetDemo);
  $("#dismiss-milestone").addEventListener("click", () => { $("#milestone-card").hidden = true; });
  $("#ask-form").addEventListener("submit", (event) => { event.preventDefault(); ask($("#ask-input").value); });
  $$(".question-chip").forEach((button) => button.addEventListener("click", () => {
    $("#ask-input").value = button.dataset.question || "";
    ask($("#ask-input").value);
  }));
  document.addEventListener("click", (event) => {
    if (!$("#attachment-menu").hidden && !$(".composer-wrap").contains(event.target)) closeAttachmentMenu();
    if (!$("#top-menu").hidden && !$(".top-actions").contains(event.target)) closeTopMenu();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") { closeAttachmentMenu(); closeTopMenu(); }
  });
  window.addEventListener("online", () => { setConnectionStatus("Online · local demo", "online"); refreshState(); });
  window.addEventListener("offline", () => setConnectionStatus("Offline shell", "offline", "The app shell is available; captures need a connection to save."));
  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    state.installPrompt = event;
    if (!document.documentElement.classList.contains("is-standalone")) {
      $("#install-button").hidden = false;
      $("#install-action").hidden = false;
    }
  });
  window.addEventListener("appinstalled", () => {
    state.installPrompt = null;
    $("#install-button").hidden = true;
    $("#install-action").hidden = true;
    closeTopMenu();
  });

  if (window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true) document.documentElement.classList.add("is-standalone");
  renderMilestoneProgress();
  resizeTextarea();
  showView(window.location.hash.slice(1), false);
  refreshState();
  if ("serviceWorker" in navigator) window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => {}));
})();
