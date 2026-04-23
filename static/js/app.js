const ROMAN = ["I", "II", "III", "IV", "V"];

const SCENARIOS = [ /* inchangé */ ];

let currentScenarioIndex = 0;
let selectedDecision = "";
let selectedReason = "";

// ✅ NEW: store all results
let allResults = [];

// ─────────────────────────
// INIT
// ─────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  loadScenario(currentScenarioIndex);
  updateProgress(0);
});

// ─────────────────────────
// LOAD SCENARIO
// ─────────────────────────
function loadScenario(index) {
  const scenario = SCENARIOS[index];

  document.getElementById("scenarioText").textContent = scenario.text;
  document.getElementById("scenarioNumber").textContent = ROMAN[index];
  document.getElementById("chapterNum").textContent = ROMAN[index];

  selectedDecision = "";
  selectedReason = "";

  showStep("step-scenario");
  updateProgress(((index) / SCENARIOS.length) * 100);
}

// ─────────────────────────
// DECISION
// ─────────────────────────
function showDecisions() {
  const scenario = SCENARIOS[currentScenarioIndex];
  const grid = document.getElementById("decisionsGrid");
  grid.innerHTML = "";

  scenario.decisions.forEach(decision => {
    const btn = document.createElement("button");
    btn.className = "choice-btn";
    btn.textContent = decision;
    btn.onclick = () => selectDecision(decision, btn);
    grid.appendChild(btn);
  });

  showStep("step-decision");
}

function selectDecision(decision, btn) {
  document.querySelectorAll("#decisionsGrid .choice-btn")
    .forEach(b => b.classList.remove("selected"));

  btn.classList.add("selected");
  selectedDecision = decision;

  setTimeout(() => showReasons(), 400);
}

// ─────────────────────────
// REASONS
// ─────────────────────────
function showReasons() {
  const scenario = SCENARIOS[currentScenarioIndex];
  const grid = document.getElementById("reasonsGrid");
  grid.innerHTML = "";

  scenario.reasons.forEach(reason => {
    const btn = document.createElement("button");
    btn.className = "choice-btn";
    btn.textContent = reason;
    btn.onclick = () => selectReason(reason, btn);
    grid.appendChild(btn);
  });

  showStep("step-reason");
}

function selectReason(reason, btn) {
  document.querySelectorAll("#reasonsGrid .choice-btn")
    .forEach(b => b.classList.remove("selected"));

  btn.classList.add("selected");
  selectedReason = reason;

  setTimeout(() => sendToAPI(), 500);
}

// ─────────────────────────
// SEND TO API (FIXED)
// ─────────────────────────
async function sendToAPI() {
  showStep("step-thinking");

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scenario: SCENARIOS[currentScenarioIndex].text,
        decision: selectedDecision,
        reason: selectedReason
      })
    });

    const data = await response.json();

    // ✅ store result
    allResults.push(data);

    // ✅ check if last chapter
    if (currentScenarioIndex < SCENARIOS.length - 1) {

      await sleep(800);
      showChapterTransition();

    } else {

      // last chapter → finish
      await sleep(800);
      finishGame();

    }

  } catch (err) {
    console.error("API error:", err);
  }
}

// ─────────────────────────
// TRANSITION BETWEEN CHAPTERS
// ─────────────────────────
function showChapterTransition() {
  const overlay = document.getElementById("chapterOverlay");

  if (overlay) {
    overlay.style.display = "flex";
    overlay.textContent = `Chapter ${ROMAN[currentScenarioIndex]} Complete`;

    setTimeout(() => {
      overlay.style.display = "none";

      currentScenarioIndex++;
      loadScenario(currentScenarioIndex);

    }, 1200);
  }
}

// ─────────────────────────
// FINAL RESULT
// ─────────────────────────
function finishGame() {

  // count occurrences
  const ethicsCount = {};
  const fallacyCount = {};

  allResults.forEach(r => {
    ethicsCount[r.ethics_label] =
      (ethicsCount[r.ethics_label] || 0) + 1;

    fallacyCount[r.fallacy_label] =
      (fallacyCount[r.fallacy_label] || 0) + 1;
  });

  // find dominant
  const dominantEthics = Object.keys(ethicsCount)
    .reduce((a, b) => ethicsCount[a] > ethicsCount[b] ? a : b);

  const dominantFallacy = Object.keys(fallacyCount)
    .reduce((a, b) => fallacyCount[a] > fallacyCount[b] ? a : b);

  const finalResult = {
    ethics_label: dominantEthics,
    fallacy_label: dominantFallacy
  };

  // store everything
  sessionStorage.setItem("socratic_all_results", JSON.stringify(allResults));
  sessionStorage.setItem("socratic_result", JSON.stringify(finalResult));

  // open language popup
  openLanguageModal();
}

// ─────────────────────────
// LANGUAGE POPUP
// ─────────────────────────
function openLanguageModal() {
  const modal = document.getElementById("languageModal");
  if (modal) modal.style.display = "flex";
}

function closeLanguageModal() {
  const modal = document.getElementById("languageModal");
  if (modal) modal.style.display = "none";
}

// called from popup button
function submitFinalAnalysis() {
  closeLanguageModal();
  window.location.href = "/result";
}

// ─────────────────────────
// STEP CONTROL
// ─────────────────────────
function showStep(stepId) {
  document.querySelectorAll(".game-step")
    .forEach(s => s.classList.remove("active"));

  const target = document.getElementById(stepId);
  if (target) target.classList.add("active");
}

// ─────────────────────────
// PROGRESS
// ─────────────────────────
function updateProgress(percent) {
  const fill = document.getElementById("progressFill");
  if (fill) fill.style.width = `${percent}%`;
}

// ─────────────────────────
// UTILS
// ─────────────────────────
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}