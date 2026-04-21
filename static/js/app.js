// static/js/app.js
// ─────────────────────────────────────────
// SOCRATIC GAME — COMPLETE GAME LOGIC
// ─────────────────────────────────────────

const ROMAN = ["I", "II", "III", "IV", "V"];

// ─────────────────────────────────────────
// SCENARIOS DATA
// Each scenario has: text, decisions, reasons
// reasons are designed to map to fallacy types
// ─────────────────────────────────────────
const SCENARIOS = [
  {
    text: "A pharmaceutical company discovers that their best-selling drug has rare but serious side effects. Disclosing this will collapse the stock price and thousands of employees will lose their jobs. The CEO considers staying silent.",
    decisions: [
      "The information must be disclosed immediately",
      "Delay disclosure until a safer alternative is ready",
      "Only disclose if legally compelled to"
    ],
    reasons: [
      "Because patients deserve the truth regardless of economic consequences",
      "Because the greatest good for the greatest number requires protecting jobs",
      "Because everyone in the industry would do the same thing",
      "Because there is simply no other choice available to the company"
    ]
  },
  {
    text: "A city council must decide whether to demolish a historic neighborhood to build a highway that would reduce commute times for hundreds of thousands of people. The residents of the neighborhood are mostly elderly and low-income.",
    decisions: [
      "Approve the demolition for the greater good",
      "Reject it and find an alternative route",
      "Let the residents vote, even if the result is suboptimal"
    ],
    reasons: [
      "Because progress always requires sacrifice from someone",
      "Because the elderly residents will not suffer much longer anyway",
      "Because a good person would never displace vulnerable people",
      "Because ninety percent of citizens support the highway"
    ]
  },
  {
    text: "A journalist obtains leaked documents proving widespread government corruption. Publishing them would destabilize the current government and cause economic uncertainty, but it would also inform the public of grave abuses of power.",
    decisions: [
      "Publish everything immediately",
      "Negotiate with the government before publishing",
      "Destroy the documents to prevent harm"
    ],
    reasons: [
      "Because the freedom of press exists precisely for moments like this",
      "Because publishing caused chaos last time, so it will cause chaos this time",
      "Because powerful institutions are always corrupt anyway",
      "Because not publishing would be equivalent to endorsing the corruption"
    ]
  },
  {
    text: "An AI system consistently produces better medical diagnoses than human doctors in studies. A hospital administrator must decide whether to replace their diagnostic team with the AI, knowing this will eliminate dozens of well-paying jobs.",
    decisions: [
      "Replace the team — better outcomes justify the decision",
      "Use AI as a tool to assist doctors, not replace them",
      "Reject AI entirely to protect human employment"
    ],
    reasons: [
      "Because technology has always displaced workers and society always recovered",
      "Because a doctor with thirty years of experience said AI cannot replace human intuition",
      "Because if we allow this, eventually AI will replace all human work",
      "Because the only thing that matters is saving the most lives possible"
    ]
  },
  {
    text: "A brilliant scientist has discovered a clean energy source that could solve climate change, but the process requires testing that would harm a small, uninhabited ecosystem. Without this test, deployment could take another decade.",
    decisions: [
      "Proceed with the test immediately",
      "Delay and seek a less harmful testing method",
      "Abandon this approach entirely"
    ],
    reasons: [
      "Because we have always sacrificed nature for human progress",
      "Because the ecosystem is small and uninhabited, so no real harm is done",
      "Because climate change will destroy far more ecosystems if we wait",
      "Because a true environmentalist would never compromise on this principle"
    ]
  }
];

// ─────────────────────────────────────────
// STATE
// ─────────────────────────────────────────
let currentScenarioIndex = 0;
let selectedDecision     = "";
let selectedReason       = "";

// ─────────────────────────────────────────
// INIT — load first scenario on page ready
// ─────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  loadScenario(currentScenarioIndex);
  updateProgress(0);
});

