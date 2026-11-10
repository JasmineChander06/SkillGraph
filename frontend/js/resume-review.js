/**
 * SkillGraph Resume Review & Rating Controller
 * Evaluates resumes across 4 dimensions and provides actionable improvements.
 */

const ResumeReviewView = (() => {
  const init = () => {
    setupCharCounter();
    setupButtons();
  };

  const setupCharCounter = () => {
    const textarea = document.getElementById("review-resume-text");
    const counter = document.getElementById("char-counter");
    if (!textarea || !counter) return;

    textarea.addEventListener("input", () => {
      const len = textarea.value.length;
      counter.textContent = `${len.toLocaleString()} characters`;
    });
  };

  const setupButtons = () => {
    const btnUseUploaded = document.getElementById("btn-use-uploaded");
    const btnRunReview = document.getElementById("btn-run-review");
    const textarea = document.getElementById("review-resume-text");

    btnUseUploaded?.addEventListener("click", async () => {
      // 1. Check if user has active session and records
      if (!API.auth.isAuthenticated()) {
        App.showToast("Please sign in or upload a resume on the Dashboard first.", "error");
        return;
      }

      btnUseUploaded.disabled = true;
      btnUseUploaded.textContent = "Loading uploaded resume…";

      try {
        const records = await API.resume.listRecords();
        if (records && records.length > 0) {
          const latest = records[0];
          if (textarea) {
            textarea.value = latest.extracted_text;
            const counter = document.getElementById("char-counter");
            if (counter) counter.textContent = `${textarea.value.length.toLocaleString()} characters`;
            App.showToast(`Loaded "${latest.filename}" (${latest.file_type.toUpperCase()}).`, "success");
          }
        } else {
          App.showToast("No uploaded resumes found on your account. Upload one on Dashboard or paste text.", "error");
        }
      } catch (err) {
        App.showToast(err.message || "Failed to retrieve uploaded resume.", "error");
      } finally {
        btnUseUploaded.disabled = false;
        btnUseUploaded.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="mr-1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
          Use Active Uploaded Resume
        `;
      }
    });

    btnRunReview?.addEventListener("click", async () => {
      const text = textarea?.value.trim();
      if (!text || text.length < 30) {
        App.showToast("Please provide at least 30 characters of resume text to analyze.", "error");
        return;
      }

      btnRunReview.disabled = true;
      btnRunReview.textContent = "Auditing resume…";

      try {
        const critique = await API.resume.critique({ text });
        renderCritiqueResults(critique);
        App.showToast("Resume review and rating calculated successfully.", "success");
      } catch (err) {
        App.showToast(err.message || "Failed to analyze resume.", "error");
      } finally {
        btnRunReview.disabled = false;
        btnRunReview.textContent = "Analyze & Score Resume";
      }
    });
  };

  const renderCritiqueResults = (data) => {
    const container = document.getElementById("review-results-container");
    if (!container) return;

    container.classList.remove("hidden");

    // 1. Overall Score & Label
    const scoreNum = document.getElementById("overall-score-num");
    const ratingBadge = document.getElementById("score-rating-badge");
    const summaryText = document.getElementById("review-summary-text");

    if (scoreNum) scoreNum.textContent = data.overall_score;
    if (summaryText) summaryText.textContent = data.summary;

    if (ratingBadge) {
      ratingBadge.textContent = data.rating_label;
      ratingBadge.className = "pill text-xs font-semibold px-4 py-1.5";
      if (data.overall_score >= 90) ratingBadge.classList.add("pill-primary");
      else if (data.overall_score >= 75) ratingBadge.classList.add("pill-secondary");
      else if (data.overall_score >= 60) ratingBadge.classList.add("pill-outline");
      else ratingBadge.classList.add("pill-destructive");
    }

    // 2. Dimension Bars (out of 25)
    const dims = data.dimension_scores || {};
    updateDimensionBar("quant", dims.quantification || 0);
    updateDimensionBar("verbs", dims.action_verbs || 0);
    updateDimensionBar("kw", dims.keyword_density || 0);
    updateDimensionBar("clarity", dims.brevity_and_clarity || 0);

    // 3. Things to Add
    const listAdd = document.getElementById("list-things-to-add");
    if (listAdd) {
      const adds = data.things_to_add || [];
      if (adds.length === 0) {
        listAdd.innerHTML = `<li class="text-muted-foreground italic">No critical missing items identified. Great work!</li>`;
      } else {
        listAdd.innerHTML = adds.map(item => `
          <li class="flex items-start gap-2 p-2 rounded-lg bg-secondary/50">
            <span class="text-emerald-600 font-bold font-mono text-sm shrink-0">+</span>
            <span class="text-foreground leading-relaxed">${App.escapeHtml(item)}</span>
          </li>
        `).join("");
      }
    }

    // 4. Things to Remove
    const listRemove = document.getElementById("list-things-to-remove");
    if (listRemove) {
      const removes = data.things_to_remove || [];
      if (removes.length === 0) {
        listRemove.innerHTML = `<li class="text-muted-foreground italic">Zero fluff words or clichés detected. High technical signal.</li>`;
      } else {
        listRemove.innerHTML = removes.map(item => `
          <li class="flex items-start gap-2 p-2 rounded-lg bg-secondary/50">
            <span class="text-rose-600 font-bold font-mono text-sm shrink-0">✕</span>
            <span class="text-foreground leading-relaxed">${App.escapeHtml(item)}</span>
          </li>
        `).join("");
      }
    }

    // 5. Bullet Improvements
    const bulletsContainer = document.getElementById("bullet-improvements-container");
    if (bulletsContainer) {
      const bullets = data.bullet_improvements || [];
      bulletsContainer.innerHTML = bullets.map(b => `
        <div class="p-4 rounded-2xl border border-border bg-card space-y-3">
          <div class="flex items-start gap-2">
            <span class="pill pill-destructive text-[10px] uppercase font-mono shrink-0 mt-0.5">Before</span>
            <p class="text-xs text-muted-foreground line-through font-mono leading-relaxed">${App.escapeHtml(b.original)}</p>
          </div>
          <div class="flex items-start gap-2 pt-2 border-t border-border">
            <span class="pill pill-primary text-[10px] uppercase font-mono shrink-0 mt-0.5">High-Impact</span>
            <p class="text-xs text-ink font-mono font-medium leading-relaxed">${App.escapeHtml(b.improved)}</p>
          </div>
          <p class="text-[11px] text-muted-foreground italic pt-1">${App.escapeHtml(b.reason)}</p>
        </div>
      `).join("");
    }

    // Smooth scroll down to results
    container.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const updateDimensionBar = (key, value) => {
    const textEl = document.getElementById(`score-dim-${key}`);
    const barEl = document.getElementById(`bar-dim-${key}`);
    if (textEl) textEl.textContent = `${value} / 25`;
    if (barEl) {
      const pct = Math.min(100, Math.round((value / 25) * 100));
      barEl.style.width = `${pct}%`;
    }
  };

  return { init };
})();

document.addEventListener("DOMContentLoaded", ResumeReviewView.init);

