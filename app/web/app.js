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
    const unit = firstValue(source.unit, source.units);
    const period = firstValue(source.billing_period, source.period, source.cadence);
    return prefix + formatted + suffix + (unit ? " " + lowercaseFirst(humanize(unit)) : "") + (period ? "/" + lowercaseFirst(humanize(period)) : "");
  };

  const formatDate = (value) => {
    if (value === null || value === undefined || value === "") return "";
    const raw = String(value);
    const parsed = new Date(raw);
    if (Number.isNaN(parsed.getTime())) return humanize(raw);
    return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(parsed);
  };

  const privateValueKeys = new Set([
    "event_id", "source_event_id", "target_event_id", "source_refs", "confirmation_ref",
    "fact_id", "fact_ids", "relation_id", "id", "entity_id", "entity_key", "source_id", "source_key",
    "attachment_id", "blob_ref", "sha256", "hash", "fingerprint", "evidence_id", "projection_run_id",
    "metadata", "semantic_metadata",
  ]);

  const formatValue = (value, depth = 0) => {
    if (depth > 2 || value === null || value === undefined || value === "") return "";
    if (typeof value === "boolean") return value ? "Yes" : "No";
    if (typeof value === "number") return Number.isFinite(value) ? String(value) : "";
    if (typeof value === "string") return value.trim();
    if (Array.isArray(value)) return value.map((item) => formatValue(item, depth + 1)).filter(Boolean).join(", ");
    if (typeof value !== "object") return "";
    if (firstValue(value.amount, value.total, value.price, value.value, value.quantity, value.count) !== undefined) {
      return formatMoney(value);
    }
    const label = firstValue(value.display, value.label, value.name, value.title, value.summary, value.description, value.location, value.date, value.when, value.status);
    if (label !== undefined && typeof label !== "object") return formatValue(label, depth + 1);
    const parts = Object.entries(value)
      .filter(([key, item]) => !privateValueKeys.has(key) && !key.endsWith("_id") && item !== null && item !== undefined && item !== "")
      .map(([key, item]) => {
        const rendered = formatValue(item, depth + 1);
        return rendered ? humanize(key) + ": " + rendered : "";
      })
      .filter(Boolean)
      .slice(0, 4);
    return parts.join(" · ");
  };

  const isDisplayArtifact = (value) => {
    const normalized = String(value ?? "").trim().toLowerCase();
    return !normalized || normalized === "undefined" || normalized === "null" || normalized === "[object object]";
  };

  const displayText = (value, fallback = "") => {
    const safeFallback = isDisplayArtifact(fallback) ? "" : String(fallback);
    if (value === null || value === undefined || value === "") return safeFallback;
    const rendered = typeof value === "string" ? value : formatValue(value);
    return isDisplayArtifact(rendered) ? safeFallback : String(rendered);
  };

  const fileTypeLabel = (attachment) => {
    if (attachment.isImage) return "Image";
    const type = String(attachment.type || "");
    if (type.includes("/")) return type.split("/")[1].split("+")[0].toUpperCase();
    const extension = String(attachment.name || "").split(".").pop();
    return extension && extension !== attachment.name ? extension.toUpperCase() : "File";
  };

  const formatCapturedTime = (value, now = new Date()) => {
    if (!value) return "";
    const captured = new Date(String(value));
    if (Number.isNaN(captured.getTime())) return "";
    const difference = now.getTime() - captured.getTime();
    if (difference >= 0 && difference < 60 * 60 * 1000) {
      const minutes = Math.floor(difference / 60000);
      return minutes < 1 ? "Captured just now" : "Captured " + minutes + " min ago";
    }
    const clock = new Intl.DateTimeFormat(undefined, { hour: "2-digit", minute: "2-digit" }).format(captured);
    const sameDate = captured.toDateString() === now.toDateString();
    if (sameDate) return "Captured today · " + clock;
    return "Captured " + new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(captured) + " · " + clock;
  };

  const humanStatus = (status, capturedAt) => {
    const normalizedStatus = String(status || "").toLowerCase();
    const captured = formatCapturedTime(capturedAt);
    if (captured) {
      const qualifier = normalizedStatus === "inferred"
        ? " · considered interpretation"
        : normalizedStatus === "unknown" ? " · needs clarification" : "";
      return captured + qualifier;
    }
    return ({
      known: "Captured evidence",
      inferred: "Considered interpretation",
      unknown: "Needs clarification",
    })[String(status || "").toLowerCase()] || "Captured evidence";
  };

  const statusClass = (status) => ["known", "inferred", "unknown"].includes(String(status || "").toLowerCase())
    ? String(status).toLowerCase()
    : "known";

  const statusDetails = (status, reason, capturedAt) => {
    if (String(status || "").toLowerCase() === "unknown") {
      const normalizedReason = String(reason || "").toLowerCase();
      if (normalizedReason.includes("conflict")) return "Needs clarification — the notes do not agree.";
      return "Needs clarification";
    }
    return humanStatus(status, capturedAt) + ".";
  };

  const naturalizeAssertion = (item) => {
    const predicate = String(item?.predicate || "").toLowerCase();
    const value = item?.value;
    const subject = displayName(firstValue(item?.entity_name, item?.subject, item?.entity?.name, "This memory"));
    if (item?.summary || item?.display?.summary || item?.text || item?.description) {
      return String(firstValue(item.summary, item.display?.summary, item.text, item.description));
    }
    if (predicate.includes("unknown") || String(item?.knowledge_status).toLowerCase() === "unknown") {
      return "Needs clarification";
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
    if (predicate) return humanize(predicate) + ": " + formatValue(value);
    if (value !== undefined) return subject + ": " + formatValue(value);
    return "A memory Blackhole is keeping nearby";
  };

  const normalizeEvidence = (item) => {
    const captured = formatCapturedTime(firstValue(item?.captured_at, item?.capturedAt, item?.observed_at));
    const evidence = firstValue(item?.evidence, item?.source, item?.source_refs, item?.sources);
    const sourceCount = Array.isArray(evidence)
      ? evidence.filter((ref) => ref !== null && ref !== undefined && String(ref).trim() !== "").length
      : 0;
    if (captured) return captured + (sourceCount > 1 ? " · " + sourceCount + " sources" : "");
    if (Array.isArray(evidence)) {
      return sourceCount === 1 ? "Captured source" : sourceCount > 1 ? sourceCount + " captured sources" : "";
    }
    const rendered = displayText(evidence, "");
    return rendered && !/^capture[:_-]|^event[:_-]|^[a-f0-9]{24,}$/i.test(rendered) ? rendered : "Captured source";
  };

  const formatAttentionTime = (item, now = new Date()) => {
    const lifecycleStatus = String(firstValue(item?.status, "open")).toLowerCase();
    if (lifecycleStatus === "completed" || lifecycleStatus === "cancelled") {
      return lifecycleStatus === "completed" ? "Done" : "Cancelled";
    }
    const timestamp = firstValue(item?.due_at, item?.starts_at);
    const due = timestamp ? new Date(String(timestamp)) : null;
    const explicitState = String(firstValue(item?.state, item?.urgency, "")).toLowerCase();
    if (!due || Number.isNaN(due.getTime())) {
      if (explicitState === "overdue") return "Overdue — time needs clarification";
      if (explicitState === "soon") return "Soon — time needs clarification";
      return displayText(firstValue(item?.display?.when, item?.when, item?.relative_time), "Worth a look");
    }
    const difference = due.getTime() - now.getTime();
    const clock = new Intl.DateTimeFormat(undefined, { hour: "2-digit", minute: "2-digit" }).format(due);
    if (difference <= 0) {
      const minutes = Math.max(1, Math.floor(Math.abs(difference) / 60000));
      return "Overdue by " + minutes + " min · " + clock;
    }
    if (difference < 60 * 60 * 1000) {
      const minutes = Math.max(1, Math.ceil(difference / 60000));
      return "in " + minutes + " min · " + clock;
    }
    const sameDate = due.toDateString() === now.toDateString();
    const tomorrow = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1).toDateString() === due.toDateString();
    if (sameDate) return "today · " + clock;
    if (tomorrow) return "tomorrow · " + clock;
    return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(due) + " · " + clock;
  };

  const attentionUrgency = (item, now = new Date()) => {
    const status = String(firstValue(item?.status, "open")).toLowerCase();
    if (status !== "open") return "upcoming";
    const timestamp = firstValue(item?.due_at, item?.starts_at, item?.dueAt, item?.startsAt);
    const due = timestamp ? new Date(String(timestamp)) : null;
    if (due && !Number.isNaN(due.getTime())) {
      const difference = due.getTime() - now.getTime();
      if (difference <= 0) return "overdue";
      if (difference < 60 * 60 * 1000) return "soon";
    }
    const explicit = String(firstValue(item?.urgency, item?.state, "")).toLowerCase();
    if (["overdue", "soon", "upcoming"].includes(explicit)) return explicit;
    return "upcoming";
  };

  const normalizeAttention = (items) => {
    const source = Array.isArray(items) ? items : [];
    const normalized = source.map((item, index) => {
      const value = item?.value;
      const display = item?.display || {};
      const subject = displayName(displayText(firstValue(item?.entity_name, item?.subject, item?.entity?.name, item?.title), "Something"));
      const predicate = String(item?.predicate || "").toLowerCase();
      const title = displayText(firstValue(item?.title, display.title, item?.label,
        predicate.includes("deadline") || predicate.includes("due") || predicate.includes("renew")
          ? "Renew " + subject
          : predicate.includes("approval")
            ? "Review " + subject
            : subject), "Something");
      const summary = displayText(firstValue(item?.summary, display.summary, item?.description,
        predicate.includes("approval") || value?.reason === "approval required"
          ? "Needs your decision before it can move forward."
          : predicate.includes("deadline") || predicate.includes("due")
            ? "A deadline is coming up."
            : "Worth a look while it is still useful."), "Worth a look while it is still useful.");
      const lifecycleStatus = String(firstValue(item?.status, "open")).toLowerCase();
      const detailObject = item?.details && typeof item.details === "object" ? item.details : {};
      const detailParts = [];
      const capturedLabel = formatCapturedTime(firstValue(item?.captured_at, item?.capturedAt, item?.observed_at));
      if (capturedLabel) detailParts.push(capturedLabel + ".");
      if (detailObject.note && typeof detailObject.note === "string") detailParts.push(detailObject.note.trim());
      if (detailObject.time_status === "coarse_or_ambiguous") detailParts.push("The time is approximate.");
      if (detailObject.time_status === "unreadable_or_ambiguous") detailParts.push("The time still needs clarification.");
      const detail = detailParts.filter(Boolean).join(" ") || "Blackhole kept this because it may need action.";
      const lifecycleState = String(firstValue(item?.state, "")).toLowerCase();
      const rawUrgency = String(firstValue(item?.urgency, display.urgency, "")).toLowerCase();
      const dueValue = firstValue(item?.due_at, item?.starts_at, item?.deadline, value?.deadline, value?.when);
      const rawWhen = firstValue(display.when, display.time, display.relative_time, item?.when, item?.relative_time);
      const urgency = attentionUrgency({ ...item, status: lifecycleStatus, due_at: dueValue }, new Date()) || rawUrgency || (lifecycleState === "overdue" || String(rawWhen || "").toLowerCase().includes("overdue") ? "overdue" : "upcoming");
      const when = formatAttentionTime({ ...item, status: lifecycleStatus, urgency, state: lifecycleState, display });
      return {
        id: String(firstValue(item?.id, item?.fingerprint, item?.event_id, item?.state_key, "attention-" + index)),
        title,
        summary,
        detail,
        when,
        urgency,
        approval: Boolean(item?.approval_required || value?.reason === "approval required" || predicate.includes("approval")),
        evidence: normalizeEvidence(item),
        status: item?.knowledge_status || "known",
        lifecycleStatus,
        unknownReason: typeof item?.unknown_reason === "string" ? item.unknown_reason : "",
        capturedAt: firstValue(item?.captured_at, item?.capturedAt, item?.observed_at) || "",
        dueAt: firstValue(item?.due_at, item?.deadline, value?.deadline, value?.when) || "",
        startsAt: firstValue(item?.starts_at, item?.start_at, value?.starts_at, value?.start_at) || "",
      };
    }).filter((item) => !["completed", "cancelled", "superseded", "done"].includes(item.lifecycleStatus));
    const seen = new Set();
    return normalized.filter((item) => {
      if (seen.has(item.id)) return false;
      seen.add(item.id);
      return true;
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

  const occurrenceMarkers = new Set([
    "occurrence", "event", "episode", "action", "transaction", "visit", "visited",
    "consumption", "consume", "consumes", "consumed", "consuming", "drink", "drinks", "drank", "drinking", "purchase", "purchased",
    "bought", "buy", "buying", "payment", "paid", "pay", "eat", "ate", "eating",
    "run", "ran", "running", "watch", "watched", "watching", "receive", "received",
    "receiving",
  ]);
  const occurrenceStateQualifiers = new Set([
    "account", "balance", "cost", "current", "default", "historical", "location", "method",
    "monthly", "owner", "preferred", "preference", "price", "recurring", "status", "subscription",
  ]);
  const hasOccurrenceMarker = (value) => {
    const normalized = String(value || "").trim().toLowerCase().replace(/[^\w]+/g, "_").replace(/^_+|_+$/g, "");
    if (!normalized) return false;
    const tokens = new Set(normalized.split("_"));
    for (const marker of occurrenceMarkers) {
      if (normalized === marker || (tokens.has(marker) && ![...tokens].some((token) => occurrenceStateQualifiers.has(token)))) return true;
    }
    return false;
  };

  const isOccurrenceSource = (source, metadata = {}) => {
    const semanticState = String(firstValue(metadata.semantic_state, source?.semantic_state, "") || "").toLowerCase();
    if (semanticState === "occurrence" || metadata.occurrence === true || source?.occurrence === true) return true;
    return hasOccurrenceMarker(firstValue(metadata.claim_type, source?.claim_type))
      || hasOccurrenceMarker(firstValue(metadata.semantic_relation, source?.semantic_relation))
      || hasOccurrenceMarker(source?.concept);
  };

  const occurrenceAmount = (fact) => {
    const value = fact?.value;
    if (typeof value === "number" && Number.isFinite(value)) return { amount: value, unit: "" };
    if (!value || typeof value !== "object" || Array.isArray(value)) return null;
    const amount = firstValue(value.amount, value.quantity, value.count, value.total);
    const number = Number(amount);
    if (amount === undefined || !Number.isFinite(number)) return null;
    return { amount: number, unit: String(firstValue(value.unit, value.units, "") || "") };
  };

  const occurrenceSummary = (facts) => {
    const amounts = facts.map(occurrenceAmount).filter(Boolean);
    if (!amounts.length) return "";
    const unit = amounts[0].unit;
    if (amounts.some((item) => item.unit.toLowerCase() !== unit.toLowerCase())) return "";
    const total = amounts.reduce((sum, item) => sum + item.amount, 0);
    const formatted = Number.isInteger(total) ? String(total) : String(Number(total.toFixed(2)));
    return formatted + (unit ? " " + lowercaseFirst(humanize(unit)) : "") + " total across " + facts.length + " captured occurrences";
  };

  const normalizeFact = (item, fallbackEntity, options = {}) => {
    if (typeof item === "string") {
      return {
        text: displayText(item, "Memory"),
        detail: "",
        status: "known",
        evidence: "Captured source",
        unknownReason: "",
        capturedAt: "",
        semanticState: "",
        occurrence: false,
        value: undefined,
        temporal: {},
        isHistory: Boolean(options.isHistory),
      };
    }
    const source = item || {};
    const proposedText = firstValue(source.summary, source.display?.summary, source.text, source.description, source.label);
    const text = displayText(proposedText, naturalizeAssertion({
      ...source,
      subject: source.subject || source.entity_label || fallbackEntity,
      entity_name: source.entity_name || source.entity_label || fallbackEntity,
      predicate: source.predicate || source.concept,
    }));
    const rawDetail = typeof source.detail === "string"
      ? source.detail
      : typeof source.explanation === "string" ? source.explanation : "";
    const metadata = source.metadata && typeof source.metadata === "object" ? source.metadata : source.semantic_metadata && typeof source.semantic_metadata === "object" ? source.semantic_metadata : {};
    const lifecycle = String(firstValue(source.lifecycle_action, metadata.lifecycle_action, "")).toLowerCase();
    const occurrence = isOccurrenceSource(source, metadata);
    const semanticState = occurrence ? "occurrence" : String(firstValue(metadata.semantic_state, source.semantic_state, "") || "").toLowerCase();
    return {
      text,
      detail: displayText(rawDetail, ""),
      status: source.knowledge_status || source.status || "known",
      evidence: normalizeEvidence(source),
      unknownReason: displayText(source.unknown_reason, ""),
      capturedAt: firstValue(source.captured_at, source.capturedAt, source.observed_at) || "",
      semanticState,
      occurrence,
      value: source.value,
      temporal: source.temporal && typeof source.temporal === "object" ? source.temporal : {},
      isHistory: Boolean(options.isHistory || ["complete", "completed", "done", "cancel", "cancelled", "superseded"].includes(lifecycle)),
    };
  };

  const normalizeMemory = (memory) => {
    const groups = new Map();
    const addGroup = (id, name, kind, summary, facts) => {
      const safeName = displayText(name, "Memory");
      const key = displayText(id || safeName || "memory", "memory").toLowerCase();
      if (!groups.has(key)) {
        groups.set(key, {
          id: key,
          name: safeName,
          kind: kindLabel(kind),
          kindKey: String(kind || "memory").toLowerCase(),
          summary: displayText(summary, ""),
          facts: [],
        });
      }
      const group = groups.get(key);
      if (summary && !group.summary) group.summary = displayText(summary, "");
      (Array.isArray(facts) ? facts : []).forEach((fact) => group.facts.push(normalizeFact(fact, name)));
      return group;
    };

    if (!memory || typeof memory !== "object") return [];
    const entities = Array.isArray(memory.entities) ? memory.entities : [];
    entities.forEach((entity, index) => {
      if (!entity || typeof entity !== "object") return;
      const name = displayText(firstValue(entity.name, entity.label, entity.title, entity.display_name, entity.subject), "Memory");
      const facts = firstValue(entity.facts, entity.items, entity.observations) || [];
      addGroup(entity.id || entity.entity_id || name + index, name, entity.kind || entity.type, entity.summary, facts);
    });

    const topics = Array.isArray(memory.topics) ? memory.topics : [];
    topics.forEach((topic, index) => {
      if (!topic || typeof topic !== "object") return;
      const name = displayText(firstValue(topic.name, topic.title, topic.label), "Topic");
      addGroup(topic.id || name + index, name, topic.kind || "topic", topic.summary, topic.items || topic.facts || []);
    });

    const groupsPayload = Array.isArray(memory.groups) ? memory.groups : [];
    groupsPayload.forEach((group, index) => {
      if (!group || typeof group !== "object") return;
      const name = displayText(firstValue(group.name, group.title, group.label), "Memory");
      addGroup(group.id || name + index, name, group.kind || "memory", group.summary, group.items || group.facts || []);
    });

    const structuredFacts = Array.isArray(memory.current_facts) ? memory.current_facts : Array.isArray(memory.facts) ? memory.facts : [];
    structuredFacts.forEach((fact, index) => {
      const source = typeof fact === "object" && fact ? fact : { text: String(fact) };
      const name = displayText(firstValue(source.entity_label, source.entity_name, source.entity?.name, source.subject), "Memory");
      const kind = firstValue(source.entity_kind, source.entity?.kind, source.kind, "memory");
      const group = addGroup(source.entity_key || source.entity_id || name + index, name, kind, "", []);
      group.facts.push(normalizeFact(source, name));
    });

    // History is evidence subordinate to its entity/topic card. A row with no
    // stable context is intentionally omitted rather than shown as a
    // misleading standalone card.
    const history = Array.isArray(memory.fact_history) ? memory.fact_history : [];
    history.forEach((fact, index) => {
      if (!fact || typeof fact !== "object") return;
      const historyMetadata = fact.metadata && typeof fact.metadata === "object" ? fact.metadata : fact.semantic_metadata && typeof fact.semantic_metadata === "object" ? fact.semantic_metadata : {};
      // Projected occurrence rows are already current evidence. They may also
      // appear in a generic history payload, but must not be relabeled as
      // previous state or shown as a conflict.
      const historyOperation = String(firstValue(fact.semantic_relation, fact.operation, "") || "").toLowerCase();
      const isCorrection = ["correction", "supersede", "supersession", "contradiction", "resolution", "resolves_uncertainty", "reschedule"].some((marker) => historyOperation.includes(marker));
      if (isOccurrenceSource(fact, historyMetadata) && !isCorrection) return;
      const name = displayText(firstValue(fact.entity_label, fact.entity_name, fact.entity?.name, fact.subject), "");
      if (!name) return;
      const kind = firstValue(fact.entity_kind, fact.entity?.kind, fact.kind, "memory");
      const group = addGroup(fact.entity_key || fact.entity_id || name, name, kind, "", []);
      const normalized = normalizeFact(fact, name, { isHistory: true });
      const operation = String(firstValue(fact.semantic_relation, fact.operation, "")).toLowerCase();
      const prefix = ["correction", "supersede", "supersession", "meaningful_change", "change"].some((marker) => operation.includes(marker))
        ? "Changed from "
        : "Previously: ";
      group.facts.push({
        ...normalized,
        text: prefix + normalized.text,
        detail: normalized.detail || "Earlier captured evidence for this memory.",
      });
    });

    Object.entries(memory).forEach(([sectionKey, sectionItems]) => {
      if (["entities", "topics", "groups", "items", "facts", "current_facts", "fact_history", "attention", "counts", "approval", "recent_captures", "processing", "relationships", "sources", "attachments", "retracted_event_ids", "store_version", "projection_version", "projection_run_id"].includes(sectionKey)) return;
      if (!Array.isArray(sectionItems)) return;
      sectionItems.forEach((item, index) => {
        const source = typeof item === "object" && item ? item : { text: String(item) };
        const name = displayText(firstValue(source.entity_name, source.entity?.name, source.subject, source.title), kindLabel(sectionKey));
        const kind = firstValue(source.entity_kind, source.entity?.kind, source.kind, sectionKey);
        const group = addGroup(source.entity_id || source.entity?.id || name, name, kind, "", []);
        group.facts.push(normalizeFact(source, name));
      });
    });

    return [...groups.values()].filter((group) => group.facts.length).map((group) => {
      const facts = [...group.facts].sort((left, right) => Number(left.isHistory) - Number(right.isHistory));
      const occurrenceFacts = facts.filter((fact) => !fact.isHistory && fact.occurrence && String(fact.status || "").toLowerCase() !== "unknown");
      return {
        ...group,
        summary: group.summary || occurrenceSummary(occurrenceFacts),
        facts,
      };
    });
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
      capturedAt: normalized.capturedAt,
      semanticState: normalized.semanticState,
      occurrence: normalized.occurrence,
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
    const rawMessage = displayText(firstValue(answer.message, answer.answer), "");
    if (mode === "processing" || mode === "pending") {
      return {
        status: "processing",
        summary: "Still understanding your recent captures.",
        helper: "Your capture is saved. Check back soon for useful memory and attention.",
        groups: [],
      };
    }
    if (mode === "processing_failed" || mode === "failed") {
      return {
        status: "processing_failed",
        summary: "Some recent captures couldn't be understood yet.",
        helper: "Your captures are still saved. Try again when your local provider is available.",
        groups: [],
      };
    }
    if (mode === "no_data") {
      return {
        status: "no_data",
        summary: "No processed memory yet.",
        helper: "Capture something first, then ask again.",
        groups: [],
      };
    }
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
      const source = group && typeof group === "object" ? group : {};
      const items = firstValue(source.items, source.assertions, []) || [];
      groups.push({
        id: displayText(firstValue(source.id, source.title), "group-" + index),
        title: displayText(firstValue(source.title, source.name), "Related memories"),
        items: Array.isArray(items) ? items.map(normalizeSupportItem) : [],
      });
    });

    const sections = Array.isArray(answer.sections) ? answer.sections : [];
    sections.forEach((section, index) => {
      const source = section && typeof section === "object" ? section : {};
      const items = firstValue(source.items, source.assertions, []) || [];
      groups.push({
        id: displayText(firstValue(source.id, source.title), "section-" + index),
        title: displayText(source.title, "Related memories"),
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
    const summary = displayText(firstValue(answer.summary, answer.answer, answer.direct_answer, answer.text),
      status === "no_match" ? "I couldn’t find that in your memory yet." : deriveAnswerSummary(answer, meaningfulGroups));
    const clarification = answer.clarification && typeof answer.clarification === "object"
      ? displayText(answer.clarification.prompt, "")
      : "";
    return {
      status,
      summary,
      helper: status === "no_match" ? "Try a person, place, thing, task, or recent change." : "",
      groups: meaningfulGroups,
      clarificationPrompt: clarification,
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
          captured_at: "2026-08-31T02:56:00Z",
          knowledge_status: "known",
        },
        {
          id: "attention-parking",
          title: "Renew parking permit",
          summary: "The permit is due on Sep 12.",
          display: { when: "Sep 12", urgency: "upcoming" },
          detail: "A date you mentioned while thinking about the apartment.",
          captured_at: "2026-08-30T13:20:00Z",
          knowledge_status: "known",
        },
        {
          id: "attention-approval",
          title: "Review the PocketWave change",
          summary: "A price change is waiting for your decision.",
          display: { when: "Worth a look", urgency: "upcoming" },
          detail: "Blackhole found a proposed change; nothing has been changed for you.",
          captured_at: "2026-08-29T15:10:00Z",
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
              { summary: "Likes the green pasta from Lidl", status: "known", captured_at: "2026-08-30T12:15:00Z" },
              { summary: "Birthday is still unclear", status: "unknown", unknown_reason: "not stated", evidence: "No clear source yet" },
            ],
          },
          {
            id: "car",
            name: "Car",
            kind: "thing",
            summary: "A few observations about your car.",
            facts: [
              { summary: "Started knocking at the front-left", status: "known", captured_at: "2026-08-30T11:42:00Z" },
            ],
          },
          {
            id: "basement-keys",
            name: "Basement keys",
            kind: "thing",
            summary: "A small detail worth being able to find.",
            facts: [
              { summary: "At Mum’s place", status: "known", captured_at: "2026-08-30T10:05:00Z" },
            ],
          },
          {
            id: "pocketwave",
            name: "PocketWave",
            kind: "money",
            summary: "A recurring cost with a change in its history.",
            facts: [
              { summary: "€11/month", status: "known", captured_at: "2026-08-30T09:12:00Z" },
              { summary: "Changed from €9 on Sep 1", status: "known", captured_at: "2026-08-30T09:18:00Z" },
            ],
          },
          {
            id: "parking-permit",
            name: "Parking permit",
            kind: "task",
            summary: "One deadline to keep nearby.",
            facts: [
              { summary: "Renew by Sep 12", status: "known", captured_at: "2026-08-30T08:40:00Z" },
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
            { summary: "PocketWave · €11/month", detail: "Changed from €9 on Sep 1", status: "known", captured_at: "2026-08-30T09:12:00Z" },
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
          items: [{ summary: "Started knocking at the front-left", status: "known", captured_at: "2026-08-30T11:42:00Z" }],
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
            { summary: "PocketWave changed from €9 to €11/month", detail: "The new price starts Sep 1.", status: "known", captured_at: "2026-08-30T09:18:00Z" },
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

  const bufferToBase64 = (buffer) => {
    const bytes = new Uint8Array(buffer);
    let binary = "";
    const chunkSize = 0x8000;
    for (let offset = 0; offset < bytes.length; offset += chunkSize) {
      binary += String.fromCharCode(...bytes.subarray(offset, offset + chunkSize));
    }
    return window.btoa(binary);
  };

  const serializeAttachment = async (attachment) => {
    if (!attachment?.file) return null;
    const dataBase64 = typeof attachment.file.arrayBuffer === "function"
      ? bufferToBase64(await attachment.file.arrayBuffer())
      : await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onerror = () => reject(new ClientError("Blackhole could not read that attachment.", "attachment_read_failed"));
        reader.onload = () => resolve(String(reader.result || "").split(",", 2)[1] || "");
        reader.readAsDataURL(attachment.file);
      });
    return {
      filename: attachment.name,
      mime_type: attachment.type,
      data_base64: dataBase64,
    };
  };

  const client = {
    fixture: fixtureMode,
    async getState() {
      if (fixtureMode) {
        await wait(40);
        return fixtureState;
      }
      const payload = await api("/api/v2/state");
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
      const attachment = await serializeAttachment(payload.attachment);
      const request = {
        source_type: payload.attachment ? (payload.attachment.isImage ? "image" : "document") : "text",
      };
      if (payload.text && payload.text.trim()) request.text = payload.text;
      if (attachment) request.attachment = attachment;
      return api("/api/v2/capture", {
        method: "POST",
        body: JSON.stringify(request),
      });
    },
    async retractCapture(captureId) {
      if (fixtureMode) {
        await wait(60);
        return { ok: true, retracted: true, capture: { event_id: captureId } };
      }
      return api("/api/v2/retract", {
        method: "POST",
        body: JSON.stringify({ event_id: captureId, reason: "user undo" }),
      });
    },
    async setAttentionStatus(fingerprint, status) {
      if (fixtureMode) {
        await wait(40);
        return { ok: true, attention: { fingerprint, status } };
      }
      return api("/api/v2/attention/status", {
        method: "POST",
        body: JSON.stringify({ fingerprint, status }),
      });
    },
    async ask(question, thread = []) {
      if (fixtureMode) {
        await wait(180);
        if (fixtureUnavailable) {
          throw new ClientError("Your local provider is unavailable right now.", "provider_unavailable", 503);
        }
        return { ok: true, answer: fixtureAnswer(question) };
      }
      return api("/api/v2/ask", {
        method: "POST",
        body: JSON.stringify({ question, thread }),
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
    processing: null,
    processingPollTimer: null,
    attentionTimer: null,
    captureStatusVisible: false,
    toastTimer: null,
    toastAction: null,
    undoRecord: null,
    lastAskQuestion: "",
    askMessages: [],
    askGeneration: 0,
    openDisclosures: new Set(),
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

  const createDisclosureState = (initial = new Set()) => {
    const openDisclosures = initial instanceof Set ? initial : new Set(initial);
    const detailsFor = (root) => {
      if (!root || typeof root.querySelectorAll !== "function") return [];
      return [...root.querySelectorAll('details[data-disclosure-id]')];
    };
    const idFor = (details) => details?.dataset?.disclosureId || "";
    return {
      remember(root) {
        detailsFor(root).forEach((details) => {
          const id = idFor(details);
          if (!id) return;
          if (details.open) openDisclosures.add(id);
          else openDisclosures.delete(id);
        });
        return this;
      },
      bind(root) {
        this.remember(root);
        detailsFor(root).forEach((details) => {
          if (typeof details.addEventListener !== "function") return;
          details.addEventListener("toggle", () => {
            const id = idFor(details);
            if (!id) return;
            if (details.open) openDisclosures.add(id);
            else openDisclosures.delete(id);
          });
        });
        return this;
      },
      restore(root) {
        detailsFor(root).forEach((details) => {
          const id = idFor(details);
          if (id) details.open = openDisclosures.has(id);
        });
        return this;
      },
      has(id) {
        return openDisclosures.has(id);
      },
      values() {
        return [...openDisclosures];
      },
    };
  };

  const disclosureState = createDisclosureState(state.openDisclosures);
  const rememberDisclosureState = (root) => disclosureState.remember(root);
  const bindDisclosureState = (root) => disclosureState.bind(root);

  const disclosureChevron = '<span class="disclosure-chevron" aria-hidden="true"><svg viewBox="0 0 24 24"><use href="#icon-chevron"></use></svg></span>';

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

  const processingCounts = (processing) => processing?.counts || {};

  const processingFeedback = (processing) => {
    const counts = processingCounts(processing);
    const status = String(processing?.status || "").toLowerCase();
    const failed = Number(counts.failed || 0);
    const pending = Number(counts.pending || 0);
    const active = Number(counts.processing || 0);
    if (failed > 0 || status === "failed") return { message: "Some recent captures couldn't be understood yet. Your captures are still saved.", kind: "error" };
    if (pending > 0 || active > 0 || status === "pending" || status === "processing") return { message: "Saved. Understanding in the background…", kind: "" };
    return { message: "Saved.", kind: "" };
  };

  const processingNotice = (processing) => {
    const counts = processingCounts(processing);
    const status = String(processing?.status || "").toLowerCase();
    if (Number(counts.failed || 0) > 0 || status === "failed") {
      return {
        kind: "error",
        title: "Some recent captures couldn't be understood yet.",
        message: "Your captures are still saved. Try again when your local provider is available.",
      };
    }
    if (Number(counts.pending || 0) > 0 || Number(counts.processing || 0) > 0 || status === "pending" || status === "processing") {
      return {
        kind: "pending",
        title: "Still understanding your recent captures.",
        message: "Your captures are saved; useful memory and attention will appear as understanding completes.",
      };
    }
    return null;
  };

  const renderProcessingNotice = (selector) => {
    const element = $(selector);
    if (!element) return;
    const notice = processingNotice(state.processing);
    if (!notice) {
      element.hidden = true;
      element.innerHTML = "";
      return;
    }
    element.hidden = false;
    element.innerHTML = '<div class="processing-notice is-' + escapeHtml(notice.kind) + '" role="status">' +
      (notice.kind === "error"
        ? '<span class="processing-notice-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#icon-error"></use></svg></span>'
        : '<span class="processing-dots" aria-hidden="true"><i></i><i></i><i></i></span>') +
      '<div><h3>' + escapeHtml(notice.title) + '</h3><p>' + escapeHtml(notice.message) + '</p></div>' +
      '</div>';
  };

  const scheduleProcessingPoll = () => {
    if (fixtureMode || state.processingPollTimer) return;
    const counts = processingCounts(state.processing);
    if (Number(counts.pending || 0) <= 0 && Number(counts.processing || 0) <= 0) return;
    state.processingPollTimer = window.setTimeout(async () => {
      state.processingPollTimer = null;
      if (document.hidden) {
        scheduleProcessingPoll();
        return;
      }
      await refreshState();
    }, 650);
  };

  const updateCaptureProcessingFeedback = () => {
    if (!state.captureStatusVisible || state.submitting) return;
    const feedback = processingFeedback(state.processing);
    setFeedback(feedback.message, feedback.kind);
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
    renderProcessingNotice("#attention-processing");
    const now = new Date();
    const items = state.attention.map((item) => ({
      ...item,
      urgency: attentionUrgency({ status: item.lifecycleStatus, due_at: item.dueAt, starts_at: item.startsAt }, now),
      when: formatAttentionTime({ status: item.lifecycleStatus, due_at: item.dueAt, starts_at: item.startsAt, urgency: item.urgency, state: item.urgency }, now),
    }));
    rememberDisclosureState(element);
    if (!items.length) {
      renderEmpty(element, "Nothing needs your attention.", "Blackhole will only interrupt when something is worth acting on.", "check");
      return;
    }
    element.innerHTML = items.map((item) => {
      const status = statusClass(item.status);
      const lifecycleStatus = item.lifecycleStatus || "open";
      const lifecycleLabel = lifecycleStatus === "completed"
        ? "Completed"
        : lifecycleStatus === "cancelled"
          ? "Cancelled"
          : item.urgency === "overdue"
            ? "Overdue"
            : item.urgency === "soon" ? "Soon" : "Upcoming";
      return '<article class="attention-card urgency-' + escapeHtml(item.urgency) + (item.approval ? " is-approval" : "") + '">' +
        '<div class="attention-card-main">' +
          '<span class="attention-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#icon-attention"></use></svg></span>' +
          '<div class="attention-copy"><h3>' + escapeHtml(item.title) + '</h3><p>' + escapeHtml(item.summary) + '</p></div>' +
          '<span class="attention-when">' + escapeHtml(item.when) + '</span>' +
        '</div>' +
        '<footer class="attention-card-footer">' +
          '<div class="attention-card-meta">' +
          (item.approval && lifecycleStatus === "open" ? '<span class="attention-state">Needs your decision</span>' : '<span class="attention-state">' + escapeHtml(lifecycleLabel) + '</span>') +
            '<details class="evidence-details" data-disclosure-id="attention:' + escapeHtml(item.id) + '"' + (state.openDisclosures.has("attention:" + item.id) ? " open" : "") + '><summary><span>Why this is here</span>' + disclosureChevron + '</summary><div class="detail-copy">' + (item.detail ? '<p>' + escapeHtml(item.detail) + '</p>' : "") + '<p class="detail-meta">' + escapeHtml(statusDetails(item.status, item.unknownReason, item.capturedAt)) + (item.evidence ? ' · ' + escapeHtml(item.evidence) : "") + '</p></div></details>' +
          '</div>' +
          '<div class="attention-action-area">' +
            '<div class="attention-actions">' +
              (lifecycleStatus === "open" ? '<button class="quiet-button attention-complete" type="button" data-attention-complete="' + escapeHtml(item.id) + '">Done</button>' : '') +
            '</div>' +
          '</div>' +
        '</footer>' +
      '</article>';
    }).join("");
    bindDisclosureState(element);
  };

  const scheduleAttentionTicker = () => {
    if (fixtureMode || state.attentionTimer) return;
    if (!state.attention.length) return;
    state.attentionTimer = window.setTimeout(() => {
      state.attentionTimer = null;
      if (typeof document !== "undefined" && document.hidden) {
        scheduleAttentionTicker();
        return;
      }
      renderAttention();
      updateAttentionBadge();
      scheduleAttentionTicker();
    }, Math.min(60000, 60000 - (Date.now() % 60000) + 80));
  };

  const completeAttention = async (button) => {
    const fingerprint = button?.dataset?.attentionComplete;
    if (!fingerprint || button.disabled) return;
    button.disabled = true;
    const previous = state.attention;
    state.attention = previous.filter((item) => item.id !== fingerprint);
    renderAttention();
    updateAttentionBadge();
    try {
      await client.setAttentionStatus(fingerprint, "completed");
      showToast("Marked done");
      await refreshState();
    } catch (_error) {
      state.attention = previous;
      renderAttention();
      updateAttentionBadge();
      button.disabled = false;
      showToast("Couldn’t update that yet.", "error");
    }
  };

  const updateAttentionBadge = () => {
    const badge = $("#nav-attention");
    if (!badge) return;
    const count = state.attention.filter((item) => item.lifecycleStatus === "open").length;
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

  const factClarificationPrompt = (entity, fact) => {
    const name = displayText(entity?.name, "this memory");
    const text = displayText(fact?.text, "the unresolved detail");
    return 'Can you clarify this memory about ' + name + ': ' + text + '?';
  };

  const formatOccurrenceWhen = (fact) => {
    const temporal = fact?.temporal && typeof fact.temporal === "object" ? fact.temporal : {};
    const raw = firstValue(temporal.normalized, temporal.date, fact?.capturedAt);
    if (!raw) return displayText(temporal.expression, "");
    const parsed = new Date(String(raw));
    if (Number.isNaN(parsed.getTime())) return displayText(temporal.expression, "");
    const now = new Date();
    if (parsed.toDateString() === now.toDateString()) return "Today";
    const yesterday = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
    if (parsed.toDateString() === yesterday.toDateString()) return "Yesterday";
    return formatDate(raw);
  };

  const renderMemory = () => {
    const element = $("#memory-list");
    if (!element) return;
    rememberDisclosureState(element);
    renderProcessingNotice("#memory-processing");
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
      const facts = [...entity.facts].sort((left, right) => Number(left.isHistory) - Number(right.isHistory));
      const currentFacts = facts.filter((fact) => !fact.isHistory);
      const certainCurrentFacts = currentFacts.filter((fact) => String(fact.status || "").toLowerCase() !== "unknown" && !fact.occurrence);
      const occurrenceFacts = currentFacts.filter((fact) => String(fact.status || "").toLowerCase() !== "unknown" && fact.occurrence);
      const uncertainCurrentFacts = currentFacts.filter((fact) => String(fact.status || "").toLowerCase() === "unknown");
      const historicalFacts = facts.filter((fact) => fact.isHistory);
      const renderFact = (fact) => {
        const status = statusClass(fact.status);
        const clarification = String(fact.status || "").toLowerCase() === "unknown" && !fact.isHistory
          ? '<button class="quiet-button clarify-button" type="button" data-clarify-question="' + escapeHtml(factClarificationPrompt(entity, fact)) + '">Clarify in Ask</button>'
          : "";
        const when = fact.occurrence ? formatOccurrenceWhen(fact) : "";
        return '<li class="memory-fact is-' + status + (fact.isHistory ? " is-history" : "") + (fact.occurrence ? " is-occurrence" : "") + '">' +
          '<span class="fact-marker" aria-hidden="true"></span>' +
          '<span class="fact-copy"><span>' + escapeHtml(fact.text) + '</span>' +
          (when ? '<span class="occurrence-when">' + escapeHtml(when) + '</span>' : "") +
          '<span class="fact-status">' + escapeHtml(humanStatus(fact.status, fact.capturedAt)) + '</span>' + clarification + '</span>' +
        '</li>';
      };
      const historyId = "memory:" + entity.id + ":history";
      const occurrenceId = "memory:" + entity.id + ":occurrences";
      const occurrenceMarkup = occurrenceFacts.length
        ? '<details class="evidence-details memory-occurrences" data-disclosure-id="' + escapeHtml(occurrenceId) + '"' + (state.openDisclosures.has(occurrenceId) ? " open" : "") + '><summary><span>Occurrences · ' + occurrenceFacts.length + '</span>' + disclosureChevron + '</summary><ul class="memory-facts memory-occurrence-list">' + occurrenceFacts.map(renderFact).join("") + '</ul></details>'
        : "";
      const historyMarkup = historicalFacts.length
        ? '<details class="evidence-details memory-history-disclosure" data-disclosure-id="' + escapeHtml(historyId) + '"' + (state.openDisclosures.has(historyId) ? " open" : "") + '><summary class="memory-history-label"><span>History · ' + historicalFacts.length + '</span>' + disclosureChevron + '</summary><ul class="memory-facts memory-history">' + historicalFacts.map(renderFact).join("") + '</ul></details>'
        : "";
      return '<article class="memory-card">' +
        '<header class="memory-card-header">' +
          '<span class="entity-avatar" aria-hidden="true">' + escapeHtml(initial) + '</span>' +
          '<div class="entity-heading"><h3>' + escapeHtml(entity.name) + '</h3><p>' + escapeHtml(entity.kind) + '</p></div>' +
          '<span class="entity-fact-count">' + entity.facts.length + '</span>' +
        '</header>' +
        (entity.summary ? '<p class="memory-card-summary">' + escapeHtml(entity.summary) + '</p>' : "") +
        (certainCurrentFacts.length ? '<div class="memory-subsection-label">Current</div><ul class="memory-facts">' + certainCurrentFacts.map(renderFact).join("") + '</ul>' : "") +
        (uncertainCurrentFacts.length ? '<div class="memory-subsection-label is-uncertain">Needs clarification</div><ul class="memory-facts memory-uncertain">' + uncertainCurrentFacts.map(renderFact).join("") + '</ul>' : "") +
        occurrenceMarkup + historyMarkup +
        '<details class="evidence-details memory-evidence" data-disclosure-id="memory:' + escapeHtml(entity.id) + '"' + (state.openDisclosures.has("memory:" + entity.id) ? " open" : "") + '><summary><span>Why Blackhole knows this</span>' + disclosureChevron + '</summary><div class="detail-copy"><p>' +
          escapeHtml(facts.map((fact) => fact.text + " — " + statusDetails(fact.status, fact.unknownReason, fact.capturedAt) + (fact.evidence ? ". " + fact.evidence : "")).join(" ")) +
        '</p></div></details>' +
      '</article>';
    }).join("");
    bindDisclosureState(element);
  };

  const renderUnavailableState = () => {
    state.processing = null;
    state.attention = [];
    state.memoryEntities = [];
    updateAttentionBadge();
    renderProcessingNotice("#attention-processing");
    renderEmpty($("#attention-list"), "Attention is unavailable right now.", "Your saved captures are safe. Try again when Blackhole is reachable.", "attention");
    renderMemoryFilters();
    renderMemorySummary();
    renderProcessingNotice("#memory-processing");
    renderEmpty($("#memory-list"), "Memory is unavailable right now.", "Your saved captures are safe. Try again when Blackhole is reachable.", "attention");
  };

  const renderState = (rawState) => {
    state.dataAvailable = true;
    state.processing = rawState?.processing || null;
    const rawAttention = Array.isArray(rawState?.attention) ? rawState.attention : rawState?.attention?.items;
    state.attention = normalizeAttention(rawAttention);
    state.memoryEntities = normalizeMemory(rawState?.memory || rawState);
    updateAttentionBadge();
    renderAttention();
    if (!state.attention.length && state.attentionTimer) {
      window.clearTimeout(state.attentionTimer);
      state.attentionTimer = null;
    }
    scheduleAttentionTicker();
    renderMemory();
    updateCaptureProcessingFeedback();
    scheduleProcessingPoll();
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
    renderAskConversation(true);
  };

  const answerIcon = (kind) => kind === "error" ? "error" : kind === "no-match" ? "search" : "spark";

  const navigateToAskWithPrompt = (prompt) => {
    const text = displayText(prompt, "");
    showView("ask");
    const input = $("#ask-input");
    if (!input) return;
    input.value = text;
    input.focus();
    if (typeof input.setSelectionRange === "function") {
      const end = text.length;
      input.setSelectionRange(end, end);
    }
  };

  const renderAssistantMarkup = (message, messageIndex) => {
    if (message.transient) {
      const transient = message.transient;
      return '<article class="chat-message assistant-message"><div class="answer-state is-' + escapeHtml(transient.kind || "empty") + '">' +
        '<span class="answer-state-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#icon-' + answerIcon(transient.kind) + '"></use></svg></span>' +
        '<div><h3>' + escapeHtml(transient.title) + '</h3><p>' + escapeHtml(transient.message) + '</p>' +
        (transient.actionLabel ? '<button class="quiet-button" type="button" data-answer-action-index="' + messageIndex + '">' + escapeHtml(transient.actionLabel) + '</button>' : "") +
        '</div></div></article>';
    }
    const normalized = message.answer || {};
    if (normalized.status === "processing" || normalized.status === "processing_failed" || normalized.status === "no_data" || normalized.status === "unsupported" || normalized.status === "no_match") {
      const copy = normalized.status === "processing"
        ? ["Still understanding your recent captures.", "Your capture is saved. Check back soon for useful memory and attention.", "processing"]
        : normalized.status === "processing_failed"
          ? ["Some recent captures couldn't be understood yet.", "Your captures are still saved. Try again when your local provider is available.", "error"]
          : normalized.status === "no_data"
            ? ["No processed memory yet.", normalized.helper, "no-match"]
            : normalized.status === "unsupported"
              ? ["Let’s try that another way.", normalized.helper, "no-match"]
              : ["Nothing clear came back yet.", normalized.summary, "no-match"];
      return '<article class="chat-message assistant-message"><div class="answer-state is-' + copy[2] + '">' +
        '<span class="answer-state-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#icon-' + answerIcon(copy[2]) + '"></use></svg></span>' +
        '<div><h3>' + escapeHtml(copy[0]) + '</h3><p>' + escapeHtml(displayText(copy[1], "")) + '</p>' +
        (normalized.status === "processing_failed" ? '<button class="quiet-button" type="button" data-answer-action-index="' + messageIndex + '">Try again</button>' : "") +
        '</div></div></article>';
    }
    const groups = Array.isArray(normalized.groups) ? normalized.groups.filter((group) => Array.isArray(group.items) && group.items.length) : [];
    const relatedCount = groups.reduce((count, group) => count + group.items.length, 0);
    const groupMarkup = groups.map((group) => '<section class="answer-group"><h3>' + escapeHtml(displayText(group.title, "Related memories")) + '</h3><ul class="support-list">' +
      group.items.map((item) => '<li class="support-item is-' + statusClass(item.status) + '">' +
        '<span class="fact-marker" aria-hidden="true"></span><span class="support-copy"><span>' + escapeHtml(displayText(item.text, "Memory")) + '</span>' +
        (item.detail ? '<span class="support-detail">' + escapeHtml(displayText(item.detail, "")) + '</span>' : "") +
        '<span class="support-detail">' + escapeHtml(statusDetails(item.status, item.unknownReason, item.capturedAt) + (item.evidence ? " · " + item.evidence : "")) + '</span>' +
      '</li>').join("") + '</ul></section>').join("");
    const related = relatedCount ? '<details class="evidence-details related-memories" data-disclosure-id="ask:' + messageIndex + ':related"' + (state.openDisclosures.has("ask:" + messageIndex + ":related") ? " open" : "") + '><summary><span>Supporting memories · ' + relatedCount + '</span>' + disclosureChevron + '</summary><div class="detail-copy answer-groups">' + groupMarkup + '</div></details>' : "";
    const clarification = normalized.clarificationPrompt
      ? '<button class="quiet-button clarify-button" type="button" data-clarify-answer-index="' + messageIndex + '" data-clarify-question="' + escapeHtml(normalized.clarificationPrompt) + '">Clarify in Ask</button>'
      : "";
    return '<article class="chat-message assistant-message"><div class="chat-assistant-primary"><span class="answer-spark"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#icon-spark"></use></svg></span><div><p>' + escapeHtml(displayText(normalized.summary, "Here’s what I found in your memory:")) + '</p>' + clarification + '</div></div>' + related + '<p class="answer-grounding">Based on what you’ve captured so far.</p></article>';
  };

  const askIsNearBottom = () => {
    if (typeof document === "undefined" || typeof window === "undefined") return true;
    const documentHeight = Math.max(document.body?.scrollHeight || 0, document.documentElement?.scrollHeight || 0);
    return documentHeight - (window.scrollY + window.innerHeight) < 180;
  };

  const settleAskScroll = (shouldStick) => {
    if (!shouldStick || typeof window === "undefined" || typeof window.scrollTo !== "function") return;
    const move = () => window.scrollTo({
      top: Math.max(document.documentElement?.scrollHeight || 0, document.body?.scrollHeight || 0),
      behavior: prefersReducedMotion() ? "auto" : "smooth",
    });
    if (typeof window.requestAnimationFrame === "function") window.requestAnimationFrame(move);
    else move();
  };

  const renderAskConversation = (loading = false) => {
    const output = $("#answer-output");
    if (!output) return;
    const shouldStick = askIsNearBottom();
    const messages = state.askMessages.map((message, index) => {
      if (message.role === "user") {
        return '<article class="chat-message user-message"><p>' + escapeHtml(displayText(message.text, "")) + '</p></article>';
      }
      return renderAssistantMarkup(message, index);
    });
    if (loading) {
      messages.push('<article class="chat-message assistant-message"><div class="answer-loading"><span class="loading-dots" aria-hidden="true"><i></i><i></i><i></i></span><div><h3>Looking through your memory…</h3><p>Just a moment.</p></div></div></article>');
    }
    output.innerHTML = messages.join("");
    bindDisclosureState(output);
    settleAskScroll(shouldStick);
    $$("[data-answer-action-index]", output).forEach((button) => {
      const index = Number(button.dataset.answerActionIndex);
      const message = state.askMessages[index];
      if (message?.transient?.action) button.addEventListener("click", message.transient.action);
      else if (message?.answer?.status === "processing_failed") button.addEventListener("click", () => refreshState());
    });
    $$("[data-clarify-answer-index]", output).forEach((button) => {
      button.addEventListener("click", () => navigateToAskWithPrompt(button.dataset.clarifyQuestion || ""));
    });
  };

  const renderAnswerState = (title, message, kind = "empty", actionLabel = "", action = null) => {
    const output = $("#answer-output");
    if (!output) return;
    output.removeAttribute("aria-busy");
    state.askMessages.push({ role: "assistant", transient: { title, message, kind, actionLabel, action } });
    renderAskConversation();
  };

  const renderAnswer = (normalized) => {
    const output = $("#answer-output");
    if (!output) return;
    output.removeAttribute("aria-busy");
    state.askMessages.push({ role: "assistant", answer: normalized });
    renderAskConversation();
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

  const askThreadContext = () => state.askMessages
    .map((message) => {
      if (message.role === "user") return { role: "user", text: displayText(message.text, "") };
      const answer = message.answer || {};
      const transient = message.transient || {};
      return {
        role: "assistant",
        text: displayText(firstValue(answer.summary, answer.answer, transient.message), ""),
      };
    })
    .filter((item) => item.text)
    .slice(-8);

  const resetAskThread = () => {
    if (state.asking) return;
    state.askMessages = [];
    state.lastAskQuestion = "";
    state.askGeneration += 1;
    renderQuestionExamples();
    renderAskConversation();
    const input = $("#ask-input");
    if (input) input.focus();
  };

  const ask = async (question) => {
    const normalizedQuestion = String(question || "").trim();
    if (!normalizedQuestion || state.asking) return;
    state.asking = true;
    state.lastAskQuestion = normalizedQuestion;
    const generation = state.askGeneration;
    const thread = askThreadContext();
    state.askMessages.push({ role: "user", text: normalizedQuestion });
    renderQuestionExamples();
    const input = $("#ask-input");
    if (input) input.value = "";
    renderAnswerLoading();
    try {
      const payload = await client.ask(normalizedQuestion, thread);
      if (generation !== state.askGeneration) return;
      renderAnswer(normalizeAnswer(payload));
    } catch (error) {
      if (generation !== state.askGeneration) return;
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
      state.captureStatusVisible = true;
      state.undoRecord = { id: captureId, inFlight: false };
      state.processing = result.processing || { status: result.capture?.processing_status || "pending" };
      updateCaptureProcessingFeedback();
      showToast("+1 off your mind", "", "Undo", undoCapture);
      await refreshState();
    } catch (error) {
      const code = String(error?.code || "");
      const message = code === "attachments_not_supported"
        ? "This host cannot save attachments yet. Your text capture is still safe."
        : code === "attachment_read_failed"
          ? "Blackhole could not read that attachment. Choose it again and retry."
        : code === "invalid_request" && attachment && !text.trim()
          ? "Blackhole could not save that attachment. Choose a smaller or supported file and retry."
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

  const shouldShowAskExamples = (messages) => !Array.isArray(messages) || messages.length === 0;

  const renderQuestionExamples = () => {
    const element = $("#question-chips");
    if (!element) return;
    const heading = $("#ask-examples-heading");
    const hasConversation = !shouldShowAskExamples(state.askMessages);
    element.hidden = hasConversation;
    if (heading) heading.hidden = hasConversation;
    if (hasConversation) return;
    const examples = [
      "What do I need to do today?",
      "What am I paying for?",
      "What do I know about my car?",
      "What changed recently?",
    ];
    element.innerHTML = examples.map((question) => '<button class="question-chip" type="button" data-question="' + escapeHtml(question) + '">' + escapeHtml(question) + '</button>').join("");
  };

  // The hook is intentionally opt-in and inert in production. It lets the
  // dependency-free UI contract tests execute the same normalization and
  // disclosure behavior without requiring a browser or a brittle source scan.
  if (window.__BLACKHOLE_V2_TEST__) {
    window.BlackholeV2 = {
      fixtureMode,
      normalizeAttention,
      normalizeMemory,
      normalizeAnswer,
      formatAttentionTime,
      formatCapturedTime,
      formatOccurrenceWhen,
      occurrenceSummary,
      attentionUrgency,
      displayText,
      createDisclosureState,
      shouldShowAskExamples,
      formatMoney,
      humanize,
    };
    return;
  }

  $$(".nav-item, .brand-button").forEach((button) => button.addEventListener("click", () => showView(button.dataset.view || "capture")));
  $("#capture-input")?.addEventListener("input", resizeTextarea);
  $("#capture-input")?.addEventListener("keydown", (event) => {
    // Some embedded Chromium builds report isComposing for ordinary Enter
    // keypresses.  Ignore the IME sentinel (229) while keeping plain Enter a
    // reliable submit action.
    const composingEnter = event.isComposing && event.keyCode === 229;
    if (event.key === "Enter" && !event.shiftKey && !composingEnter) {
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
  $("#new-ask-thread")?.addEventListener("click", resetAskThread);
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
  $("#memory-list")?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-clarify-question]");
    if (!button) return;
    navigateToAskWithPrompt(button.dataset.clarifyQuestion || "");
  });
  $("#attention-list")?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-attention-complete]");
    if (button) completeAttention(button);
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
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) return;
    renderAttention();
    scheduleAttentionTicker();
    scheduleProcessingPoll();
  });
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
    let reloadingForServiceWorker = false;
    const hadServiceWorkerController = Boolean(navigator.serviceWorker.controller);
    navigator.serviceWorker.addEventListener("controllerchange", () => {
      if (!hadServiceWorkerController || reloadingForServiceWorker) return;
      reloadingForServiceWorker = true;
      window.location.reload();
    });
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/sw.js?v=9", { updateViaCache: "none" })
        .then((registration) => {
          if (registration.waiting) registration.waiting.postMessage({ type: "SKIP_WAITING" });
          if (typeof registration.update === "function") return registration.update();
          return undefined;
        })
        .catch(() => {});
    });
  }

  if (typeof window !== "undefined") {
    window.BlackholeV2 = {
      fixtureMode,
      normalizeAttention,
      normalizeMemory,
      normalizeAnswer,
      formatAttentionTime,
      formatCapturedTime,
      formatOccurrenceWhen,
      occurrenceSummary,
      attentionUrgency,
      displayText,
      createDisclosureState,
      shouldShowAskExamples,
      formatMoney,
      humanize,
    };
  }
})();