// ─────────────────────────────────────────
// LOAD SCENARIO
// ─────────────────────────────────────────
function loadScenario(index) {
  const scenario = SCENARIOS[index];

  document.getElementById("scenarioText").textContent   = scenario.text;
  document.getElementById("scenarioNumber").textContent = ROMAN[index];
  document.getElementById("chapterNum").textContent     = ROMAN[index];

  // reset state
  selectedDecision = "";
  selectedReason   = "";

  // show step 1
  showStep("step-scenario");
  updateProgress((index / SCENARIOS.length) * 100);
}

// ─────────────────────────────────────────
// SHOW DECISIONS (Step 2)
// ─────────────────────────────────────────
function showDecisions() {
  const scenario = SCENARIOS[currentScenarioIndex];
  const grid     = document.getElementById("decisionsGrid");
  grid.innerHTML = "";

  scenario.decisions.forEach(decision => {
    const btn = document.createElement("button");
    btn.className   = "choice-btn";
    btn.textContent = decision;
    btn.onclick     = () => selectDecision(decision, btn);
    grid.appendChild(btn);
  });

  showStep("step-decision");
}

// ─────────────────────────────────────────
// SELECT DECISION
// ─────────────────────────────────────────
function selectDecision(decision, btn) {
  // remove previous selection
  document.querySelectorAll("#decisionsGrid .choice-btn")
    .forEach(b => b.classList.remove("selected"));

  btn.classList.add("selected");
  selectedDecision = decision;

  // slight delay then show reasons
  setTimeout(() => showReasons(), 400);
}

// ─────────────────────────────────────────
// SHOW REASONS (Step 3)
// ─────────────────────────────────────────
function showReasons() {
  const scenario = SCENARIOS[currentScenarioIndex];
  const grid     = document.getElementById("reasonsGrid");
  grid.innerHTML = "";

  scenario.reasons.forEach(reason => {
    const btn = document.createElement("button");
    btn.className   = "choice-btn";
    btn.textContent = reason;
    btn.onclick     = () => selectReason(reason, btn);
    grid.appendChild(btn);
  });

  showStep("step-reason");
}

// ─────────────────────────────────────────
// SELECT REASON
// ─────────────────────────────────────────
function selectReason(reason, btn) {
  document.querySelectorAll("#reasonsGrid .choice-btn")
    .forEach(b => b.classList.remove("selected"));

  btn.classList.add("selected");
  selectedReason = reason;

  // send to API after short delay
  setTimeout(() => sendToAPI(), 500);
}

// ─────────────────────────────────────────
// SEND TO API
// ─────────────────────────────────────────
async function sendToAPI() {
  showStep("step-thinking");

  try {
    const response = await fetch("/analyze", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scenario: SCENARIOS[currentScenarioIndex].text,
        decision: selectedDecision,
        reason:   selectedReason
      })
    });

    if (!response.ok) throw new Error("API error");

    const data = await response.json();

    // store in sessionStorage for result page
    sessionStorage.setItem("socratic_result", JSON.stringify(data));

    // small dramatic pause before redirect
    await sleep(1500);
    window.location.href = "/result";

  } catch (err) {
    console.error("Analysis failed:", err);
    // fallback — go to result with empty data
    await sleep(1000);
    window.location.href = "/result";
  }
}

// ─────────────────────────────────────────
// STEP TRANSITIONS
// ─────────────────────────────────────────
function showStep(stepId) {
  document.querySelectorAll(".game-step").forEach(s => {
    s.classList.remove("active");
  });

  const target = document.getElementById(stepId);
  if (target) {
    target.classList.add("active");
  }
}

// ─────────────────────────────────────────
// PROGRESS BAR
// ─────────────────────────────────────────
function updateProgress(percent) {
  const fill = document.getElementById("progressFill");
  if (fill) fill.style.width = `${percent}%`;
}

// ─────────────────────────────────────────
// UTILS
// ─────────────────────────────────────────
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
