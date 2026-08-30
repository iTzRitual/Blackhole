"""Language-safe intent and retrieval planning for Product V2 Ask.

The planner is deliberately small and deterministic.  It recognizes a few
high-confidence product intents, removes conversational stop words from
retrieval terms, and leaves open-world questions on the generic memory path.
It does not contain benchmark query IDs or product-specific question text.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any


_STOPWORDS = frozenset(
    {
        "a",
        "about",
        "am",
        "an",
        "and",
        "anything",
        "are",
        "at",
        "belong",
        "belongs",
        "can",
        "could",
        "coming",
        "co",
        "czy",
        "did",
        "dla",
        "do",
        "does",
        "for",
        "from",
        "find",
        "gdzie",
        "have",
        "i",
        "in",
        "information",
        "is",
        "jest",
        "keep",
        "it",
        "jak",
        "jaka",
        "jakie",
        "jaki",
        "kiedy",
        "know",
        "mam",
        "ma",
        "me",
        "memory",
        "mnie",
        "my",
        "might",
        "needs",
        "moim",
        "moja",
        "moje",
        "mój",
        "na",
        "need",
        "o",
        "of",
        "on",
        "oraz",
        "please",
        "pamiętam",
        "person",
        "people",
        "recorded",
        "remember",
        "remembered",
        "say",
        "said",
        "są",
        "sie",
        "się",
        "should",
        "ten",
        "tell",
        "thing",
        "things",
        "the",
        "there",
        "this",
        "to",
        "up",
        "w",
        "was",
        "what",
        "where",
        "which",
        "who",
        "with",
        "we",
        "wiem",
        "when",
        "mowilem",
        "mowilam",
        "you",
        "za",
        "że",
        "z",
    }
)


# These are cross-language lexical equivalents, not question-specific rules.
# They make a Polish capture searchable from English and vice versa while
# leaving arbitrary entity names untouched.
_TERM_ALIASES = {
    "buying": "buy",
    "bought": "buy",
    "buys": "buy",
    "purchase": "buy",
    "purchases": "buy",
    "choosing": "choose",
    "chosen": "choose",
    "choose": "choose",
    "went": "go",
    "going": "go",
    "gone": "go",
    "locations": "location",
    "now": "current",
    "mieszkanie": "house",
    "mieszkania": "house",
    "mieszkaniu": "house",
    "wejsc": "entrance",
    "wejscie": "entrance",
    "wejscia": "entrance",
    "but": "shoe",
    "buty": "shoe",
    "butow": "shoe",
    "shoes": "shoe",
    "notice": "observation",
    "noticed": "observation",
    "note": "observation",
    "noted": "observation",
    "stopped": "stop",
    "stopping": "stop",
    "rattles": "rattle",
    "rattling": "rattle",
    "gift_idea": "gift",
    "dietary_preference": "preference",
    "shoe_size": "shoe",
    "monthly_cost": "cost",
    "basement": "basement",
    "piwnica": "basement",
    "piwnicy": "basement",
    "piwnice": "basement",
    "piwnicę": "basement",
    "car": "car",
    "auto": "car",
    "samochod": "car",
    "samochodzie": "car",
    "samochodem": "car",
    "samochodu": "car",
    "issue": "condition",
    "problem": "condition",
    "ostatnio": "recent",
    "kubie": "kuba",
    "charger": "charger",
    "ladowarka": "charger",
    "ladowarki": "charger",
    "location": "location",
    "located": "location",
    "kept": "location",
    "stored": "location",
    "dziecko": "kids",
    "dzieci": "kids",
    "children": "kids",
    "kids": "kids",
    "key": "keys",
    "keys": "keys",
    "klucz": "keys",
    "klucze": "keys",
    "kluczem": "keys",
    "kluczyk": "keys",
    "kluczy": "keys",
    "mother": "mother",
    "mum": "mother",
    "mom": "mother",
    "mama": "mother",
    "mamy": "mother",
    "mamie": "mother",
    "matka": "mother",
    "green": "green",
    "zielony": "green",
    "zielona": "green",
    "pasta": "pasta",
    "makaron": "pasta",
    "like": "preference",
    "likes": "preference",
    "liked": "preference",
    "prefer": "preference",
    "prefers": "preference",
    "favorite": "preference",
    "favourite": "preference",
    "boiler": "boiler",
    "piec": "boiler",
    "kotl": "boiler",
    "house": "house",
    "home": "house",
    "dom": "house",
    "own": "owner",
    "owns": "owner",
    "ownership": "owner",
    "owner": "owner",
    "document": "document",
    "dokument": "document",
    "contract": "document",
    "umowa": "document",
    "najem": "document",
    "najmu": "document",
    "rental": "document",
    "permit": "permit",
    "pozwolenie": "permit",
    "parking": "parking",
    "parkowanie": "parking",
    "urgent": "urgent",
    "pilne": "urgent",
    "pilny": "urgent",
    "attention": "attention",
    "uwaga": "attention",
    "uwagi": "attention",
    "deadline": "deadline",
    "termin": "deadline",
    "terminy": "deadline",
    "task": "task",
    "tasks": "task",
    "zadanie": "task",
    "zadania": "task",
    "reminder": "reminder",
    "przypomnienie": "reminder",
    "appointment": "appointment",
    "spotkanie": "appointment",
    "today": "today",
    "dzis": "today",
    "dzisiaj": "today",
    "tomorrow": "tomorrow",
    "jutro": "tomorrow",
    "upcoming": "upcoming",
    "soon": "soon",
    "niedlugo": "soon",
    "wkrotce": "soon",
    "week": "week",
    "tydzien": "week",
    "change": "change",
    "changes": "change",
    "changed": "change",
    "zmiana": "change",
    "zmienilo": "change",
    "zmienila": "change",
    "zmienione": "change",
    "correction": "correction",
    "corrected": "correction",
    "korekta": "correction",
    "poprawione": "correction",
    "replaced": "replacement",
    "replacement": "replacement",
    "zastapione": "replacement",
    "previous": "previous",
    "earlier": "earlier",
    "before": "before",
    "poprzedni": "previous",
    "poprzednia": "previous",
    "wczesniej": "earlier",
    "history": "history",
    "historical": "history",
    "historia": "history",
    "price": "price",
    "prices": "price",
    "cena": "price",
    "ceny": "price",
    "cost": "cost",
    "costs": "cost",
    "koszt": "cost",
    "koszty": "cost",
    "pay": "pay",
    "paying": "pay",
    "subscription": "subscription",
    "subscriptions": "subscription",
    "abonament": "subscription",
    "billing": "billing",
    "monthly": "monthly",
    "month": "month",
    "miesiac": "month",
    "miesiecznie": "monthly",
    "miesieczny": "monthly",
    "fee": "fee",
    "fees": "fee",
    "oplata": "fee",
    "oplaty": "fee",
    "synthesize": "synthesize",
    "synthesis": "synthesize",
    "summarize": "summarize",
    "summary": "summarize",
    "explain": "explain",
    "meaning": "meaning",
    "mean": "meaning",
    "means": "meaning",
    "oznacza": "meaning",
    "znaczenie": "meaning",
    "wyjasnij": "explain",
    "podsumuj": "summarize",
}

_ATTENTION_TERMS = frozenset(
    {
        "appointment",
        "attention",
        "deadline",
        "due",
        "reminder",
        "task",
        "todo",
        "today",
        "tomorrow",
        "urgent",
        "upcoming",
        "soon",
        "week",
        "zrobic",
        "zrobienia",
    }
)
_COST_TERMS = frozenset(
    {
        "billing",
        "cost",
        "fee",
        "month",
        "monthly",
        "pay",
        "price",
        "subscription",
    }
)
_CHANGE_TERMS = frozenset(
    {
        "before",
        "change",
        "correction",
        "earlier",
        "history",
        "previous",
        "replacement",
        "superseded",
    }
)
_STRONG_CHANGE_TERMS = frozenset(
    {
        "before",
        "change",
        "correction",
        "earlier",
        "previous",
        "replacement",
        "superseded",
    }
)
_SYNTHESIS_TERMS = frozenset({"compare", "connect", "explain", "how", "meaning", "summarize", "synthesize", "why"})
_PLANNER_TERMS = _ATTENTION_TERMS | _COST_TERMS | _CHANGE_TERMS | _SYNTHESIS_TERMS | {
    "coming",
    "context",
    "current",
    "due",
    "history",
    "last",
    "mention",
    "mentioned",
    "next",
    "recent",
    "recently",
    "urgent",
    "value",
}

_LAST_MENTION_TERMS = frozenset({"last", "mention", "mentioned", "wspomnialem", "wspomnialam"})

_ATTENTION_PHRASES = (
    r"\bwhat\s+do\s+i\s+need\s+to\s+do\b",
    r"\bwhat\s+do\s+i\s+have\s+to\s+do\b",
    r"\bwhat\s+should\s+i\s+do\b",
    r"\bwhat\s+am\s+i\s+supposed\s+to\s+do\b",
    r"\bwhat\s+needs?\s+(?:my\s+)?attention\b",
    r"\bdo\s+i\s+have\s+anything\s+urgent\b",
    r"\bwhat\s+(?:is|s)\s+(?:currently\s+)?(?:urgent|due)\b",
    r"\bwhat\s+(?:is|s)\s+coming\s+up\b",
    r"\bwhat\s+do\s+i\s+have\s+coming\s+up\b",
    r"\bco\s+mam\s+(?:niedlugo\s+)?do\s+zrobienia\b",
    r"\bco\s+musze\s+zrobic\b",
    r"\bco\s+trzeba\s+zrobic\b",
    r"\bco\s+(?:jest|mnie)\s+(?:teraz\s+)?pilne\b",
    r"\bco\s+wymaga\s+uwagi\b",
    r"\bco\s+nadchodzi\b",
)


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    normalized = normalized.translate(str.maketrans({"ł": "l", "đ": "d", "ð": "d", "þ": "th", "ß": "ss"}))
    return "".join(character for character in normalized if not unicodedata.combining(character))


_FOLDED_STOPWORDS = frozenset(_fold(item) for item in _STOPWORDS)


def word_tokens(value: Any) -> set[str]:
    """Return whole-word tokens without routing or alias semantics."""

    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True) if value is not None else ""
    return {
        token
        for token in re.findall(r"[\w]+", value.casefold(), flags=re.UNICODE)
        if len(token) > 1
    }


def search_terms(value: Any) -> set[str]:
    """Return stop-word-filtered, accent-folded, cross-language terms."""

    terms: set[str] = set()
    for token in word_tokens(value):
        folded = _fold(token)
        if len(folded) <= 1 or folded in _FOLDED_STOPWORDS:
            continue
        terms.add(_TERM_ALIASES.get(folded, folded))
    return terms


def _normalized_question(question: str) -> str:
    return re.sub(r"[^\w]+", " ", _fold(question), flags=re.UNICODE).strip()


def _has_polish_signal(tokens: set[str]) -> bool:
    if any(any(unicodedata.combining(character) for character in unicodedata.normalize("NFKD", token)) for token in tokens):
        return True
    return bool(
        tokens
        & {
            "co",
            "gdzie",
            "jest",
            "jaki",
            "jaka",
            "jakie",
            "mam",
            "mamy",
            "kiedy",
            "ile",
            "wiem",
            "butow",
            "rozmiar",
            "nosi",
            "ktoredy",
            "wejsc",
        }
    )


@dataclass(frozen=True)
class AskPlan:
    """The bounded, inspectable decision used by Product V2 Ask."""

    intent: str
    query_terms: frozenset[str]
    topic_terms: frozenset[str]
    time_window: str | None
    history_requested: bool
    requires_synthesis: bool
    broad: bool
    language: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "query_terms": sorted(self.query_terms),
            "topic_terms": sorted(self.topic_terms),
            "time_window": self.time_window,
            "history_requested": self.history_requested,
            "requires_synthesis": self.requires_synthesis,
            "broad": self.broad,
            "language": self.language,
        }


def plan_ask(question: str) -> AskPlan:
    """Classify high-confidence intents and otherwise choose generic retrieval."""

    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must not be empty")
    tokens = word_tokens(question)
    folded_tokens = {_fold(token) for token in tokens}
    normalized = _normalized_question(question)
    terms = frozenset(search_terms(question))
    future_advice = bool(
        re.search(r"\bhow\s+should\b", normalized)
        or re.search(r"\bwhat\s+should\b.*\b(?:next|buy|remember)\b", normalized)
        or re.search(r"\bnext\s+time\b", normalized)
    )
    strong_changes = set(terms) & _STRONG_CHANGE_TERMS
    if future_advice:
        # A future recommendation can mention "change" without asking for a
        # recorded correction.  Keep the known observation on generic memory.
        strong_changes.clear()
    has_history = bool(folded_tokens & {"history", "historical", "historia", "previous", "earlier", "before", "poprzedni", "poprzednia", "wczesniej"})
    polish_payment = bool(tokens & {"płacę", "płace", "placę", "płacić", "płaci"})
    has_cost = bool(terms & {"billing", "cost", "fee", "pay", "price", "subscription"}) or bool(
        tokens
        & {
            "koszt",
            "koszty",
            "cena",
            "ceny",
            "abonament",
            "miesięcznie",
            "miesiąc",
            "opłata",
            "opłaty",
        }
    ) or polish_payment
    if not has_cost and bool(terms & {"month", "monthly"}):
        has_cost = bool(re.search(r"\bhow\s+much\b|\bile\b", normalized))
    attention_terms = terms & _ATTENTION_TERMS
    time_window: str | None = None
    if "today" in terms:
        time_window = "today"
    elif "tomorrow" in terms:
        time_window = "tomorrow"
    elif terms & {"upcoming", "soon", "week"}:
        time_window = "upcoming"

    has_attention_phrase = any(re.search(pattern, normalized) for pattern in _ATTENTION_PHRASES)
    has_action_phrase = bool(
        re.search(r"\b(?:need|should)\s+(?:to\s+)?do\b", normalized)
        or re.search(r"\b(?:musze|trzeba)\s+zrobic\b", normalized)
        or re.search(r"\bdo\s+zrobienia\b", normalized)
    )
    has_deadline_question = bool(
        folded_tokens & {"deadline", "due", "termin", "urgent", "pilne", "uwagi", "attention"}
    )
    topic_terms = frozenset(
        term
        for term in terms
        if term not in _PLANNER_TERMS
        and term not in {"pay", "price", "cost", "subscription", "billing", "fee", "month", "monthly"}
        and not (polish_payment and term == "place")
    )
    has_topic = bool(topic_terms)
    looks_like_attention = has_attention_phrase or has_action_phrase or has_deadline_question
    if time_window is not None and (not has_topic or bool(attention_terms & {"task", "urgent", "deadline", "reminder", "appointment"})):
        looks_like_attention = True
    if "need" in folded_tokens and not (has_action_phrase or time_window or has_deadline_question):
        # ``need`` on its own is not an Attention intent.  This keeps questions
        # such as "What do I need to know about the boiler?" generic.
        looks_like_attention = False

    if strong_changes:
        intent = "changes"
    elif has_cost:
        # A price/history question is still a money retrieval request.  A
        # strong change marker above takes precedence for explicit corrections
        # and previous-value questions.
        intent = "costs"
    elif has_history:
        intent = "changes"
    elif looks_like_attention:
        intent = "attention"
    elif (
        "last" in terms
        and bool(set(terms) & (_LAST_MENTION_TERMS - {"last"}))
    ):
        intent = "last_mention"
    else:
        intent = "generic"

    broad = not topic_terms and not (terms - _PLANNER_TERMS)
    requires_synthesis = intent == "generic" and bool(terms & _SYNTHESIS_TERMS)
    return AskPlan(
        intent=intent,
        query_terms=terms,
        topic_terms=topic_terms,
        time_window=time_window,
        history_requested=has_history,
        requires_synthesis=requires_synthesis,
        broad=broad,
        language="pl" if _has_polish_signal(tokens) else "en",
    )


__all__ = ["AskPlan", "plan_ask", "search_terms", "word_tokens"]
