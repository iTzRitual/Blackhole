(() => {
  "use strict";

  const viewNames = ["capture", "attention", "memory", "ask"];
  const storageKey = "blackhole.ui.v2";
  const maxAttachmentBytes = 10 * 1024 * 1024;
  const fixtureParam = new URLSearchParams(window.location.search).get("fixture");
  const fixtureMode = fixtureParam !== null;
  const fixtureUnavailable = fixtureParam === "unavailable";
  const fixtureEmpty = fixtureParam === "empty";

  const $ = (selector, parent = document) => parent.querySelector(selector);
  const $$ = (selector, parent = document) => [...parent.querySelectorAll(selector)];

  const escapeHtml = (value) => String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

  const firstValue = (...values) => values.find((value) => value !== null && value !== undefined && String(value).trim() !== "");

  const humanize = (value) => String(value ?? "")
    .replace(/^capture:/i, "")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());

  const lowercaseFirst = (value) => {
    const text = String(value ?? "");
    return text ? text.charAt(0).toLowerCase() + text.slice(1) : text;
  };

  const displayName = (value) => humanize(value || "Blackhole");

  const formatBytes = (bytes) => {
    if (!Number.isFinite(Number(bytes))) return "Size unavailable";
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return Math.round(bytes / 1024) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  const currencySymbol = (currency) => ({
    EUR: "€",
    USD: "$",
    GBP: "£",
    JPY: "¥",
    CHF: "CHF ",
  })[String(currency || "").toUpperCase()] || "";

  const formatMoney = (value) => {
    if (value === null || value === undefined || value === "") return "Amount not stated";
    const source = typeof value === "object" ? value : { amount: value };
    const amount = firstValue(source.amount, source.total, source.value);
    if (amount === undefined) return formatValue(value);
    const currency = String(firstValue(source.currency, source.currency_code, "") || "").toUpperCase();
    const number = Number(amount);
    const formatted = Number.isFinite(number)
      ? new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(number)
      : String(amount);
    const prefix = currencySymbol(currency);
    const suffix = prefix ? "" : (currency ? " " + currency : "");
    const period = firstValue(source.billing_period, source.period, source.cadence);
    return prefix + formatted + suffix + (period ? "/" + lowercaseFirst(humanize(period)) : "");
  };

  const formatDate = (value) => {
    if (value === null || value === undefined || value === "") return "";
    const raw = String(value);
    const parsed = new Date(raw);
    if (Number.isNaN(parsed.getTime())) return humanize(raw);
    return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(parsed);
  };

  const formatValue = (value) => {
    if (value === null || value === undefined || value === "") return "Not stated";
    if (typeof value === "boolean") return value ? "Yes" : "No";
    if (Array.isArray(value)) return value.length ? value.map(formatValue).join(", ") : "Not stated";
    if (typeof value === "object") {
      if (firstValue(value.amount, value.total, value.price, value.value) !== undefined) return formatMoney(value);
      const label = firstValue(value.display, value.label, value.name, value.title, value.summary);
      if (label) return String(label);
      const parts = Object.entries(value)
        .filter(([key]) => !["source_event_id", "target_event_id", "source_refs", "confirmation_ref"].includes(key))
        .map(([key, item]) => humanize(key) + ": " + formatValue(item));
      return parts.join(" · ") || "Not stated";
    }
    return String(value);
  };

  const fileTypeLabel = (attachment) => {
    if (attachment.isImage) return "Image";
    const type = String(attachment.type || "");
    if (type.includes("/")) return type.split("/")[1].split("+")[0].toUpperCase();
    const extension = String(attachment.name || "").split(".").pop();
    return extension && extension !== attachment.name ? extension.toUpperCase() : "File";
  };

  const humanStatus = (status) => ({
    known: "From a capture",
    inferred: "A considered interpretation",
    unknown: "Still uncertain",
  })[String(status || "").toLowerCase()] || "From a capture";

  const statusClass = (status) => ["known", "inferred", "unknown"].includes(String(status || "").toLowerCase())
    ? String(status).toLowerCase()
    : "known";

  const statusDetails = (status, reason) => {
    if (String(status || "").toLowerCase() === "unknown") {
      return "Blackhole is still waiting for clearer evidence" + (reason ? ": " + lowercaseFirst(humanize(reason)) : ".");
    }
    return humanStatus(status) + ".";
  };

  const naturalizeAssertion = (item) => {
    const predicate = String(item?.predicate || "").toLowerCase();
    const value = item?.value;
    const subject = displayName(firstValue(item?.entity_name, item?.subject, item?.entity?.name, "This memory"));
    if (item?.summary || item?.display?.summary || item?.text || item?.description) {
      return String(firstValue(item.summary, item.display?.summary, item.text, item.description));
    }
    if (predicate.includes("current_price") || predicate.includes("price")) {
      const price = formatMoney(value);
      if (predicate.includes("historical")) return "Changed from " + price;
      return price;
    }
    if (predicate.includes("deadline") || predicate.includes("renewal") || predicate.includes("due")) {
      const date = typeof value === "object" ? firstValue(value.date, value.deadline, value.when) : value;
      return date ? "Renew by " + formatDate(date) : "A deadline is coming up";
    }
    if (predicate.includes("owner") || predicate.includes("location") || predicate.includes("place")) {
      return "At " + displayName(formatValue(value));
    }
    if (predicate.includes("status")) return humanize(formatValue(value));
    if (predicate.includes("missing") || predicate.includes("unobserved")) {
      return "Missing " + lowercaseFirst(formatValue(value));
    }
    if (predicate.includes("unknown") || String(item?.knowledge_status).toLowerCase() === "unknown") {
      return "Still unclear" + (item?.unknown_reason ? " — " + lowercaseFirst(humanize(item.unknown_reason)) : "");
    }
    if (predicate) return humanize(predicate) + ": " + formatValue(value);
    if (value !== undefined) return subject + ": " + formatValue(value);
    return "A memory Blackhole is keeping nearby";
  };

  const normalizeEvidence = (item) => {
    const evidence = firstValue(item?.evidence, item?.source, item?.source_refs, item?.sources);
    if (Array.isArray(evidence)) return evidence.map((ref) => String(ref)).join(", ");
    return evidence ? String(evidence) : "From a captured source";
  };

  const normalizeAttention = (items) => {
    const source = Array.isArray(items) ? items : [];
    return source.map((item, index) => {
      const value = item?.value;
      const display = item?.display || {};
      const subject = displayName(firstValue(item?.entity_name, item?.subject, item?.entity?.name, item?.title, "Something"));
      const predicate = String(item?.predicate || "").toLowerCase();
      const rawWhen = firstValue(display.when, display.time, display.relative_time, item?.when, item?.relative_time, item?.deadline, value?.deadline, value?.when);
      const title = String(firstValue(item?.title, display.title, item?.label,
        predicate.includes("deadline") || predicate.includes("due") || predicate.includes("renew")
          ? "Renew " + subject
          : predicate.includes("approval")
            ? "Review " + subject
            : subject));
      const summary = String(firstValue(item?.summary, display.summary, item?.description,
        predicate.includes("approval") || value?.reason === "approval required"
          ? "Needs your decision before it can move forward."
          : predicate.includes("deadline") || predicate.includes("due")
            ? "A deadline is coming up."
            : "Worth a look while it is still useful."));
      const detail = String(firstValue(item?.detail, item?.details, value?.detail, value?.reason,
        predicate ? humanize(predicate) + " needs a closer look." : "Blackhole found something worth checking."));
      const rawUrgency = String(firstValue(item?.urgency, display.urgency, "")).toLowerCase();
      const urgency = rawUrgency || (String(rawWhen || "").toLowerCase().includes("overdue") ? "overdue" : String(rawWhen || "").toLowerCase().includes("min") ? "soon" : "upcoming");
      const when = rawWhen ? (String(rawWhen).match(/^\d{4}-\d{2}-\d{2}/) ? formatDate(rawWhen) : String(rawWhen)) : "Worth a look";
      return {
        id: String(firstValue(item?.id, item?.event_id, item?.state_key, "attention-" + index)),
        title,
        summary,
        detail,
        when,
        urgency,
        approval: Boolean(item?.approval_required || value?.reason === "approval required" || predicate.includes("approval")),
        evidence: normalizeEvidence(item),
        status: item?.knowledge_status || item?.status || "known",
        unknownReason: item?.unknown_reason || "",
      };
    });
  };

  const kindLabel = (kind) => {
    const normalized = String(kind || "").toLowerCase();
    const labels = {
      person: "Person",
      people: "People",
      place: "Place",
      places: "Places",
      thing: "Thing",
      things: "Things",
      money: "Money",
      subscription: "Subscription",
      task: "Task",
      document: "Document",
      service: "Service",
      merchant: "Purchase",
      change: "Change",
    };
    return labels[normalized] || humanize(normalized || "Memory");
  };

  const normalizeFact = (item, fallbackEntity) => {
    if (typeof item === "string") {
      return {
        text: item,
        detail: "",
        status: "known",
        evidence: "From a captured source",
        unknownReason: "",
      };
    }
    const source = item || {};
    const text = String(firstValue(source.summary, source.display?.summary, source.text, source.description, source.label, naturalizeAssertion({ ...source, subject: source.subject || fallbackEntity })));
    return {
      text,
      detail: String(firstValue(source.detail, source.details, source.explanation, "")),
      status: source.knowledge_status || source.status || "known",
      evidence: normalizeEvidence(source),
      unknownReason: source.unknown_reason || "",
    };
  };

  const normalizeMemory = (memory) => {
    const groups = new Map();
    const addGroup = (id, name, kind, summary, facts) => {
      const key = String(id || name || "memory").toLowerCase();
      if (!groups.has(key)) {
        groups.set(key, {
          id: key,
          name: String(name || "Memory"),
          kind: kindLabel(kind),
          kindKey: String(kind || "memory").toLowerCase(),
          summary: String(summary || ""),
          facts: [],
        });
      }
      const group = groups.get(key);
      if (summary && !group.summary) group.summary = String(summary);
      (Array.isArray(facts) ? facts : []).forEach((fact) => group.facts.push(normalizeFact(fact, name)));
      return group;
    };

    if (!memory || typeof memory !== "object") return [];
    const entities = Array.isArray(memory.entities) ? memory.entities : [];
    entities.forEach((entity, index) => {
      const name = String(firstValue(entity.name, entity.title, entity.display_name, entity.subject, "Memory"));
      const facts = firstValue(entity.facts, entity.items, entity.observations) || [];
      addGroup(entity.id || entity.entity_id || name + index, name, entity.kind || entity.type, entity.summary, facts);
    });

    const topics = Array.isArray(memory.topics) ? memory.topics : [];
    topics.forEach((topic, index) => {
      const name = String(firstValue(topic.name, topic.title, topic.label, "Topic"));
      addGroup(topic.id || name + index, name, topic.kind || "topic", topic.summary, topic.items || topic.facts || []);
    });

    const groupsPayload = Array.isArray(memory.groups) ? memory.groups : [];
    groupsPayload.forEach((group, index) => {
      const name = String(firstValue(group.name, group.title, group.label, "Memory"));
      addGroup(group.id || name + index, name, group.kind || "memory", group.summary, group.items || group.facts || []);
    });

    Object.entries(memory).forEach(([sectionKey, sectionItems]) => {
      if (["entities", "topics", "groups", "items", "attention", "counts", "approval", "recent_captures", "processing"].includes(sectionKey)) return;
      if (!Array.isArray(sectionItems)) return;
      sectionItems.forEach((item, index) => {
        const source = typeof item === "object" && item ? item : { text: String(item) };
        const name = String(firstValue(source.entity_name, source.entity?.name, source.subject, source.title, kindLabel(sectionKey)));
        const kind = firstValue(source.entity_kind, source.entity?.kind, source.kind, sectionKey);
        const group = addGroup(source.entity_id || source.entity?.id || name, name, kind, "", []);
        group.facts.push(normalizeFact(source, name));
      });
    });

    return [...groups.values()].filter((group) => group.facts.length);
  };

  const normalizeSupportItem = (item) => {
    const source = typeof item === "object" && item ? item : { text: String(item) };
    const normalized = normalizeFact(source, source.subject || source.title || "Memory");
    return {
      text: normalized.text,
      detail: normalized.detail,
      status: normalized.status,
      evidence: normalized.evidence,
      unknownReason: normalized.unknownReason,
    };
  };

  const deriveAnswerSummary = (answer, groups) => {
    const mode = String(answer?.mode || "").toLowerCase();
    if (mode === "attention" || mode.includes("attention")) return "Here’s what needs your attention:";
    if (mode.includes("recurring") || mode.includes("subscription") || mode.includes("cost")) return "You’re currently paying for:";
    if (mode.includes("task")) return "Here’s what you have on your plate:";
    if (mode.includes("change")) return "A few things changed recently:";
    if (mode === "unsupported") return "I’m not sure how to answer that yet.";
    if (groups.length) return "Here’s what I found in your memory:";
    return "I couldn’t find a clear match yet.";
  };

  const normalizeAnswer = (payload) => {
    const answer = payload?.answer || payload || {};
    const mode = String(answer.mode || answer.status || "").toLowerCase();
    const rawMessage = String(answer.message || "");
    if (mode === "unsupported" || rawMessage.toLowerCase().includes("outside blackhole")) {
      return {
        status: "unsupported",
        summary: "I’m not sure how to answer that yet.",
        helper: "Try asking about something you’ve captured, or phrase it another way.",
        groups: [],
      };
    }

    const groups = [];
    const rawGroups = Array.isArray(answer.groups) ? answer.groups : [];
    rawGroups.forEach((group, index) => {
      const items = firstValue(group.items, group.assertions, []) || [];
      groups.push({
        id: String(firstValue(group.id, group.title, "group-" + index)),
        title: String(firstValue(group.title, group.name, "Related memories")),
        items: Array.isArray(items) ? items.map(normalizeSupportItem) : [],
      });
    });

    const sections = Array.isArray(answer.sections) ? answer.sections : [];
    sections.forEach((section, index) => {
      const items = firstValue(section.items, section.assertions, []) || [];
      groups.push({
        id: String(firstValue(section.id, section.title, "section-" + index)),
        title: String(firstValue(section.title, "Related memories")),
        items: Array.isArray(items) ? items.map(normalizeSupportItem) : [],
      });
    });

    if (!groups.length && Array.isArray(answer.items)) {
      groups.push({ id: "answer", title: "Related memories", items: answer.items.map(normalizeSupportItem) });
    }

    const meaningfulGroups = groups.filter((group) => group.items.length);
    const messageIsEmpty = !rawMessage || rawMessage.toLowerCase().includes("no supported observations");
    const status = mode === "no_match" || mode === "empty" || (!meaningfulGroups.length && !answer.summary && messageIsEmpty)
      ? "no_match"
      : "ready";
    const summary = String(firstValue(answer.summary, answer.direct_answer, answer.text,
      status === "no_match" ? "I couldn’t find that in your memory yet." : deriveAnswerSummary(answer, meaningfulGroups)));
    return {
      status,
      summary,
      helper: status === "no_match" ? "Try a person, place, thing, task, or recent change." : "",
      groups: meaningfulGroups,
    };
  };

  const createFixtureState = () => {
    if (fixtureEmpty) {
      return {
        attention: [],
        memory: { entities: [] },
        counts: { captures: 0 },
        recent_captures: [],
      };
    }
    return {
      attention: [
        {
          id: "attention-pickup",
          title: "Pick up the kids",
          summary: "Leave soon for pickup.",
          display: { when: "in 8 min", urgency: "soon" },
          detail: "A reminder you captured for today.",
          evidence: "From a captured note",
          knowledge_status: "known",
        },
        {
          id: "attention-parking",
          title: "Renew parking permit",
          summary: "The permit is due on Sep 12.",
          display: { when: "Sep 12", urgency: "upcoming" },
          detail: "A date you mentioned while thinking about the apartment.",
          evidence: "From a captured note",
          knowledge_status: "known",
        },
        {
          id: "attention-approval",
          title: "Review the PocketWave change",
          summary: "A price change is waiting for your decision.",
          display: { when: "Worth a look", urgency: "upcoming" },
          detail: "Blackhole found a proposed change; nothing has been changed for you.",
          evidence: "From a captured note",
          approval_required: true,
          knowledge_status: "inferred",
        },
      ],
      memory: {
        entities: [
          {
            id: "kuba",
            name: "Kuba",
            kind: "person",
            summary: "People and preferences you’ve mentioned.",
            facts: [
              { summary: "Likes the green pasta from Lidl", status: "known", evidence: "From a captured note" },
              { summary: "Birthday is still unclear", status: "unknown", unknown_reason: "not stated", evidence: "No clear source yet" },
            ],
          },
          {
            id: "car",
            name: "Car",
            kind: "thing",
            summary: "A few observations about your car.",
            facts: [
              { summary: "Started knocking at the front-left", status: "known", evidence: "From a captured note" },
            ],
          },
          {
            id: "basement-keys",
            name: "Basement keys",
            kind: "thing",
            summary: "A small detail worth being able to find.",
            facts: [
              { summary: "At Mum’s place", status: "known", evidence: "From a captured note" },
            ],
          },
          {
            id: "pocketwave",
            name: "PocketWave",
            kind: "money",
            summary: "A recurring cost with a change in its history.",
            facts: [
              { summary: "€11/month", status: "known", evidence: "From a captured note" },
              { summary: "Changed from €9 on Sep 1", status: "known", evidence: "From a later captured note" },
            ],
          },
          {
            id: "parking-permit",
            name: "Parking permit",
            kind: "task",
            summary: "One deadline to keep nearby.",
            facts: [
              { summary: "Renew by Sep 12", status: "known", evidence: "From a captured note" },
            ],
          },
        ],
      },
      counts: { captures: 18, current_facts: 12, relationships: 4 },
      recent_captures: [],
    };
  };

  const fixtureState = createFixtureState();
  let fixtureSequence = 19;

  const wait = (duration) => new Promise((resolve) => window.setTimeout(resolve, duration));

  const fixtureAnswer = (question) => {
    const normalized = String(question || "").toLowerCase();
    if (normalized.includes("pay") || normalized.includes("subscription") || normalized.includes("cost")) {
      return {
        mode: "recurring_costs",
        summary: "You’re currently paying for:",
        groups: [{
          title: "Recurring costs",
          items: [
            { summary: "PocketWave · €11/month", detail: "Changed from €9 on Sep 1", status: "known", evidence: "From a captured note" },
          ],
        }],
      };
    }
    if (normalized.includes("car")) {
      return {
        mode: "memory",
        summary: "Here’s what I remember about your car:",
        groups: [{
          title: "Car",
          items: [{ summary: "Started knocking at the front-left", status: "known", evidence: "From a captured note" }],
        }],
      };
    }
    if (normalized.includes("today") || normalized.includes("attention") || normalized.includes("week") || normalized.includes("need")) {
      return {
        mode: "attention",
        summary: "Here’s what needs your attention:",
        groups: [{ title: "Worth acting on", items: normalizeAttention(fixtureState.attention).map((item) => ({
          summary: item.title + " · " + item.when,
          detail: item.summary,
          status: item.status,
          evidence: item.evidence,
        })) }],
      };
    }
    if (normalized.includes("change") || normalized.includes("recent")) {
      return {
        mode: "changes",
        summary: "A few things changed recently:",
        groups: [{
          title: "Recent changes",
          items: [
            { summary: "PocketWave changed from €9 to €11/month", detail: "The new price starts Sep 1.", status: "known", evidence: "From a captured note" },
          ],
        }],
      };
    }
    return {
      mode: "no_match",
      message: "I couldn’t find that in your memory yet.",
    };
  };

  class ClientError extends Error {
    constructor(message, code = "request_failed", status = 0) {
      super(message);
      this.name = "ClientError";
      this.code = code;
      this.status = status;
    }
  }

  const api = async (url, options = {}) => {
    let response;
    try {
      response = await fetch(url, {
        headers: { "Content-Type": "application/json", ...(options.headers || {}) },
        ...options,
      });
    } catch (_error) {
      throw new ClientError("Blackhole is not reachable right now.", "offline");
    }
    let payload = {};
    try {
      payload = await response.json();
    } catch (_error) {
      throw new ClientError("Blackhole returned an unreadable response.", "invalid_response", response.status);
    }
    if (!response.ok) {
      throw new ClientError(
        String(payload.message || payload.error || "Blackhole could not complete that request."),
        String(payload.code || "request_failed"),
        response.status,
      );
    }
    return payload;
  };

  const client = {
    fixture: fixtureMode,
    async getState() {
      if (fixtureMode) {
        await wait(40);
        return fixtureState;
      }
      const payload = await api("/api/state");
      return payload.state || {};
    },
    async capture(payload) {
      if (fixtureMode) {
        await wait(80);
        const eventId = "fixture:capture-" + fixtureSequence;
        fixtureSequence += 1;
        return {
          ok: true,
          saved: true,
          message: "Saved.",
          capture: { event_id: eventId, sequence: fixtureSequence },
          processing: { status: "pending" },
        };
      }
      const attachment = payload.attachment;
      return api("/api/capture", {
        method: "POST",
        body: JSON.stringify({
          text: payload.text || "",
          source_type: attachment ? (attachment.isImage ? "image" : "document") : "text",
          filename: attachment?.name || null,
          attachment: attachment ? {
            name: attachment.name,
            type: attachment.type,
            size: attachment.size,
          } : null,
        }),
      });
    },
    async retractCapture(captureId) {
      if (fixtureMode) {
        await wait(60);
        return { ok: true, retracted: true, capture: { event_id: captureId } };
      }
      return api("/api/capture/retract", {
        method: "POST",
        body: JSON.stringify({ capture_id: captureId }),
      });
    },
    async ask(question) {
      if (fixtureMode) {
        await wait(180);
        if (fixtureUnavailable) {
          throw new ClientError("Your local provider is unavailable right now.", "provider_unavailable", 503);
        }
        return { ok: true, answer: fixtureAnswer(question) };
      }
      return api("/api/query", {
        method: "POST",
        body: JSON.stringify({ question }),
      });
    },
  };

  const readLocalState = () => {
    try {
      const stored = JSON.parse(window.localStorage.getItem(storageKey) || "{}");
      return {
        activeView: viewNames.includes(stored.activeView) ? stored.activeView : "capture",
        memoryFilter: typeof stored.memoryFilter === "string" ? stored.memoryFilter : "all",
      };
    } catch (_error) {
      return { activeView: "capture", memoryFilter: "all" };
    }
  };

  const localState = readLocalState();
  const state = {
    activeView: localState.activeView,
    memoryFilter: localState.memoryFilter,
    memoryQuery: "",
    attention: [],
    memoryEntities: [],
    dataAvailable: false,
    attachment: null,
    objectUrl: null,
    installPrompt: null,
    submitting: false,
    asking: false,
    toastTimer: null,
    toastAction: null,
    undoRecord: null,
    lastAskQuestion: "",
  };

  const persistLocalState = () => {
    try {
      window.localStorage.setItem(storageKey, JSON.stringify({
        activeView: state.activeView,
        memoryFilter: state.memoryFilter,
      }));
    } catch (_error) {
      // Local view preferences are optional.
    }
  };

  const prefersReducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const setConnectionStatus = (text, mode = "") => {
    const element = $("#connection-status");
    if (!element) return;
    element.textContent = text;
    element.dataset.mode = mode;
  };

  const renderEmpty = (element, title, message, icon = "spark") => {
    if (!element) return;
    element.innerHTML = '<div class="empty-state">' +
      '<span class="empty-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#icon-' + escapeHtml(icon) + '"></use></svg></span>' +
      '<div><h3>' + escapeHtml(title) + '</h3><p>' + escapeHtml(message) + '</p></div>' +
      '</div>';
  };

  const clearToast = () => {
    const region = $("#toast-region");
    if (state.toastTimer) window.clearTimeout(state.toastTimer);
    state.toastTimer = null;
    state.toastAction = null;
    if (region) region.innerHTML = "";
  };

  const showToast = (message, kind = "", actionLabel = "", action = null) => {
    const region = $("#toast-region");
    if (!region) return;
    clearToast();
    const icon = kind === "error" ? "error" : "check";
    region.innerHTML = '<div class="toast' + (kind ? " is-" + escapeHtml(kind) : "") + '" role="status">' +
      '<span class="toast-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#icon-' + icon + '"></use></svg></span>' +
      '<span class="toast-message">' + escapeHtml(message) + '</span>' +
      (actionLabel ? '<button class="toast-action" type="button" data-toast-action>' + escapeHtml(actionLabel) + '</button>' : "") +
      '</div>';
    state.toastAction = action;
    const actionButton = $("[data-toast-action]", region);
    if (actionButton) actionButton.addEventListener("click", () => {
      const callback = state.toastAction;
      clearToast();
      if (callback) callback();
    });
    state.toastTimer = window.setTimeout(clearToast, kind === "error" ? 5600 : actionLabel ? 5200 : 3400);
  };

  const setFeedback = (message, kind = "") => {
    const element = $("#capture-feedback");
    if (!element) return;
    element.textContent = message;
    element.className = "inline-feedback" + (kind ? " is-" + kind : "");
  };

  const updateCapturePlaceholder = () => {
    const input = $("#capture-input");
    if (input) input.placeholder = state.attachment ? "Add a note (optional)…" : "Capture it…";
  };

  const clearAttachment = () => {
    if (state.objectUrl && window.URL?.revokeObjectURL) window.URL.revokeObjectURL(state.objectUrl);
    state.objectUrl = null;
    state.attachment = null;
    const fileInput = $("#file-input");
    if (fileInput) fileInput.value = "";
    const preview = $("#attachment-preview");
    if (preview) {
      preview.hidden = true;
      preview.innerHTML = "";
    }
    updateCapturePlaceholder();
  };

  const renderAttachment = () => {
    const preview = $("#attachment-preview");
    const attachment = state.attachment;
    if (!preview) return;
    if (!attachment) {
      preview.hidden = true;
      preview.innerHTML = "";
      return;
    }
    const visual = attachment.isImage && state.objectUrl
      ? '<span class="attachment-thumb"><img src="' + escapeHtml(state.objectUrl) + '" alt="Preview of ' + escapeHtml(attachment.name) + '" width="48" height="48"></span>'
      : '<span class="attachment-file-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#icon-file"></use></svg></span>';
    preview.innerHTML = visual +
      '<span class="attachment-info"><strong class="attachment-name">' + escapeHtml(attachment.name) + '</strong><span class="attachment-detail">' + escapeHtml(fileTypeLabel(attachment) + " · " + formatBytes(attachment.size)) + '</span></span>' +
      '<button id="remove-attachment" class="icon-button attachment-remove" type="button" aria-label="Remove ' + escapeHtml(attachment.name) + '"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#icon-close"></use></svg></button>';
    preview.hidden = false;
    const remove = $("#remove-attachment");
    if (remove) remove.addEventListener("click", clearAttachment);
    updateCapturePlaceholder();
  };

  const resizeTextarea = () => {
    const textarea = $("#capture-input");
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = Math.min(Math.max(textarea.scrollHeight, 52), 180) + "px";
  };

  const handleAttachment = (file) => {
    if (!file) return;
    if (file.size > maxAttachmentBytes) {
      setFeedback("That attachment is over 10 MB. Choose a smaller file.", "error");
      const fileInput = $("#file-input");
      if (fileInput) fileInput.value = "";
      return;
    }
    clearAttachment();
    state.attachment = {
      file,
      name: file.name,
      size: file.size,
      type: file.type || "application/octet-stream",
      isImage: file.type.startsWith("image/"),
    };
    if (state.attachment.isImage && window.URL?.createObjectURL) {
      state.objectUrl = window.URL.createObjectURL(file);
    }
    renderAttachment();
    setFeedback("");
    const input = $("#capture-input");
    if (input) input.focus();
  };

  const closeAttachmentMenu = () => {
    const menu = $("#attachment-menu");
    const button = $("#attachment-button");
    if (menu) menu.hidden = true;
    if (button) button.setAttribute("aria-expanded", "false");
  };

  const selectAttachmentMode = (mode) => {
    const input = $("#file-input");
    if (!input) return;
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

  const renderAttention = () => {
    const element = $("#attention-list");
    const items = state.attention;
    if (!items.length) {
      renderEmpty(element, "Nothing needs your attention.", "Blackhole will only interrupt when something is worth acting on.", "check");
      return;
    }
    element.innerHTML = items.map((item) => {
      const status = statusClass(item.status);
      return '<article class="attention-card urgency-' + escapeHtml(item.urgency) + (item.approval ? " is-approval" : "") + '">' +
        '<div class="attention-card-main">' +
          '<span class="attention-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#icon-attention"></use></svg></span>' +
          '<div class="attention-copy"><h3>' + escapeHtml(item.title) + '</h3><p>' + escapeHtml(item.summary) + '</p></div>' +
          '<span class="attention-when">' + escapeHtml(item.when) + '</span>' +
        '</div>' +
        '<div class="attention-card-meta">' +
          (item.approval ? '<span class="attention-state">Needs your decision</span>' : '<span class="attention-state">' + escapeHtml(item.urgency === "overdue" ? "Overdue" : "Upcoming") + '</span>') +
          '<details class="evidence-details"><summary>Why this is here</summary><div class="detail-copy"><p>' + escapeHtml(item.detail) + '</p><p class="detail-meta">' + escapeHtml(statusDetails(item.status, item.unknownReason)) + ' · ' + escapeHtml(item.evidence) + '</p></div></details>' +
        '</div>' +
      '</article>';
    }).join("");
  };

  const updateAttentionBadge = () => {
    const badge = $("#nav-attention");
    if (!badge) return;
    const count = state.attention.length;
    badge.textContent = count ? String(count) : "";
    badge.classList.toggle("has-count", count > 0);
    badge.setAttribute("aria-hidden", count ? "false" : "true");
    const button = $('.nav-item[data-view="attention"]');
    if (button) button.setAttribute("aria-label", count ? "Attention, " + count + " items" : "Attention");
  };

  const availableMemoryKinds = () => {
    const kinds = [...new Set(state.memoryEntities.map((entity) => entity.kindKey).filter(Boolean))];
    return ["all", ...kinds];
  };

  const renderMemoryFilters = () => {
    const element = $("#memory-filters");
    if (!element) return;
    const options = availableMemoryKinds();
    if (!options.includes(state.memoryFilter)) state.memoryFilter = "all";
    element.innerHTML = options.map((option) => {
      const active = option === state.memoryFilter;
      return '<button class="filter-chip' + (active ? " is-active" : "") + '" type="button" data-memory-filter="' + escapeHtml(option) + '" aria-pressed="' + String(active) + '">' + escapeHtml(option === "all" ? "All" : kindLabel(option)) + '</button>';
    }).join("");
  };

  const renderMemorySummary = () => {
    const element = $("#memory-summary");
    if (!element) return;
    const total = state.memoryEntities.length;
    const visible = state.memoryEntities.filter((entity) => {
      const matchesKind = state.memoryFilter === "all" || entity.kindKey === state.memoryFilter;
      const query = state.memoryQuery.trim().toLowerCase();
      return matchesKind && (!query || entity.name.toLowerCase().includes(query) || entity.facts.some((fact) => fact.text.toLowerCase().includes(query)));
    }).length;
    const text = state.memoryQuery || state.memoryFilter !== "all"
      ? visible + (visible === 1 ? " memory" : " memories") + " in this view"
      : total + (total === 1 ? " memory" : " memories") + " worth keeping nearby";
    element.textContent = text;
  };

  const renderMemory = () => {
    const element = $("#memory-list");
    if (!element) return;
    renderMemoryFilters();
    renderMemorySummary();
    const query = state.memoryQuery.trim().toLowerCase();
    const filtered = state.memoryEntities.filter((entity) => {
      const matchesKind = state.memoryFilter === "all" || entity.kindKey === state.memoryFilter;
      const matchesQuery = !query || entity.name.toLowerCase().includes(query) || entity.facts.some((fact) => fact.text.toLowerCase().includes(query));
      return matchesKind && matchesQuery;
    });
    if (!filtered.length) {
      renderEmpty(element,
        state.memoryEntities.length ? "Nothing matches that search." : "Your memory is just getting started.",
        state.memoryEntities.length ? "Try a different word or browse everything." : "Capture a thought, receipt, or reminder and it will appear here.",
        "memory");
      return;
    }
    element.innerHTML = filtered.map((entity) => {
      const initial = entity.name.trim().charAt(0).toUpperCase() || "•";
      return '<article class="memory-card">' +
        '<header class="memory-card-header">' +
          '<span class="entity-avatar" aria-hidden="true">' + escapeHtml(initial) + '</span>' +
          '<div class="entity-heading"><h3>' + escapeHtml(entity.name) + '</h3><p>' + escapeHtml(entity.kind) + '</p></div>' +
          '<span class="entity-fact-count">' + entity.facts.length + '</span>' +
        '</header>' +
        (entity.summary ? '<p class="memory-card-summary">' + escapeHtml(entity.summary) + '</p>' : "") +
        '<ul class="memory-facts">' + entity.facts.map((fact) => {
          const status = statusClass(fact.status);
          return '<li class="memory-fact is-' + status + '">' +
            '<span class="fact-marker" aria-hidden="true"></span>' +
            '<span class="fact-copy"><span>' + escapeHtml(fact.text) + '</span>' +
            '<span class="fact-status">' + escapeHtml(humanStatus(fact.status)) + '</span></span>' +
          '</li>';
        }).join("") + '</ul>' +
        '<details class="evidence-details memory-evidence"><summary>Why Blackhole knows this</summary><div class="detail-copy"><p>' +
          escapeHtml(entity.facts.map((fact) => fact.text + " — " + statusDetails(fact.status, fact.unknownReason) + ". " + fact.evidence).join(" ")) +
        '</p></div></details>' +
      '</article>';
    }).join("");
  };

  const renderUnavailableState = () => {
    state.attention = [];
    state.memoryEntities = [];
    updateAttentionBadge();
    renderEmpty($("#attention-list"), "Attention is unavailable right now.", "Your saved captures are safe. Try again when Blackhole is reachable.", "attention");
    renderMemoryFilters();
    renderMemorySummary();
    renderEmpty($("#memory-list"), "Memory is unavailable right now.", "Your saved captures are safe. Try again when Blackhole is reachable.", "attention");
  };

  const renderState = (rawState) => {
    state.dataAvailable = true;
    const rawAttention = Array.isArray(rawState?.attention) ? rawState.attention : rawState?.attention?.items;
    state.attention = normalizeAttention(rawAttention);
    state.memoryEntities = normalizeMemory(rawState?.memory || rawState);
    updateAttentionBadge();
    renderAttention();
    renderMemory();
    setConnectionStatus(fixtureMode ? "Fixture" : "Connected", "online");
  };

  const refreshState = async () => {
    try {
      const rawState = await client.getState();
      renderState(rawState || {});
      return true;
    } catch (error) {
      setConnectionStatus("Offline", "offline");
      if (!state.dataAvailable) renderUnavailableState();
      if (state.activeView === "attention" || state.activeView === "memory") {
        showToast("Blackhole is not reachable right now.", "error");
      }
      return false;
    }
  };

  const renderAnswerLoading = () => {
    const output = $("#answer-output");
    if (!output) return;
    output.setAttribute("aria-busy", "true");
    output.innerHTML = '<div class="answer-loading"><span class="loading-orbit" aria-hidden="true"><svg viewBox="0 0 24 24"><use href="#icon-orbit"></use></svg></span><div><h3>Looking through your memory…</h3><p>Just a moment.</p></div></div>';
  };

  const renderAnswerState = (title, message, kind = "empty", actionLabel = "", action = null) => {
    const output = $("#answer-output");
    if (!output) return;
    output.removeAttribute("aria-busy");
    output.innerHTML = '<div class="answer-state is-' + escapeHtml(kind) + '">' +
      '<span class="answer-state-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#icon-' + (kind === "error" ? "error" : kind === "no-match" ? "search" : "spark") + '"></use></svg></span>' +
      '<div><h3>' + escapeHtml(title) + '</h3><p>' + escapeHtml(message) + '</p>' +
      (actionLabel ? '<button class="quiet-button" type="button" data-answer-action>' + escapeHtml(actionLabel) + '</button>' : "") +
      '</div></div>';
    const button = $("[data-answer-action]", output);
    if (button && action) button.addEventListener("click", action);
  };

  const renderAnswer = (normalized) => {
    const output = $("#answer-output");
    if (!output) return;
    output.removeAttribute("aria-busy");
    if (normalized.status === "unsupported") {
      renderAnswerState("Let’s try that another way.", normalized.helper, "no-match");
      return;
    }
    if (normalized.status === "no_match") {
      renderAnswerState("Nothing clear came back yet.", normalized.summary, "no-match");
      return;
    }
    output.innerHTML = '<div class="answer-summary"><span class="answer-spark"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#icon-spark"></use></svg></span><p>' + escapeHtml(normalized.summary) + '</p></div>' +
      '<div class="answer-groups">' + normalized.groups.map((group) => {
        return '<section class="answer-group"><h3>' + escapeHtml(group.title) + '</h3><ul class="support-list">' +
          group.items.map((item) => '<li class="support-item is-' + statusClass(item.status) + '">' +
            '<span class="fact-marker" aria-hidden="true"></span><span class="support-copy"><span>' + escapeHtml(item.text) + '</span>' +
            (item.detail ? '<span class="support-detail">' + escapeHtml(item.detail) + '</span>' : "") +
            '</span><details class="evidence-details"><summary>Details</summary><div class="detail-copy"><p>' + escapeHtml(statusDetails(item.status, item.unknownReason) + " · " + item.evidence) + '</p></div></details>' +
          '</li>').join("") +
          '</ul></section>';
      }).join("") + '</div>' +
      '<p class="answer-grounding">Based on what you’ve captured so far.</p>';
  };

  const answerError = (error) => {
    const code = String(error?.code || "");
    if (code === "provider_unavailable" || code === "state_not_fresh") {
      renderAnswerState("Your latest memory is still safe.", "Blackhole couldn’t finish understanding the newest capture yet. Try again when your local provider is available.", "error", "Try again", () => ask(state.lastAskQuestion));
      return;
    }
    if (code === "offline") {
      renderAnswerState("Blackhole is offline.", "Your saved captures are safe. Reconnect and try again.", "error", "Try again", () => ask(state.lastAskQuestion));
      return;
    }
    renderAnswerState("I couldn’t answer that yet.", "Try again in a moment, or ask about a different capture.", "error", "Try again", () => ask(state.lastAskQuestion));
  };

  const ask = async (question) => {
    const normalizedQuestion = String(question || "").trim();
    if (!normalizedQuestion || state.asking) return;
    state.asking = true;
    state.lastAskQuestion = normalizedQuestion;
    renderAnswerLoading();
    try {
      const payload = await client.ask(normalizedQuestion);
      renderAnswer(normalizeAnswer(payload));
    } catch (error) {
      answerError(error);
    } finally {
      state.asking = false;
    }
  };

  const animateCaptureSuccess = async () => {
    const composer = $("#composer");
    const vortex = $("#capture-vortex");
    if (!composer) return;
    composer.classList.add("is-collapsing");
    if (vortex && !prefersReducedMotion()) vortex.classList.add("is-active");
    await wait(prefersReducedMotion() ? 180 : 520);
    composer.classList.remove("is-collapsing");
    if (vortex) vortex.classList.remove("is-active");
  };

  const undoCapture = async () => {
    const record = state.undoRecord;
    if (!record || record.inFlight) return;
    record.inFlight = true;
    try {
      await client.retractCapture(record.id);
      state.undoRecord = null;
      showToast("Capture undone");
      await refreshState();
    } catch (error) {
      record.inFlight = false;
      showToast("Undo is not connected on this host yet.", "error");
    }
  };

  const submitCapture = async (event) => {
    event.preventDefault();
    if (state.submitting) return;
    const input = $("#capture-input");
    const submit = $("#submit-capture");
    const plus = $("#attachment-button");
    const text = input ? input.value : "";
    const attachment = state.attachment;
    if (!text.trim() && !attachment) {
      setFeedback("Add a thought or choose an attachment.", "error");
      if (input) input.focus();
      return;
    }

    state.submitting = true;
    if (submit) submit.disabled = true;
    if (plus) plus.disabled = true;
    const composer = $("#composer");
    if (composer) composer.setAttribute("aria-busy", "true");
    setFeedback("Saving…");
    try {
      const result = await client.capture({ text, attachment });
      const captureId = String(firstValue(result?.capture?.event_id, result?.capture?.id, result?.event_id, "capture"));
      await animateCaptureSuccess();
      if (input) {
        input.value = "";
        input.style.height = "";
      }
      clearAttachment();
      state.undoRecord = { id: captureId, inFlight: false };
      setFeedback("");
      showToast("+1 off your mind", "", "Undo", undoCapture);
      await refreshState();
    } catch (error) {
      const code = String(error?.code || "");
      const message = code === "attachments_not_supported"
        ? "This host needs the V2 attachment contract before it can save a file by itself."
        : code === "invalid_request" && attachment && !text.trim()
          ? "This host still requires text for attachments. The V2 attachment contract will allow attachment-only saves."
          : "Couldn’t save that yet. Your capture is still here.";
      setFeedback(message, "error");
      showToast(message, "error");
    } finally {
      state.submitting = false;
      if (submit) submit.disabled = false;
      if (plus) plus.disabled = false;
      if (composer) composer.removeAttribute("aria-busy");
      resizeTextarea();
    }
  };

  const showView = (name, updateHash = true) => {
    const nextView = viewNames.includes(name) ? name : "capture";
    state.activeView = nextView;
    viewNames.forEach((view) => {
      const active = view === nextView;
      const element = $("#view-" + view);
      const nav = $('.nav-item[data-view="' + view + '"]');
      if (element) {
        element.hidden = !active;
        element.classList.toggle("is-active", active);
      }
      if (nav) {
        nav.classList.toggle("is-active", active);
        if (active) nav.setAttribute("aria-current", "page");
        else nav.removeAttribute("aria-current");
      }
    });
    persistLocalState();
    if (updateHash && window.location.hash !== "#" + nextView) history.replaceState(null, "", "#" + nextView);
    if (typeof window.scrollTo === "function") window.scrollTo({ top: 0, behavior: "auto" });
  };

  const triggerInstall = async () => {
    if (!state.installPrompt) return;
    state.installPrompt.prompt();
    await state.installPrompt.userChoice;
    state.installPrompt = null;
    const button = $("#install-button");
    if (button) button.hidden = true;
  };

  const renderQuestionExamples = () => {
    const element = $("#question-chips");
    if (!element) return;
    const examples = [
      "What do I need to do today?",
      "What am I paying for?",
      "What do I know about my car?",
      "What changed recently?",
    ];
    element.innerHTML = examples.map((question) => '<button class="question-chip" type="button" data-question="' + escapeHtml(question) + '">' + escapeHtml(question) + '</button>').join("");
  };

  $$(".nav-item, .brand-button").forEach((button) => button.addEventListener("click", () => showView(button.dataset.view || "capture")));
  $("#capture-input")?.addEventListener("input", resizeTextarea);
  $("#capture-input")?.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      $("#capture-form")?.requestSubmit();
    }
  });
  $("#capture-form")?.addEventListener("submit", submitCapture);
  $("#attachment-button")?.addEventListener("click", () => {
    const menu = $("#attachment-menu");
    if (!menu) return;
    menu.hidden = !menu.hidden;
    $("#attachment-button").setAttribute("aria-expanded", String(!menu.hidden));
    if (!menu.hidden) $(".attachment-option", menu)?.focus();
  });
  $$(".attachment-option").forEach((option) => option.addEventListener("click", () => {
    closeAttachmentMenu();
    selectAttachmentMode(option.dataset.attachmentMode);
  }));
  $("#file-input")?.addEventListener("change", (event) => handleAttachment(event.target.files?.[0]));
  $("#ask-form")?.addEventListener("submit", (event) => {
    event.preventDefault();
    ask($("#ask-input")?.value);
  });
  $("#question-chips")?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-question]");
    if (!button) return;
    const input = $("#ask-input");
    if (input) input.value = button.dataset.question || "";
    ask(button.dataset.question || "");
  });
  $("#memory-search")?.addEventListener("input", (event) => {
    state.memoryQuery = event.target.value;
    renderMemory();
  });
  $("#memory-filters")?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-memory-filter]");
    if (!button) return;
    state.memoryFilter = button.dataset.memoryFilter || "all";
    persistLocalState();
    renderMemory();
  });
  $("#install-button")?.addEventListener("click", triggerInstall);
  document.addEventListener("click", (event) => {
    if (!$("#attachment-menu")?.hidden && !$(".composer-wrap")?.contains(event.target)) closeAttachmentMenu();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeAttachmentMenu();
  });
  window.addEventListener("online", () => { setConnectionStatus("Connected", "online"); refreshState(); });
  window.addEventListener("offline", () => setConnectionStatus("Offline", "offline"));
  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    state.installPrompt = event;
    const button = $("#install-button");
    if (button && !document.documentElement.classList.contains("is-standalone")) button.hidden = false;
  });
  window.addEventListener("appinstalled", () => {
    state.installPrompt = null;
    const button = $("#install-button");
    if (button) button.hidden = true;
  });

  if (window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true) {
    document.documentElement.classList.add("is-standalone");
  }

  renderQuestionExamples();
  resizeTextarea();
  showView(window.location.hash.slice(1), false);
  refreshState();
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => {}));
  }

  if (typeof window !== "undefined") {
    window.BlackholeV2 = {
      fixtureMode,
      normalizeAttention,
      normalizeMemory,
      normalizeAnswer,
      formatMoney,
      humanize,
    };
  }
})();
