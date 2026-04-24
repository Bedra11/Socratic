/* ===============================================================
   THE SOCRATIC GAME — result.js
   Result page logic. No inline styles anywhere.
   =============================================================== */

/* ---- GLOSSARY ---- */
const PHILOSOPHY_GLOSSARY = {
  care_ethics:          "Care ethics is an ethical approach centered on empathy, relationships, responsibility, and sensitivity to the needs of others. It values compassion and human connection in moral decisions.",
  deontology:           "Deontology is an ethical theory based on duty, rules, and moral principles. It judges an action mainly by whether it is right in itself, not by the consequences it produces.",
  egoism:               "Egoism is the view that actions are guided mainly by self-interest. It focuses on what benefits the individual making the choice.",
  utilitarianism:       "Utilitarianism evaluates actions by their consequences. A decision is morally good if it creates the greatest overall good or happiness for the greatest number of people.",
  virtue_ethics:        "Virtue ethics focuses on character. It asks what a wise, honest, courageous, and morally admirable person would do in a given situation.",
  ad_hominem:           "Ad hominem is a fallacy where someone attacks the person instead of addressing the argument itself.",
  ad_populum:           "Ad populum is a fallacy that treats something as true, good, or right simply because many people believe it or support it.",
  appeal_to_emotion:    "Appeal to emotion is a fallacy where fear, pity, guilt, anger, or another emotion is used instead of solid reasoning.",
  circular_reasoning:   "Circular reasoning happens when the conclusion is simply repeated in different words instead of being supported by actual evidence.",
  equivocation:         "Equivocation is a fallacy where a word or phrase changes meaning during an argument, creating confusion and misleading reasoning.",
  fallacy_of_credibility: "Fallacy of credibility happens when a claim is accepted or rejected mainly because of who says it, rather than because of the strength of the evidence or reasoning.",
  fallacy_of_extension: "Fallacy of extension happens when someone exaggerates, oversimplifies, or distorts an argument beyond its real form, making it easier to attack or dismiss.",
  fallacy_of_logic:     "Fallacy of logic refers to a flaw in the structure of reasoning itself, where the conclusion does not properly follow from the premises.",
  fallacy_of_relevance: "Fallacy of relevance happens when reasons are given that are not truly connected to the issue being argued, even if they sound persuasive.",
  false_causality:      "False causality is the mistake of assuming that one thing caused another without sufficient evidence of a real causal link.",
  false_dilemma:        "False dilemma presents only two options as if they are the only possibilities, even though other alternatives may exist.",
  faulty_generalization:"Faulty generalization builds a broad conclusion from weak, limited, or unrepresentative evidence.",
  intentional:          "Intentional reasoning focuses heavily on motives or intended meaning. In this context, it suggests the argument may rely too much on assumed intention rather than clear logical support."
};

/* ---- UTILITIES ---- */
function normalizeTerm(term) {
  return String(term || "")
    .trim()
    .toLowerCase()
    .replace(/&/g, "and")
    .replace(/-/g, "_")
    .replace(/\//g, "_")
    .replace(/\s+/g, "_");
}

function toTitleCase(text) {
  return String(text || "")
    .split(" ")
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el && value) el.textContent = value;
}

/* ---- TERM INFO BOXES ---- */
function openInfoBox(term, boxId, titleId, textId, fallbackTitle) {
  const box   = document.getElementById(boxId);
  const title = document.getElementById(titleId);
  const text  = document.getElementById(textId);
  if (!box || !title || !text) return;

  const normalized = normalizeTerm(term);
  const description =
    PHILOSOPHY_GLOSSARY[normalized] ||
    "This term represents a category identified by the game. No glossary entry is saved for it yet.";

  title.textContent = `${fallbackTitle}: ${toTitleCase(String(term).replace(/_/g, " "))}`;
  text.textContent  = description;
  box.classList.remove("hidden");
}

function closeInfoBox(boxId) {
  const box = document.getElementById(boxId);
  if (box) box.classList.add("hidden");
}

/* ---- FALLBACK RESULT BUILDER ---- */
function pickFallbackFinalResult(results) {
  if (!Array.isArray(results) || results.length === 0) return null;

  const last = results[results.length - 1] || {};

  return {
    ethics_icon:        last.ethics_icon        || "🧠",
    ethics_name:        last.ethics_name        || "Undefined",
    ethics_text:        last.ethics_text        || "",
    ethics_explanation: last.ethics_explanation || "",
    ethics_label:       last.ethics_label       || last.ethics_prediction  || "",
    fallacy_label:      last.fallacy_label      || last.fallacy_prediction || "",
    fallacy_text:       last.fallacy_text        || "",
    fallacy_explanation:last.fallacy_explanation || "",
    personal_insight:   last.personal_insight   || "",
    book_title:         last.book_title         || "Meditations",
    book_author:        last.book_author        || "Marcus Aurelius",
    book_why:           last.book_why           || "A classic for any thinker.",
    book_link:          last.book_link          || "",
    chapters_analyzed:  results.length
  };
}

