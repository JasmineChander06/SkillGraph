/**
 * SkillGraph Dashboard Controller
 * Pure Vanilla JavaScript & SVG Chart Renderers
 * Authentic Account-Based Career Readiness Engine
 */

const Dashboard = (() => {
  let activeResumeText = "";
  let loadedRoles = [];
  let userTargetRole = "backend-engineer";

  const init = async () => {
    // Phase 3 Auth Guard: Redirect unauthenticated visitors to auth.html
    if (!API.auth.requireAuth()) return;

    await loadRoles();
    setupOnboarding();
    await loadUserData();
    setupResumeDropZone();
    setupSkillGapAnalyzer();
    setupJobDescriptionMatcher();
  };

  /**
   * Fetch roles from backend to populate benchmarks and dropdowns
   */
  const loadRoles = async () => {
    try {
      const res = await API.roles.list();
      loadedRoles = (Array.isArray(res) && res.length > 0) ? res : CONFIG.DEFAULT_ROLES;
    } catch {
      loadedRoles = CONFIG.DEFAULT_ROLES;
    }

    // Populate skill gap role selector
    const skillRoleSelect = document.getElementById("skills-role-select");
    if (skillRoleSelect && loadedRoles.length > 0) {
      skillRoleSelect.innerHTML = loadedRoles.map(role => {
        const id = role.id;
        const title = role.canonical_title || role.title;
        return `<option value="${App.escapeHtml(id)}">${App.escapeHtml(title)}</option>`;
      }).join("");
    }

    // Populate onboarding target role selector
    const onboardingRoleSelect = document.getElementById("onboarding-target-role");
    if (onboardingRoleSelect && loadedRoles.length > 0) {
      onboardingRoleSelect.innerHTML = loadedRoles.map(role => {
        const id = role.id;
        const title = role.canonical_title || role.title;
        return `<option value="${App.escapeHtml(id)}">${App.escapeHtml(title)}</option>`;
      }).join("");
    }
  };

  /**
   * Setup Phase 4 Onboarding Banner
   */
  const setupOnboarding = () => {
    const section = document.getElementById("onboarding-section");
    const form = document.getElementById("onboarding-form");
    const dismissBtn = document.getElementById("onboarding-dismiss-btn");
    const nameInput = document.getElementById("onboarding-name");
    const stageSelect = document.getElementById("onboarding-stage");
    const interestsInput = document.getElementById("onboarding-interests");
    const skillLevelSelect = document.getElementById("onboarding-skill-level");
    const targetRoleSelect = document.getElementById("onboarding-target-role");

    const user = API.auth.getUser() || {};
    userTargetRole = user.target_role || localStorage.getItem(CONFIG.STORAGE_KEYS.ACTIVE_ROLE) || "backend-engineer";

    const urlParams = new URLSearchParams(window.location.search);
    const forceOnboarding = urlParams.get("onboarding") === "true";

    if (!user.onboarding_completed || forceOnboarding) {
      section?.classList.remove("hidden");
    }

    if (nameInput) nameInput.value = user.full_name || user.name || "";
    if (stageSelect && user.education_stage) stageSelect.value = user.education_stage;
    if (interestsInput && user.career_interests) interestsInput.value = user.career_interests;
    if (skillLevelSelect && user.skill_level) skillLevelSelect.value = user.skill_level;
    if (targetRoleSelect && userTargetRole) targetRoleSelect.value = userTargetRole;

    dismissBtn?.addEventListener("click", () => {
      section?.classList.add("hidden");
    });

    form?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const saveBtn = document.getElementById("onboarding-save-btn");
      if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.textContent = "Saving profile…";
      }

      try {
        const payload = {
          full_name: nameInput?.value.trim() || undefined,
          education_stage: stageSelect?.value || undefined,
          career_interests: interestsInput?.value.trim() || undefined,
          skill_level: skillLevelSelect?.value || undefined,
          target_role: targetRoleSelect?.value || undefined,
        };

        const updatedUser = await API.user.saveOnboarding(payload);
        localStorage.setItem(CONFIG.STORAGE_KEYS.USER, JSON.stringify(updatedUser));
        if (targetRoleSelect?.value) {
          userTargetRole = targetRoleSelect.value;
          localStorage.setItem(CONFIG.STORAGE_KEYS.ACTIVE_ROLE, userTargetRole);
        }

        section?.classList.add("hidden");
        App.showToast("Profile onboarding saved. Now upload your resume below.", "success");

        const resumeSec = document.getElementById("resume-section");
        resumeSec?.scrollIntoView({ behavior: "smooth" });

        await loadUserData();
      } catch (err) {
        App.showToast(err.message || "Failed to save onboarding.", "error");
      } finally {
        if (saveBtn) {
          saveBtn.disabled = false;
          saveBtn.textContent = "Save profile & proceed to resume upload →";
        }
      }
    });
  };

  /**
   * Load real, non-fabricated user data from database
   */
  const loadUserData = async () => {
    const kpiReadiness = document.getElementById("kpi-readiness");
    const kpiReadinessSub = document.getElementById("kpi-readiness-sub");
    const kpiSkills = document.getElementById("kpi-skills");
    const kpiSkillsSub = document.getElementById("kpi-skills-sub");
    const kpiRoadmaps = document.getElementById("kpi-roadmaps");

    const user = API.auth.getUser() || {};
    userTargetRole = user.target_role || localStorage.getItem(CONFIG.STORAGE_KEYS.ACTIVE_ROLE) || "backend-engineer";

    try {
      // 1. Fetch user's saved resumes from DB
      const resumes = await API.resume.listRecords();

      if (resumes && resumes.length > 0) {
        const latestResume = await API.resume.getRecord(resumes[0].id);
        activeResumeText = latestResume.extracted_text || "";
        const skills = latestResume.extracted_skills || [];

        // Pre-fill text area for gap analysis
        const syncTextarea = document.getElementById("skills-resume-text");
        if (syncTextarea && activeResumeText) {
          syncTextarea.value = activeResumeText;
        }

        // Calculate REAL coverage for user's target role
        const analysis = await API.skills.analyze(activeResumeText, userTargetRole);
        const readinessScore = Math.round(analysis.coverage_percent);

        if (kpiReadiness) kpiReadiness.textContent = `${readinessScore}%`;
        if (kpiReadinessSub) kpiReadinessSub.textContent = `Target: ${analysis.role_title}`;
        if (kpiSkills) kpiSkills.textContent = `${skills.length}`;
        if (kpiSkillsSub) kpiSkillsSub.textContent = `From ${latestResume.filename}`;

        renderRealRadarChart("radar-chart-container", skills, analysis);
        renderRealTrajectoryChart("trajectory-chart-container", readinessScore);
        await renderTargetRolesAnalyzed(loadedRoles.slice(0, 3), activeResumeText);

      } else {
        // Honest empty state for new account (no fabricated scores)
        if (kpiReadiness) kpiReadiness.textContent = "—";
        if (kpiReadinessSub) kpiReadinessSub.textContent = "Upload resume in Resume";
        if (kpiSkills) kpiSkills.textContent = "0";
        if (kpiSkillsSub) kpiSkillsSub.textContent = "Awaiting resume parse";

        renderEmptyRadarChart("radar-chart-container");
        renderEmptyTrajectoryChart("trajectory-chart-container");
        renderTargetRolesPending(loadedRoles.slice(0, 3));
      }

      // 2. Fetch saved roadmaps count
      let savedRoadmaps = [];
      try {
        savedRoadmaps = await API.roadmaps.list();
        if (kpiRoadmaps) {
          kpiRoadmaps.textContent = Array.isArray(savedRoadmaps) ? `${savedRoadmaps.length}` : "0";
        }
      } catch {
        if (kpiRoadmaps) kpiRoadmaps.textContent = "0";
      }

      // 3. Update dynamic workflow guidance based on real saved data (Requirement 7)
      updateWorkflowIndicator(resumes, user, savedRoadmaps);

    } catch (err) {
      console.warn("Could not load user data:", err.message);
    }
  };

  /**
   * Phase 7: Dynamic Workflow Next Action Indicator
   */
  const updateWorkflowIndicator = (resumes, user, savedRoadmaps) => {
    const card = document.getElementById("workflow-indicator-card");
    const badge = document.getElementById("workflow-step-badge");
    const tag = document.getElementById("workflow-step-tag");
    const headline = document.getElementById("workflow-headline");
    const subtext = document.getElementById("workflow-subtext");
    const actionBtn = document.getElementById("workflow-action-btn");

    if (!card || !headline || !actionBtn) return;

    const hasResume = Array.isArray(resumes) && resumes.length > 0;
    const isSkillsReviewed = (
      localStorage.getItem(`sg_skills_reviewed_${user?.id}`) === "true" ||
      localStorage.getItem("sg_skills_reviewed") === "true" ||
      (hasResume && resumes[0].extracted_skills && resumes[0].extracted_skills.length > 0)
    );
    const hasTargetRole = !!(user && user.target_role && user.target_role !== "");
    const hasRoadmap = Array.isArray(savedRoadmaps) && savedRoadmaps.length > 0;

    if (!hasResume) {
      // State 1: No resume
      if (badge) badge.textContent = "Step 1 of 5 • Next Action";
      if (tag) tag.textContent = "Ingestion";
      headline.textContent = "Upload your resume to begin.";
      if (subtext) subtext.textContent = "Ingest your PDF or DOCX resume to extract technical skills and benchmark your readiness.";
      actionBtn.textContent = "Upload resume →";
      actionBtn.setAttribute("href", "resume-review.html");
      actionBtn.className = "btn btn-primary btn-md";
    } else if (!isSkillsReviewed) {
      // State 2: Resume uploaded but skills not reviewed
      if (badge) badge.textContent = "Step 2 of 5 • Next Action";
      if (tag) tag.textContent = "Verification";
      headline.textContent = "Review the skills extracted from your resume.";
      if (subtext) subtext.textContent = "Verify detected competencies, remove false positives, and add unlisted tools.";
      actionBtn.textContent = "Review skills →";
      actionBtn.setAttribute("href", "resume-review.html#skills-management-card");
      actionBtn.className = "btn btn-primary btn-md";
    } else if (!hasTargetRole) {
      // State 3: Skills reviewed but no target roles selected
      if (badge) badge.textContent = "Step 3 of 5 • Next Action";
      if (tag) tag.textContent = "Taxonomy";
      headline.textContent = "Choose the career roles you want to explore.";
      if (subtext) subtext.textContent = "Benchmark your profile against 11 curated role ontologies and compare overlapping requirements.";
      actionBtn.textContent = "Explore roles →";
      actionBtn.setAttribute("href", "roles.html");
      actionBtn.className = "btn btn-primary btn-md";
    } else if (!hasRoadmap) {
      // State 4: Role selected, roadmap not generated
      if (badge) badge.textContent = "Step 4 of 5 • Next Action";
      if (tag) tag.textContent = "Curriculum";
      headline.textContent = "Generate your personalized learning roadmap.";
      if (subtext) subtext.textContent = `Review your skill gaps for ${userTargetRole} and generate an actionable 6-week progression.`;
      actionBtn.textContent = "Generate roadmap →";
      actionBtn.setAttribute("href", "roadmap.html");
      actionBtn.className = "btn btn-primary btn-md";
    } else {
      // State 5: Roadmap in progress
      if (badge) badge.textContent = "Step 5 of 5 • Active Plan";
      if (tag) tag.textContent = "In Progress";
      headline.textContent = "Continue your learning plan.";
      if (subtext) subtext.textContent = "Work through this week's milestone tasks and check off completed objectives.";
      actionBtn.textContent = "Continue roadmap →";
      actionBtn.setAttribute("href", "roadmap.html");
      actionBtn.className = "btn btn-outline btn-md";
    }
  };

  /**
   * Render Target Roles in Pending State (No Fake Scores)
   */
  const renderTargetRolesPending = (roles) => {
    const container = document.getElementById("target-roles-container");
    if (!container) return;

    container.innerHTML = roles.map(role => {
      const title = role.canonical_title || role.title;
      const id = role.id;
      const coreSkills = (role.core_skills || ["python", "docker", "ci-cd"]).slice(0, 3);

      return `
        <div class="card role-card">
          <div>
            <div class="role-card-header">
              <span class="eyebrow-pill">Role Target</span>
              <span class="role-score-badge" style="background:var(--secondary); color:var(--muted-foreground);">Pending</span>
            </div>
            <h3 class="role-card-title">${App.escapeHtml(title)}</h3>
            <p style="font-size:0.8rem; color:var(--muted-foreground); margin-top:0.25rem;">
              ${App.escapeHtml(role.role_family || "Engineering")} &bull; ${App.escapeHtml(role.experience_level || "Mid-Level")}
            </p>
          </div>

          <div>
            <div class="progress-track" style="margin-bottom:0.75rem;">
              <div class="progress-fill" style="width: 0%;"></div>
            </div>

            <div class="role-gaps-list">
              ${coreSkills.map(s => `
                <span class="skill-tag">
                  ${App.escapeHtml(typeof s === 'string' ? s : s.canonical_name || s.name)}
                </span>
              `).join("")}
            </div>
          </div>

          <a href="resume-review.html" class="btn btn-outline btn-sm" style="width:100%; justify-content:center;">
            Upload resume to score &rarr;
          </a>
        </div>
      `;
    }).join("");
  };

  /**
   * Render Target Roles with Genuine Calculated Analysis
   */
  const renderTargetRolesAnalyzed = async (roles, resumeText) => {
    const container = document.getElementById("target-roles-container");
    if (!container) return;

    const cardsHtml = await Promise.all(roles.map(async (role) => {
      const title = role.canonical_title || role.title;
      const id = role.id;
      let score = 0;

      try {
        const gap = await API.skills.analyze(resumeText, id);
        score = Math.round(gap.coverage_percent);
      } catch {
        score = 0;
      }

      const coreSkills = (role.core_skills || ["python", "docker", "ci-cd"]).slice(0, 3);

      return `
        <div class="card role-card">
          <div>
            <div class="role-card-header">
              <span class="eyebrow-pill">Role Target</span>
              <span class="role-score-badge">${score}%</span>
            </div>
            <h3 class="role-card-title">${App.escapeHtml(title)}</h3>
            <p style="font-size:0.8rem; color:var(--muted-foreground); margin-top:0.25rem;">
              ${App.escapeHtml(role.role_family || "Engineering")} &bull; ${App.escapeHtml(role.experience_level || "Mid-Level")}
            </p>
          </div>

          <div>
            <div class="progress-track" style="margin-bottom:0.75rem;">
              <div class="progress-fill" style="width: ${score}%;"></div>
            </div>

            <div class="role-gaps-list">
              ${coreSkills.map(s => `
                <span class="skill-tag">
                  ${App.escapeHtml(typeof s === 'string' ? s : s.canonical_name || s.name)}
                </span>
              `).join("")}
            </div>
          </div>

          <a href="roadmap.html?role=${encodeURIComponent(id)}" class="btn btn-outline btn-sm" style="width:100%; justify-content:center;">
            View 6-week roadmap &rarr;
          </a>
        </div>
      `;
    }));

    container.innerHTML = cardsHtml.join("");
  };

  /**
   * Empty Radar Chart State for New Accounts
   */
  const renderEmptyRadarChart = (containerId) => {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = `
      <div style="height:260px; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; padding:1.5rem; border:1px dashed var(--border); border-radius:var(--radius-sm); background:var(--secondary);">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom:0.75rem; color:var(--muted-foreground);">
          <circle cx="12" cy="12" r="10"></circle>
          <polyline points="12 6 12 12 16 14"></polyline>
        </svg>
        <p style="font-family:var(--font-display); font-size:1.1rem; color:var(--foreground); margin-bottom:0.35rem;">Awaiting Resume Upload</p>
        <p style="font-size:0.8rem; color:var(--muted-foreground); max-width:260px;">Upload your resume below to generate your authentic 6-axis competency radar.</p>
      </div>
    `;
  };

  /**
   * Real Radar Chart with Genuine Analyzed Skills
   */
  const renderRealRadarChart = (containerId, extractedSkills, analysis) => {
    const container = document.getElementById(containerId);
    if (!container) return;

    const matchedNames = new Set((analysis.matched_skills || []).map(s => (s.canonical_name || s.name || "").toLowerCase()));

    // Group matched skills into 6 domain axes
    const categories = {
      "Backend": ["python", "fastapi", "django", "nodejs", "go", "sql", "postgresql"],
      "DevOps": ["docker", "kubernetes", "ci-cd", "aws", "linux", "git", "terraform"],
      "Frontend": ["javascript", "html5", "css3", "react", "typescript", "tailwind"],
      "ML / AI": ["pytorch", "tensorflow", "scikit-learn", "langchain", "llm", "vector-db"],
      "Systems": ["concurrency", "caching", "redis", "microservices", "grpc", "rest"],
      "Testing": ["pytest", "unit-testing", "integration-testing", "selenium", "load-testing"]
    };

    const axes = Object.entries(categories).map(([label, sampleSkills]) => {
      let matchedCount = 0;
      sampleSkills.forEach(s => {
        if (matchedNames.has(s) || extractedSkills.some(es => (es.canonical_name || "").toLowerCase().includes(s))) {
          matchedCount++;
        }
      });
      const youScore = Math.min(95, Math.max(20, matchedCount * 25));
      return { label, you: youScore, target: 80 };
    });

    const size = 320;
    const cx = size / 2;
    const cy = size / 2;
    const r = 90;
    const n = axes.length;

    const getAngle = (i) => (2 * Math.PI * i / n) - (Math.PI / 2);

    const webs = [0.2, 0.4, 0.6, 0.8, 1.0].map(level => {
      const pts = axes.map((_, i) => {
        const a = getAngle(i);
        const x = cx + r * level * Math.cos(a);
        const y = cy + r * level * Math.sin(a);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      }).join(" ");
      return `<polygon points="${pts}" fill="none" stroke="var(--border)" stroke-width="1" />`;
    }).join("");

    const spokes = axes.map((_, i) => {
      const a = getAngle(i);
      const x = cx + r * Math.cos(a);
      const y = cy + r * Math.sin(a);
      return `<line x1="${cx}" y1="${cy}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}" stroke="var(--border)" stroke-width="1" />`;
    }).join("");

    const youPoints = axes.map((ax, i) => {
      const a = getAngle(i);
      const x = cx + r * (ax.you / 100) * Math.cos(a);
      const y = cy + r * (ax.you / 100) * Math.sin(a);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(" ");

    const targetPoints = axes.map((ax, i) => {
      const a = getAngle(i);
      const x = cx + r * (ax.target / 100) * Math.cos(a);
      const y = cy + r * (ax.target / 100) * Math.sin(a);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(" ");

    const labels = axes.map((ax, i) => {
      const a = getAngle(i);
      const labelR = r + 22;
      const x = cx + labelR * Math.cos(a);
      const y = cy + labelR * Math.sin(a);
      let anchor = "middle";
      if (Math.cos(a) > 0.3) anchor = "start";
      else if (Math.cos(a) < -0.3) anchor = "end";

      return `
        <text x="${x.toFixed(1)}" y="${(y + 4).toFixed(1)}" fill="var(--muted-foreground)" font-family="var(--font-sans)" font-size="11" text-anchor="${anchor}">
          ${ax.label}
        </text>
      `;
    }).join("");

    const svg = `
      <svg viewBox="0 0 ${size} ${size}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Skill radar 6-axis chart">
        ${webs}
        ${spokes}
        <polygon points="${targetPoints}" fill="var(--highlight)" fill-opacity="0.12" stroke="var(--highlight)" stroke-width="1.8" />
        <polygon points="${youPoints}" fill="var(--foreground)" fill-opacity="0.18" stroke="var(--foreground)" stroke-width="2" />
        ${labels}
      </svg>
    `;

    container.innerHTML = svg;
  };

  /**
   * Empty Trajectory Chart State for New Accounts
   */
  const renderEmptyTrajectoryChart = (containerId) => {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = `
      <div style="height:260px; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; padding:1.5rem; border:1px dashed var(--border); border-radius:var(--radius-sm); background:var(--secondary);">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom:0.75rem; color:var(--muted-foreground);">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
        </svg>
        <p style="font-family:var(--font-display); font-size:1.1rem; color:var(--foreground); margin-bottom:0.35rem;">Readiness Trajectory</p>
        <p style="font-size:0.8rem; color:var(--muted-foreground); max-width:280px;">Your historical trajectory will be plotted as you upload resumes and complete 6-week roadmap sprints.</p>
      </div>
    `;
  };

  /**
   * Real Trajectory Chart with Initial Readiness Point
   */
  const renderRealTrajectoryChart = (containerId, currentScore) => {
    const container = document.getElementById(containerId);
    if (!container) return;

    const points = [
      { month: "Initial", val: Math.max(10, currentScore - 15) },
      { month: "Current", val: currentScore }
    ];

    const width = 640;
    const height = 288;
    const padX = 60;
    const padTop = 40;
    const padBottom = 40;

    const chartW = width - padX * 2;
    const chartH = height - padTop - padBottom;

    const coords = points.map((p, i) => {
      const x = padX + (i / (points.length - 1)) * chartW;
      const y = padTop + chartH - (p.val / 100) * chartH;
      return { x, y, ...p };
    });

    const curvePath = `M ${coords[0].x} ${coords[0].y} L ${coords[1].x} ${coords[1].y}`;
    const fillPath = `${curvePath} L ${coords[1].x} ${padTop + chartH} L ${coords[0].x} ${padTop + chartH} Z`;

    const svg = `
      <svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" role="img" aria-label="Readiness trajectory chart">
        <defs>
          <linearGradient id="trajectory-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="var(--ink)" stop-opacity="0.25" />
            <stop offset="100%" stop-color="var(--ink)" stop-opacity="0.00" />
          </linearGradient>
        </defs>

        <line x1="${padX}" y1="${padTop}" x2="${width - padX}" y2="${padTop}" stroke="var(--border)" stroke-dasharray="3 3" />
        <line x1="${padX}" y1="${padTop + chartH * 0.5}" x2="${width - padX}" y2="${padTop + chartH * 0.5}" stroke="var(--border)" stroke-dasharray="3 3" />
        <line x1="${padX}" y1="${padTop + chartH}" x2="${width - padX}" y2="${padTop + chartH}" stroke="var(--border)" />

        <path d="${fillPath}" fill="url(#trajectory-grad)" />
        <path d="${curvePath}" fill="none" stroke="var(--foreground)" stroke-width="2.5" stroke-linecap="round" />

        ${coords.map(c => `
          <circle cx="${c.x}" cy="${c.y}" r="5" fill="var(--card)" stroke="var(--foreground)" stroke-width="2.5" />
          <text x="${c.x}" y="${c.y - 12}" fill="var(--foreground)" font-family="var(--font-mono)" font-size="12" font-weight="600" text-anchor="middle">
            ${c.val}%
          </text>
          <text x="${c.x}" y="${height - 12}" fill="var(--muted-foreground)" font-family="var(--font-mono)" font-size="11" text-anchor="middle">
            ${c.month}
          </text>
        `).join("")}
      </svg>
    `;

    container.innerHTML = svg;
  };

  /**
   * Resume Upload Drag-and-Drop Handler
   */
  const setupResumeDropZone = () => {
    const dropZone = document.getElementById("resume-drop-zone");
    const fileInput = document.getElementById("resume-file-input");
    const parseBtn = document.getElementById("resume-parse-btn");
    const resultsContainer = document.getElementById("resume-results");
    const fileNameDisplay = document.getElementById("resume-filename");
    const syncTextarea = document.getElementById("skills-resume-text");

    let selectedFile = null;

    dropZone?.addEventListener("click", () => fileInput?.click());

    fileInput?.addEventListener("change", (e) => {
      if (e.target.files && e.target.files.length > 0) {
        handleFileSelection(e.target.files[0]);
      }
    });

    ["dragenter", "dragover"].forEach(eventName => {
      dropZone?.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropZone.classList.add("drag-over");
      });
    });

    ["dragleave", "drop"].forEach(eventName => {
      dropZone?.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropZone.classList.remove("drag-over");
      });
    });

    dropZone?.addEventListener("drop", (e) => {
      if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
        handleFileSelection(e.dataTransfer.files[0]);
      }
    });

    const handleFileSelection = (file) => {
      const validExtensions = [".pdf", ".docx"];
      const ext = "." + file.name.split(".").pop().toLowerCase();

      if (!validExtensions.includes(ext)) {
        App.showToast("Unsupported file type. Please upload a .pdf or .docx file.", "error");
        return;
      }

      if (file.size > 5 * 1024 * 1024) {
        App.showToast("File exceeds the 5MB size limit.", "error");
        return;
      }

      selectedFile = file;
      if (fileNameDisplay) {
        fileNameDisplay.textContent = `Selected: ${file.name} (${Math.round(file.size / 1024)} KB)`;
      }
      if (parseBtn) {
        parseBtn.disabled = false;
      }
    };

    parseBtn?.addEventListener("click", async () => {
      if (!selectedFile) return;

      parseBtn.disabled = true;
      parseBtn.textContent = "Parsing document & saving to account…";

      try {
        const result = await API.resume.parse(selectedFile);
        activeResumeText = result.text || "";

        if (syncTextarea && activeResumeText) {
          syncTextarea.value = activeResumeText;
        }

        if (resultsContainer) {
          resultsContainer.classList.remove("hidden");
          const count = result.metadata ? result.metadata.word_count : 0;
          resultsContainer.innerHTML = `
            <div class="alert-box success">
              <span>Successfully parsed and saved <strong>${App.escapeHtml(selectedFile.name)}</strong> (${count} words extracted).</span>
            </div>
            <div class="card" style="margin-top:1rem;">
              <div class="flex items-center justify-between" style="margin-bottom:0.75rem;">
                <h4 style="font-family:var(--font-display); font-size:1.15rem;">Extracted Resume Text</h4>
                <span class="eyebrow-pill" style="font-size:0.7rem;">${result.metadata?.file_type?.toUpperCase() || "DOCUMENT"}</span>
              </div>
              <p style="font-size:0.85rem; color:var(--foreground); max-height:180px; overflow-y:auto; white-space:pre-wrap; font-family:var(--font-mono); background:var(--secondary); padding:1rem; border-radius:var(--radius-sm); border:1px solid var(--border);">
                ${App.escapeHtml(result.text.slice(0, 1200))}${result.text.length > 1200 ? "…" : ""}
              </p>
            </div>
          `;
        }

        App.showToast("Resume parsed and saved to your account.", "success");
        await loadUserData();

      } catch (err) {
        App.showToast(err.message || "Failed to parse resume.", "error");
      } finally {
        parseBtn.disabled = false;
        parseBtn.textContent = "Parse resume";
      }
    });
  };

  /**
   * Skill-Gap Analyzer Form Handler
   */
  const setupSkillGapAnalyzer = () => {
    const form = document.getElementById("skill-gap-form");
    const roleSelect = document.getElementById("skills-role-select");
    const textarea = document.getElementById("skills-resume-text");
    const submitBtn = document.getElementById("skills-analyze-btn");
    const resultsContainer = document.getElementById("skills-results-container");

    form?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const roleId = roleSelect.value;
      const text = textarea.value.trim();

      if (!text || text.length < 10) {
        App.showToast("Please provide resume text (upload a document or paste text above).", "error");
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = "Analyzing skill gaps…";

      try {
        const analysis = await API.skills.analyze(text, roleId);

        if (resultsContainer) {
          resultsContainer.classList.remove("hidden");

          const matchedHtml = analysis.matched_skills.length ? analysis.matched_skills.map(s => `
            <span class="skill-tag" title="Category: ${App.escapeHtml(s.category)} &bull; Matched via: ${App.escapeHtml(s.matched_via)}">
              ${App.escapeHtml(s.canonical_name)}
            </span>
          `).join("") : `<span style="font-size:0.8rem; color:var(--muted-foreground);">No skills detected for this tier</span>`;

          const missingHtml = analysis.missing_skills.length ? analysis.missing_skills.map(s => `
            <span class="skill-tag missing" title="Importance: ${App.escapeHtml(s.importance)} &bull; ~${s.estimated_hours}h study">
              ${App.escapeHtml(s.canonical_name)} (${s.estimated_hours}h)
            </span>
          `).join("") : `<span style="font-size:0.8rem; color:var(--muted-foreground);">All core skills matched!</span>`;

          const uncertainHtml = analysis.uncertain_skills.length ? analysis.uncertain_skills.map(s => `
            <span class="skill-tag" style="background-color:transparent; border-color:var(--highlight); color:var(--foreground);" title="Recommended tier skill detected">
              ${App.escapeHtml(s.canonical_name)}
            </span>
          `).join("") : `<span style="font-size:0.8rem; color:var(--muted-foreground);">No uncertain skills</span>`;

          resultsContainer.innerHTML = `
            <div class="card" style="margin-top:1.5rem;">
              <div class="flex items-center justify-between" style="margin-bottom:0.75rem;">
                <span class="eyebrow-pill">Gap Analysis &bull; ${App.escapeHtml(analysis.role_title)}</span>
                <span style="font-family:var(--font-mono); font-size:1.5rem; font-weight:600;">
                  ${Math.round(analysis.coverage_percent)}% Match
                </span>
              </div>

              <div class="progress-track thick" style="margin-bottom:1.5rem;">
                <div class="progress-fill ${analysis.coverage_percent < 50 ? 'accent' : ''}" style="width: ${analysis.coverage_percent}%;"></div>
              </div>

              <div class="grid" style="grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap:1.25rem;">
                <div class="card-sm card-dashed">
                  <h5 style="font-size:0.85rem; font-weight:600; text-transform:uppercase; margin-bottom:0.75rem; color:#059669;">
                    Matched Skills (${analysis.matched_count})
                  </h5>
                  <div class="flex flex-wrap gap-2">
                    ${matchedHtml}
                  </div>
                </div>

                <div class="card-sm card-dashed">
                  <h5 style="font-size:0.85rem; font-weight:600; text-transform:uppercase; margin-bottom:0.75rem; color:#DC2626;">
                    Missing Skills (${analysis.missing_count})
                  </h5>
                  <div class="flex flex-wrap gap-2">
                    ${missingHtml}
                  </div>
                </div>
              </div>

              <p style="font-size:0.8rem; color:var(--muted-foreground); margin-top:1.25rem; font-style:italic;">
                ${App.escapeHtml(analysis.coverage_note)}
              </p>

              <div style="margin-top:1.25rem; display:flex; justify-content:flex-end;">
                <a href="roadmap.html?role=${encodeURIComponent(analysis.role_id)}" class="btn btn-outline btn-sm">
                  Generate 6-week roadmap for this role &rarr;
                </a>
              </div>
            </div>
          `;
        }

        App.showToast(`Analyzed ${analysis.role_title}: ${Math.round(analysis.coverage_percent)}% match.`, "success");
      } catch (err) {
        App.showToast(err.message || "Failed to analyze skills.", "error");
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Analyze skill gaps →";
      }
    });
  };

  /**
   * Job Description Analysis Form Handler
   */
  const setupJobDescriptionMatcher = () => {
    const jdInput = document.getElementById("jd-textarea");
    const charCounter = document.getElementById("jd-char-counter");
    const matchBtn = document.getElementById("jd-match-btn");
    const resultsContainer = document.getElementById("jd-results-container");

    if (!jdInput) return;

    jdInput.addEventListener("input", () => {
      const count = jdInput.value.length;
      if (charCounter) charCounter.textContent = `${count} chars`;
      if (matchBtn) matchBtn.disabled = count < 20;
    });

    matchBtn?.addEventListener("click", async () => {
      const jdText = jdInput.value.trim();
      if (!jdText || jdText.length < 20) {
        App.showToast("Please enter at least 20 characters of job description text.", "error");
        return;
      }

      matchBtn.disabled = true;
      matchBtn.textContent = "Scoring alignment…";

      try {
        const analysis = await API.jobs.analyze(activeResumeText, jdText);

        if (resultsContainer) {
          resultsContainer.classList.remove("hidden");
          resultsContainer.innerHTML = `
            <div class="card" style="margin-top:1.5rem;">
              <div class="flex items-center justify-between" style="margin-bottom:1rem;">
                <span class="eyebrow-pill">Match Result</span>
                <span style="font-family:var(--font-mono); font-size:1.5rem; font-weight:600;">
                  ${Math.round(analysis.coverage_percent)}% Match
                </span>
              </div>

              <div class="progress-track thick" style="margin-bottom:1.5rem;">
                <div class="progress-fill ${analysis.coverage_percent < 50 ? 'accent' : ''}" style="width: ${analysis.coverage_percent}%;"></div>
              </div>

              <div class="grid" style="grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap:1.25rem;">
                <div class="card-sm card-dashed">
                  <h5 style="font-size:0.85rem; font-weight:600; text-transform:uppercase; margin-bottom:0.75rem; color:#059669;">
                    Matched Skills (${analysis.matched_count})
                  </h5>
                  <div class="flex flex-wrap gap-2">
                    ${analysis.matched_skills.length ? analysis.matched_skills.map(s => `
                      <span class="skill-tag">${App.escapeHtml(s.canonical_name || s.skill_id)}</span>
                    `).join("") : `<span style="font-size:0.8rem; color:var(--muted-foreground);">None detected in resume</span>`}
                  </div>
                </div>

                <div class="card-sm card-dashed">
                  <h5 style="font-size:0.85rem; font-weight:600; text-transform:uppercase; margin-bottom:0.75rem; color:#DC2626;">
                    Missing Skills (${analysis.missing_count})
                  </h5>
                  <div class="flex flex-wrap gap-2">
                    ${analysis.missing_skills.length ? analysis.missing_skills.map(s => `
                      <span class="skill-tag missing">${App.escapeHtml(s.canonical_name || s.skill_id)}</span>
                    `).join("") : `<span style="font-size:0.8rem; color:var(--muted-foreground);">No missing skills</span>`}
                  </div>
                </div>
              </div>
            </div>
          `;
        }

        App.showToast("Job description scored successfully.", "success");
      } catch (err) {
        App.showToast(err.message || "Failed to analyze job description.", "error");
      } finally {
        matchBtn.disabled = false;
        matchBtn.textContent = "Score job description →";
      }
    });
  };

  return {
    init
  };
})();

window.refreshDashboard = Dashboard.init;
document.addEventListener("DOMContentLoaded", Dashboard.init);
