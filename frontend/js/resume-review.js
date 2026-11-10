/**
 * SkillGraph Resume Review & Rating Controller
 * Handles resume file upload, skills extraction & management, and 4-dimension critique.
 */

const ResumeReviewView = (() => {
  let selectedFile = null;
  let currentSkills = [];

  const init = async () => {
    // Phase 3 Auth Guard
    if (!API.auth.requireAuth()) return;

    setupCharCounter();
    setupButtons();
    setupDropzone();
    setupSkillsManager();
    await autoLoadSavedResume();
  };

  /**
   * Setup Drag-and-Drop and File Picker
   */
  const setupDropzone = () => {
    const dropzone = document.getElementById("resume-drop-zone");
    const fileInput = document.getElementById("resume-file-input");
    const filenameEl = document.getElementById("resume-filename");
    const statusText = document.getElementById("upload-status-text");
    const uploadBtn = document.getElementById("resume-upload-btn");

    if (!dropzone || !fileInput) return;

    dropzone.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", (e) => {
      const file = e.target.files?.[0];
      if (file) handleFileSelected(file);
    });

    ["dragenter", "dragover"].forEach(evt => {
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.style.borderColor = "var(--accent)";
        dropzone.style.backgroundColor = "var(--secondary)";
      });
    });

    ["dragleave", "drop"].forEach(evt => {
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.style.borderColor = "";
        dropzone.style.backgroundColor = "";
      });
    });

    dropzone.addEventListener("drop", (e) => {
      const file = e.dataTransfer?.files?.[0];
      if (file) handleFileSelected(file);
    });

    const handleFileSelected = (file) => {
      const ext = file.name.split(".").pop().toLowerCase();
      if (!["pdf", "docx"].includes(ext)) {
        App.showToast("Unsupported file format. Please upload a PDF or DOCX resume.", "error");
        return;
      }

      if (file.size > 5 * 1024 * 1024) {
        App.showToast("File size exceeds 5MB limit.", "error");
        return;
      }

      selectedFile = file;
      if (filenameEl) {
        filenameEl.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
      }
      if (statusText) statusText.textContent = "Ready to parse";
      if (uploadBtn) uploadBtn.disabled = false;
    };

    uploadBtn?.addEventListener("click", async () => {
      if (!selectedFile) return;

      uploadBtn.disabled = true;
      uploadBtn.textContent = "Parsing resume in memory…";
      if (statusText) statusText.textContent = "Extracting technical competencies…";

      try {
        const resp = await API.resume.parse(selectedFile);
        if (resp && resp.text) {
          const textarea = document.getElementById("review-resume-text");
          if (textarea) {
            textarea.value = resp.text;
            const counter = document.getElementById("char-counter");
            if (counter) counter.textContent = `${resp.text.length.toLocaleString()} characters`;
          }

          currentSkills = resp.skills || [];
          renderSkillsChips(currentSkills);

          if (statusText) statusText.textContent = `Parsed ${currentSkills.length} skills successfully`;
          App.showToast(`Extracted ${currentSkills.length} skills from ${selectedFile.name}.`, "success");

          // Trigger critique automatically on newly ingested resume
          const critiqueBtn = document.getElementById("btn-run-review");
          critiqueBtn?.click();
        }
      } catch (err) {
        App.showToast(err.message || "Failed to parse resume.", "error");
        if (statusText) statusText.textContent = "Parsing failed";
      } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = "Parse & Ingest Resume";
      }
    });
  };

  /**
   * Extracted Skills Chips & Custom Skill Management
   */
  const setupSkillsManager = () => {
    const customInput = document.getElementById("custom-skill-input");
    const addBtn = document.getElementById("btn-add-skill");
    const confirmBtn = document.getElementById("btn-confirm-skills");

    const addSkill = () => {
      const skill = customInput?.value.trim().toLowerCase();
      if (!skill) return;

      if (!currentSkills.includes(skill)) {
        currentSkills.push(skill);
        renderSkillsChips(currentSkills);
        customInput.value = "";
        App.showToast(`Added "${skill}" to your skills.`, "info");
      } else {
        App.showToast(`"${skill}" is already in your skills list.`, "info");
      }
    };

    addBtn?.addEventListener("click", addSkill);
    customInput?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        addSkill();
      }
    });

    confirmBtn?.addEventListener("click", () => {
      const user = API.auth.getUser();
      if (user && user.id) {
        localStorage.setItem(`sg_skills_reviewed_${user.id}`, "true");
      } else {
        localStorage.setItem("sg_skills_reviewed", "true");
      }
      App.showToast("Skills verified! You can now explore roles or view your dashboard.", "success");
      
      const count = currentSkills.length;
      confirmBtn.textContent = "✓ Skills Confirmed";
      confirmBtn.classList.remove("btn-primary");
      confirmBtn.classList.add("btn-outline");
      setTimeout(() => {
        confirmBtn.textContent = "Confirm & Save Skills →";
        confirmBtn.classList.add("btn-primary");
        confirmBtn.classList.remove("btn-outline");
      }, 3000);
    });
  };

  const renderSkillsChips = (skills) => {
    const container = document.getElementById("skills-chip-container");
    const countBadge = document.getElementById("skills-count-badge");
    if (!container) return;

    if (countBadge) {
      countBadge.textContent = `${skills.length} ${skills.length === 1 ? "Skill" : "Skills"}`;
    }

    if (!skills || skills.length === 0) {
      container.innerHTML = `<span class="text-xs text-muted-foreground italic self-center">No skills extracted yet. Upload a resume above.</span>`;
      return;
    }

    container.innerHTML = skills.map((skill, idx) => `
      <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono bg-secondary border border-border text-foreground transition-all hover:border-foreground/30">
        <span>${App.escapeHtml(skill)}</span>
        <button type="button" class="text-muted-foreground hover:text-rose-600 font-bold ml-0.5 focus:outline-none" title="Remove skill" data-index="${idx}">
          &times;
        </button>
      </span>
    `).join("");

    container.querySelectorAll("button[data-index]").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const idx = parseInt(btn.getAttribute("data-index"), 10);
        if (!isNaN(idx) && idx >= 0 && idx < currentSkills.length) {
          const removed = currentSkills.splice(idx, 1)[0];
          renderSkillsChips(currentSkills);
          App.showToast(`Removed "${removed}".`, "info");
        }
      });
    });
  };

  /**
   * Auto-load user's latest saved resume record from database
   */
  const autoLoadSavedResume = async () => {
    const textarea = document.getElementById("review-resume-text");

    try {
      const records = await API.resume.listRecords();
      if (records && records.length > 0) {
        const latest = await API.resume.getRecord(records[0].id);
        if (latest) {
          if (latest.extracted_text && textarea && !textarea.value.trim()) {
            textarea.value = latest.extracted_text;
            const counter = document.getElementById("char-counter");
            if (counter) counter.textContent = `${textarea.value.length.toLocaleString()} characters`;
          }

          if (latest.extracted_skills && latest.extracted_skills.length > 0) {
            currentSkills = [...latest.extracted_skills];
            renderSkillsChips(currentSkills);
          }

          const filenameEl = document.getElementById("resume-filename");
          if (filenameEl) {
            filenameEl.textContent = `Active: ${latest.filename} (${latest.file_type.toUpperCase()})`;
          }
        }
      }
    } catch {
      // Ignore if no saved resume
    }
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
      if (!API.auth.isAuthenticated()) {
        App.showToast("Please sign in or upload a resume first.", "error");
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
          if (latest.extracted_skills) {
            currentSkills = [...latest.extracted_skills];
            renderSkillsChips(currentSkills);
          }
        } else {
          App.showToast("No uploaded resumes found on your account. Upload a PDF/DOCX file above.", "error");
        }
      } catch (err) {
        App.showToast(err.message || "Failed to retrieve uploaded resume.", "error");
      } finally {
        btnUseUploaded.disabled = false;
        btnUseUploaded.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="mr-1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
          Sync from Uploaded Resume
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
