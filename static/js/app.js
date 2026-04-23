const ROMAN = ["I", "II", "III", "IV", "V"];

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

let currentScenarioIndex = 0;
let selectedDecision = "";
let selectedReason = "";

// Stores every API response from all chapters
let allResults = [];

// Stores every raw user answer from all chapters
let allChapterInputs = [];

document.addEventListener("DOMContentLoaded", () => {
  loadScenario(currentScenarioIndex);
  updateProgress(0);

  const overlay = document.getElementById("chapterOverlay");
  if (overlay) {
    overlay.style.display = "none";
  }
});

function loadScenario(index) {
  const scenario = SCENARIOS[index];
  if (!scenario) return;

  document.getElementById("scenarioText").textContent = scenario.text;
  document.getElementById("scenarioNumber").textContent = ROMAN[index];
  document.getElementById("chapterNum").textContent = ROMAN[index];

  selectedDecision = "";
  selectedReason = "";

  showStep("step-scenario");
  updateProgress((index / SCENARIOS.length) * 100);
}

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

async function sendToAPI() {
  showStep("step-thinking");

  const scenarioText = SCENARIOS[currentScenarioIndex].text;

  allChapterInputs.push({
    chapter: currentScenarioIndex + 1,
    scenario: scenarioText,
    decision: selectedDecision,
    reason: selectedReason
  });

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scenario: scenarioText,
        decision: selectedDecision,
        reason: selectedReason,
        language: "english"
      })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();

    allResults.push({
      chapter: currentScenarioIndex + 1,
      scenario: scenarioText,
      decision: selectedDecision,
      reason: selectedReason,
      ...data
    });

    if (currentScenarioIndex < SCENARIOS.length - 1) {
      await sleep(800);
      showChapterTransition();
    } else {
      await sleep(800);
      await finishGame();
    }

  } catch (err) {
    console.error("API error:", err);
  }
}

function showChapterTransition() {
  const overlay = document.getElementById("chapterOverlay");

  if (overlay) {
    overlay.style.display = "flex";
    overlay.textContent = `Chapter ${ROMAN[currentScenarioIndex]} Complete`;
  }

  setTimeout(() => {
    if (overlay) {
      overlay.style.display = "none";
    }

    currentScenarioIndex++;
    loadScenario(currentScenarioIndex);
  }, 1200);
}

async function finishGame() {
  if (!allResults.length || !allChapterInputs.length) return;

  try {
    const response = await fetch("/analyze-final", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chapters: allChapterInputs.map(item => ({
          scenario: item.scenario,
          decision: item.decision,
          reason: item.reason
        })),
        language: "english"
      })
    });

    if (!response.ok) {
      throw new Error(`Final API error: ${response.status}`);
    }

    const finalData = await response.json();

    sessionStorage.setItem("socratic_all_results", JSON.stringify(allResults));
    sessionStorage.setItem("socratic_all_inputs", JSON.stringify(allChapterInputs));
    sessionStorage.setItem("socratic_result", JSON.stringify(finalData));

    window.location.href = "/result";

  } catch (err) {
    console.error("Final API error:", err);

    // Fallback local if /analyze-final fails
    const ethicsCount = {};
    const fallacyCount = {};

    allResults.forEach(result => {
      const ethicsKey = result.ethics_prediction || result.ethics_label || "unknown";
      const fallacyKey = result.fallacy_prediction || result.fallacy_label || "unknown";

      ethicsCount[ethicsKey] = (ethicsCount[ethicsKey] || 0) + 1;
      fallacyCount[fallacyKey] = (fallacyCount[fallacyKey] || 0) + 1;
    });

    const dominantEthics = Object.keys(ethicsCount)
      .reduce((a, b) => ethicsCount[a] >= ethicsCount[b] ? a : b);

    const dominantFallacy = Object.keys(fallacyCount)
      .reduce((a, b) => fallacyCount[a] >= fallacyCount[b] ? a : b);

    const representativeEthics =
      allResults.find(r => (r.ethics_prediction || r.ethics_label) === dominantEthics) || {};

    const representativeFallacy =
      allResults.find(r => (r.fallacy_prediction || r.fallacy_label) === dominantFallacy) || {};

    const fallbackResult = {
      language: "english",
      ethics_prediction: dominantEthics,
      fallacy_prediction: dominantFallacy,
      ethics_label: dominantEthics,
      ethics_name: representativeEthics.ethics_name || dominantEthics,
      ethics_icon: representativeEthics.ethics_icon || "🧠",
      ethics_text: representativeEthics.ethics_text || representativeEthics.ethics_explanation || "",
      fallacy_label: dominantFallacy,
      book_title: representativeFallacy.book_title || "Meditations",
      book_author: representativeFallacy.book_author || "Marcus Aurelius",
      book_why: representativeFallacy.book_why || "A classic for any thinker.",
      ethics_explanation: representativeEthics.ethics_explanation || "",
      fallacy_explanation: representativeFallacy.fallacy_explanation || "",
      personal_insight: representativeFallacy.personal_insight || "",
      chapters_analyzed: allChapterInputs.length
    };

    sessionStorage.setItem("socratic_all_results", JSON.stringify(allResults));
    sessionStorage.setItem("socratic_all_inputs", JSON.stringify(allChapterInputs));
    sessionStorage.setItem("socratic_result", JSON.stringify(fallbackResult));

    window.location.href = "/result";
  }
}

function showStep(stepId) {
  document.querySelectorAll(".game-step")
    .forEach(s => s.classList.remove("active"));

  const target = document.getElementById(stepId);
  if (target) {
    target.classList.add("active");
  }
}

function updateProgress(percent) {
  const fill = document.getElementById("progressFill");
  if (fill) {
    fill.style.width = `${percent}%`;
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}