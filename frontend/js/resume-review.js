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

          const rawSkills = resp.skills || [];
          currentSkills = rawSkills.map(normalizeSkillName).filter(Boolean);
          renderSkillsChips(currentSkills);

          // Auto-persist extracted skills to user database record so Dashboard immediately reflects them!
          try {
            await API.resume.updateSkills(currentSkills);
          } catch (syncErr) {
            console.warn("Auto-syncing skills to database:", syncErr);
          }

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
   * Safe skill name normalizer: converts both dicts and strings into clean display names
   */
  const normalizeSkillName = (s) => {
    if (!s) return "";
    if (typeof s === "object") {
      return s.canonical_name || s.name || s.skill_id || "";
    }
    return String(s).trim();
  };

  /**
   * Extracted Skills Chips & Custom Skill Management
   */
  const setupSkillsManager = () => {
    const customInput = document.getElementById("custom-skill-input");
    const addBtn = document.getElementById("btn-add-skill");
    const confirmBtn = document.getElementById("btn-confirm-skills");

    const addSkill = () => {
      const raw = customInput?.value.trim();
      if (!raw) return;

      const skill = normalizeSkillName(raw);
      if (!skill) return;

      const alreadyExists = currentSkills.some(s => s.toLowerCase() === skill.toLowerCase());
      if (!alreadyExists) {
        currentSkills.push(skill);
        renderSkillsChips(currentSkills);
        if (customInput) customInput.value = "";
        App.showToast(`Added "${skill}". Click "Confirm & Save Skills" to persist.`, "info");
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

    confirmBtn?.addEventListener("click", async () => {
      confirmBtn.disabled = true;
      confirmBtn.textContent = "Saving to database…";

      try {
        // Persist confirmed skills to backend database via PUT /api/resume/skills
        await API.resume.updateSkills(currentSkills);

        const user = API.auth.getUser();
        if (user && user.id) {
          localStorage.setItem(`sg_skills_reviewed_${user.id}`, "true");
        } else {
          localStorage.setItem("sg_skills_reviewed", "true");
        }

        App.showToast(`Saved ${currentSkills.length} skills to your account! Dashboard updated.`, "success");

        confirmBtn.textContent = "✓ Skills Saved to Profile";
        confirmBtn.classList.remove("btn-primary");
        confirmBtn.classList.add("btn-outline");
        setTimeout(() => {
          confirmBtn.disabled = false;
          confirmBtn.textContent = "Confirm & Save Skills →";
          confirmBtn.classList.add("btn-primary");
          confirmBtn.classList.remove("btn-outline");
        }, 3000);
      } catch (err) {
        App.showToast(err.message || "Failed to save skills to database.", "error");
        confirmBtn.disabled = false;
        confirmBtn.textContent = "Confirm & Save Skills →";
      }
    });
  };

  const renderSkillsChips = (skills) => {
    const container = document.getElementById("skills-chip-container");
    const countBadge = document.getElementById("skills-count-badge");
    if (!container) return;

    // Normalize incoming items
    currentSkills = (skills || []).map(normalizeSkillName).filter(Boolean);

    if (countBadge) {
      countBadge.textContent = `${currentSkills.length} ${currentSkills.length === 1 ? "Skill" : "Skills"}`;
    }

    if (currentSkills.length === 0) {
      container.innerHTML = `<span class="text-xs text-muted-foreground italic self-center">No skills extracted yet. Upload a resume above.</span>`;
      return;
    }

    container.innerHTML = currentSkills.map((skill, idx) => `
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
          App.showToast(`Removed "${removed}". Click "Confirm & Save Skills" to persist.`, "info");
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
            currentSkills = latest.extracted_skills.map(normalizeSkillName).filter(Boolean);
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
          const latest = await API.resume.getRecord(records[0].id);
          if (latest) {
            if (textarea && latest.extracted_text) {
              textarea.value = latest.extracted_text;
              const counter = document.getElementById("char-counter");
              if (counter) counter.textContent = `${textarea.value.length.toLocaleString()} characters`;
              App.showToast(`Loaded "${latest.filename}" (${latest.file_type.toUpperCase()}).`, "success");
            }
            if (latest.extracted_skills && latest.extracted_skills.length > 0) {
              currentSkills = latest.extracted_skills.map(normalizeSkillName).filter(Boolean);
              renderSkillsChips(currentSkills);
            }
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
        const user = API.auth.getUser();
        const activeRole = user?.target_role || localStorage.getItem(CONFIG.STORAGE_KEYS.ACTIVE_ROLE) || undefined;
        const critique = await API.resume.critique({ text, target_role: activeRole });
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

  // =========================================================================
  // Copy to clipboard utility
  // =========================================================================
  const copyToClipboard = (text, label) => {
    navigator.clipboard.writeText(text).then(() => {
      App.showToast(`${label} copied to clipboard.`, "success");
    }).catch(() => {
      // Fallback for non-secure contexts
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      App.showToast(`${label} copied to clipboard.`, "success");
    });
  };

  // =========================================================================
  // Render Critique Results
  // =========================================================================
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

    // 3. Things to Add (structured)
    renderThingsToAdd(data.things_to_add || []);

    // 4. Things to Remove (structured)
    renderThingsToRemove(data.things_to_remove || []);

    // 5. Bullet Improvements (with copy/edit/accept)
    renderBulletImprovements(data.bullet_improvements || []);

    // Smooth scroll down to results
    container.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  // =========================================================================
  // Things to Add — structured rendering
  // =========================================================================
  const renderThingsToAdd = (items) => {
    const listAdd = document.getElementById("list-things-to-add");
    if (!listAdd) return;

    if (items.length === 0) {
      listAdd.innerHTML = `<li class="text-muted-foreground italic">No critical missing items identified. Great work!</li>`;
      return;
    }

    // Support both old format (string[]) and new format (ThingToAdd[])
    listAdd.innerHTML = items.map((item, idx) => {
      if (typeof item === "string") {
        // Legacy string format fallback
        return `
          <li class="flex items-start gap-2 p-2 rounded-lg bg-secondary/50">
            <span class="text-emerald-600 font-bold font-mono text-sm shrink-0">+</span>
            <span class="text-foreground leading-relaxed">${App.escapeHtml(item)}</span>
          </li>
        `;
      }

      const suggestion = item.suggestion || "";
      const section = item.section || "";
      const why = item.why || "";
      const context = item.context || "";
      const needsInput = item.needs_user_input;

      return `
        <li class="p-3 rounded-xl bg-secondary/40 border border-border space-y-2">
          <div class="flex items-start gap-2">
            <span class="text-emerald-600 font-bold font-mono text-sm shrink-0 mt-0.5">+</span>
            <div class="space-y-1.5 flex-1 min-w-0">
              <p class="text-foreground text-xs font-medium leading-relaxed">${App.escapeHtml(suggestion)}</p>
              ${section ? `<span class="inline-block px-2 py-0.5 rounded-full text-[10px] font-mono bg-secondary border border-border text-muted-foreground">${App.escapeHtml(section)}</span>` : ""}
              ${context ? `<p class="text-[11px] text-muted-foreground italic leading-relaxed"><span class="font-semibold not-italic text-foreground/60">Context:</span> "${App.escapeHtml(context)}"</p>` : ""}
              ${why ? `<p class="text-[11px] text-muted-foreground leading-relaxed"><span class="font-semibold text-foreground/60">Why:</span> ${App.escapeHtml(why)}</p>` : ""}
              ${needsInput ? `<span class="inline-flex items-center gap-1 text-[10px] font-mono text-amber-700"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v4m0 4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"/></svg> You need to provide this information</span>` : ""}
            </div>
          </div>
        </li>
      `;
    }).join("");
  };

  // =========================================================================
  // Things to Remove — structured rendering with action badges
  // =========================================================================
  const renderThingsToRemove = (items) => {
    const listRemove = document.getElementById("list-things-to-remove");
    if (!listRemove) return;

    if (items.length === 0) {
      listRemove.innerHTML = `<li class="text-muted-foreground italic">Zero fluff words or clichés detected. High technical signal.</li>`;
      return;
    }

    // Support both old format (string[]) and new format (ThingToRemove[])
    listRemove.innerHTML = items.map((item, idx) => {
      if (typeof item === "string") {
        return `
          <li class="flex items-start gap-2 p-2 rounded-lg bg-secondary/50">
            <span class="text-rose-600 font-bold font-mono text-sm shrink-0">✕</span>
            <span class="text-foreground leading-relaxed">${App.escapeHtml(item)}</span>
          </li>
        `;
      }

      const original = item.original_line || "";
      const issue = item.issue || "";
      const recommendation = item.recommendation || "";
      const action = (item.action || "REWRITE").toUpperCase();
      const section = item.section || "";

      const actionColor = action === "REMOVE" ? "text-rose-700 bg-rose-50 border-rose-200"
        : action === "KEEP" ? "text-emerald-700 bg-emerald-50 border-emerald-200"
        : "text-amber-700 bg-amber-50 border-amber-200";

      return `
        <li class="p-3 rounded-xl bg-secondary/40 border border-border space-y-2">
          <div class="flex items-start gap-2">
            <span class="text-rose-600 font-bold font-mono text-sm shrink-0 mt-0.5">✕</span>
            <div class="space-y-1.5 flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="inline-block px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold border ${actionColor}">${App.escapeHtml(action)}</span>
                ${section ? `<span class="inline-block px-2 py-0.5 rounded-full text-[10px] font-mono bg-secondary border border-border text-muted-foreground">${App.escapeHtml(section)}</span>` : ""}
              </div>
              <p class="text-[11px] text-muted-foreground font-mono leading-relaxed bg-secondary/70 p-2 rounded-lg border border-border">"${App.escapeHtml(original)}"</p>
              <p class="text-[11px] text-muted-foreground leading-relaxed"><span class="font-semibold text-foreground/60">Issue:</span> ${App.escapeHtml(issue)}</p>
              <p class="text-[11px] text-muted-foreground leading-relaxed"><span class="font-semibold text-foreground/60">Recommendation:</span> ${App.escapeHtml(recommendation)}</p>
            </div>
          </div>
        </li>
      `;
    }).join("");
  };

  // =========================================================================
  // Bullet Improvements — with Copy, Edit, Accept
  // =========================================================================
  const renderBulletImprovements = (bullets) => {
    const bulletsContainer = document.getElementById("bullet-improvements-container");
    if (!bulletsContainer) return;

    if (bullets.length === 0) {
      bulletsContainer.innerHTML = `<p class="text-muted-foreground italic text-xs">No bullet points to optimize. Your resume bullets are already well-structured.</p>`;
      return;
    }

    bulletsContainer.innerHTML = bullets.map((b, idx) => `
      <div class="p-4 rounded-2xl border border-border bg-card space-y-3" data-bullet-idx="${idx}">
        <div class="flex items-start gap-2">
          <span class="pill pill-destructive text-[10px] uppercase font-mono shrink-0 mt-0.5">Before</span>
          <p class="text-xs text-muted-foreground line-through font-mono leading-relaxed flex-1 min-w-0" data-original="${App.escapeHtml(b.original)}">${App.escapeHtml(b.original)}</p>
          <button type="button" class="btn-copy-original shrink-0 text-[10px] font-mono text-muted-foreground hover:text-foreground border border-border rounded-lg px-2 py-1 transition-colors" title="Copy original">Copy</button>
        </div>
        <div class="flex items-start gap-2 pt-2 border-t border-border">
          <span class="pill pill-primary text-[10px] uppercase font-mono shrink-0 mt-0.5">High-Impact</span>
          <div class="flex-1 min-w-0">
            <p class="text-xs text-ink font-mono font-medium leading-relaxed improved-text">${App.escapeHtml(b.improved)}</p>
            <textarea class="edit-improved hidden w-full mt-2 p-2 text-xs font-mono border border-border rounded-lg bg-background resize-y" rows="3">${App.escapeHtml(b.improved)}</textarea>
          </div>
          <div class="flex flex-col gap-1 shrink-0">
            <button type="button" class="btn-copy-improved text-[10px] font-mono text-muted-foreground hover:text-foreground border border-border rounded-lg px-2 py-1 transition-colors" title="Copy improved">Copy</button>
            <button type="button" class="btn-edit-improved text-[10px] font-mono text-muted-foreground hover:text-foreground border border-border rounded-lg px-2 py-1 transition-colors" title="Edit suggestion">Edit</button>
            <button type="button" class="btn-accept-improved text-[10px] font-mono text-emerald-700 hover:text-emerald-900 border border-emerald-200 bg-emerald-50 rounded-lg px-2 py-1 transition-colors" title="Accept suggestion">Accept</button>
          </div>
        </div>
        <p class="text-[11px] text-muted-foreground italic pt-1">${App.escapeHtml(b.reason)}</p>
      </div>
    `).join("");

    // Attach event listeners
    bulletsContainer.querySelectorAll("[data-bullet-idx]").forEach(card => {
      const idx = card.dataset.bulletIdx;
      const originalText = card.querySelector("[data-original]")?.dataset.original || "";
      const improvedTextEl = card.querySelector(".improved-text");
      const editTextarea = card.querySelector(".edit-improved");

      // Copy Original
      card.querySelector(".btn-copy-original")?.addEventListener("click", () => {
        copyToClipboard(originalText, "Original bullet");
      });

      // Copy Improved
      card.querySelector(".btn-copy-improved")?.addEventListener("click", () => {
        const text = editTextarea && !editTextarea.classList.contains("hidden")
          ? editTextarea.value
          : improvedTextEl?.textContent || "";
        copyToClipboard(text, "Improved bullet");
      });

      // Edit
      card.querySelector(".btn-edit-improved")?.addEventListener("click", (e) => {
        const btn = e.currentTarget;
        if (editTextarea.classList.contains("hidden")) {
          editTextarea.classList.remove("hidden");
          editTextarea.value = improvedTextEl.textContent;
          editTextarea.focus();
          btn.textContent = "Done";
        } else {
          improvedTextEl.textContent = editTextarea.value;
          editTextarea.classList.add("hidden");
          btn.textContent = "Edit";
        }
      });

      // Accept
      card.querySelector(".btn-accept-improved")?.addEventListener("click", (e) => {
        const btn = e.currentTarget;
        const text = editTextarea && !editTextarea.classList.contains("hidden")
          ? editTextarea.value
          : improvedTextEl?.textContent || "";
        editTextarea.classList.add("hidden");
        improvedTextEl.textContent = text;
        card.querySelector(".btn-edit-improved").textContent = "Edit";

        // Visual feedback
        card.style.borderColor = "var(--accent)";
        card.style.opacity = "0.7";
        btn.textContent = "✓ Accepted";
        btn.disabled = true;
        App.showToast("Suggestion accepted. Copy the improved version to use in your resume.", "success");
      });
    });
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