/* ---- MAIN INIT ---- */
document.addEventListener("DOMContentLoaded", () => {
  const raw        = JSON.parse(sessionStorage.getItem("socratic_result")     || "{}");
  const allResults = JSON.parse(sessionStorage.getItem("socratic_all_results") || "[]");
  const allInputs  = JSON.parse(sessionStorage.getItem("socratic_all_inputs")  || "[]");

  const finalData  = Object.keys(raw).length
    ? raw
    : (pickFallbackFinalResult(allResults) || {});

  const hasData = Object.keys(finalData).length > 0;

  if (!hasData) {
    document.getElementById("emptyStateNote").classList.remove("hidden");
    return;
  }

  /* Ethics card */
  setText("ethicsIcon",        finalData.ethics_icon);
  setText("ethicsName",        finalData.ethics_name);
  setText("ethicsText",        finalData.ethics_text);
  setText("ethicsExplanation", finalData.ethics_explanation);

  if (finalData.ethics_label) {
    setText("ethicsLabel", toTitleCase(String(finalData.ethics_label).replace(/_/g, " ")));
  }

  /* Fallacy card */
  if (finalData.fallacy_label) {
    setText("fallacyLabel", toTitleCase(String(finalData.fallacy_label).replace(/_/g, " ")));
  }
  setText("fallacyText",        finalData.fallacy_text);
  setText("fallacyExplanation", finalData.fallacy_explanation);
  setText("personalInsight",    finalData.personal_insight);

  /* Book card */
  if (finalData.book_title) {
    setText("bookTitle", finalData.book_title);
    setText("popupTitle", finalData.book_title);
  }
  if (finalData.book_author) {
    setText("bookAuthor", `— ${finalData.book_author}`);
    setText("popupAuthor", finalData.book_author);
  }
  setText("bookWhy",  finalData.book_why);
  setText("popupWhy", finalData.book_why);

  const popupLink = document.getElementById("popupLink");
  if (popupLink) {
    const link = finalData.book_link || (() => {
    const q = encodeURIComponent(`${finalData.book_title || ""} ${finalData.book_author || ""}`.trim());
      return `https://www.goodreads.com/search?q=${q}`;
    })();
    popupLink.href = link;
  }

  /* Summary card */
  const chaptersAnalyzed =
    finalData.chapters_analyzed || allInputs.length || allResults.length || 0;

  setText(
    "chaptersAnalyzedText",
`The final report is based on ${chaptersAnalyzed} chapter${chaptersAnalyzed === 1 ? "" : "s"}`  );

  /* Term button click handlers */
  const ethicsBtn  = document.getElementById("ethicsLabel");
  const fallacyBtn = document.getElementById("fallacyLabel");

  if (ethicsBtn) {
    ethicsBtn.addEventListener("click", () => {
      openInfoBox(
        ethicsBtn.textContent,
        "ethicsTermBox",
        "ethicsTermTitle",
        "ethicsTermDescription",
        "Philosophical Meaning"
      );
    });
  }

  if (fallacyBtn) {
    fallacyBtn.addEventListener("click", () => {
      openInfoBox(
        fallacyBtn.textContent,
        "fallacyTermBox",
        "fallacyTermTitle",
        "fallacyTermDescription",
        "Reasoning Meaning"
      );
    });
  }

  /* Close buttons — delegated via data-close attribute */
  document.addEventListener("click", e => {
    const closeBtn = e.target.closest("[data-close]");
    if (closeBtn) {
      closeInfoBox(closeBtn.dataset.close);
    }
  });

  /* Card entrance animations */
  document.querySelectorAll(".result-card").forEach((card, index) => {
card.style.animationDelay = `${0.2 + index * 0.2}s`;
    card.classList.add("card-reveal");
  });
});

const bookTitle = document.getElementById("bookTitle");
const popup = document.getElementById("bookPopup");

if (bookTitle && popup) {
  bookTitle.addEventListener("click", () => {
    popup.classList.toggle("active");
  });

  // close if clicking outside
  document.addEventListener("click", (e) => {
    if (!popup.contains(e.target) && !bookTitle.contains(e.target)) {
      popup.classList.remove("active");
    }
  });
}