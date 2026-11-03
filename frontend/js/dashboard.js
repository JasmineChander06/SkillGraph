/**
 * SkillGraph Dashboard Controller
 * Pure Vanilla JavaScript & SVG Chart Renderers
 */

const Dashboard = (() => {
  let activeResumeText = "";

  const init = async () => {
    renderTrajectoryChart("trajectory-chart-container");
    renderRadarChart("radar-chart-container");
    await loadRolesAndKPIs();
    setupResumeDropZone();
    setupJobDescriptionMatcher();
  };

  /**
   * Fetch roles and user metrics to populate KPIs and target role cards
   */
  const loadRolesAndKPIs = async () => {
    let roles = [];
    try {
      roles = await API.roles.list();
    } catch {
      roles = CONFIG.DEFAULT_ROLES;
    }

    // Render target role cards
    renderTargetRoles(roles.slice(0, 3));

    // Update KPIs if authenticated
    if (API.auth.isAuthenticated()) {
      try {
        const progress = await API.progress.get();
        const kpiReadiness = document.getElementById("kpi-readiness");
        const kpiSkills = document.getElementById("kpi-skills");
        const kpiRoadmaps = document.getElementById("kpi-roadmaps");

        if (kpiReadiness && progress.total_tasks > 0) {
          kpiReadiness.textContent = `${Math.round(progress.completion_percentage)}%`;
        }
        if (kpiSkills) {
          kpiSkills.textContent = progress.total_tasks || "12";
        }
        if (kpiRoadmaps) {
          kpiRoadmaps.textContent = progress.active_roadmaps_count || "1";
        }
      } catch (err) {
        console.warn("Could not load user progress:", err);
      }
    }
  };

  /**
   * Render Target Roles Grid
   */
  const renderTargetRoles = (roles) => {
    const container = document.getElementById("target-roles-container");
    if (!container) return;

    container.innerHTML = roles.map(role => {
      const title = role.canonical_title || role.title;
      const id = role.id;
      const coreSkills = (role.core_skills || ["Python", "Docker", "CI/CD"]).slice(0, 3);
      const score = role.readiness || Math.floor(68 + (id.length * 3) % 20);

      return `
        <div class="card role-card">
          <div>
            <div class="role-card-header">
              <span class="eyebrow-pill">Role Target</span>
              <span class="role-score-badge">${score}%</span>
            </div>
            <h3 class="role-card-title">${App.escapeHtml(title)}</h3>
            <p style="font-size:0.8rem; color:var(--muted-foreground); margin-top:0.25rem;">
              ${App.escapeHtml(role.role_family || "Engineering")} • ${App.escapeHtml(role.experience_level || "Mid-Level")}
            </p>
          </div>

          <div>
            <div class="progress-track">
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
    }).join("");
  };

  /**
   * Pure Vanilla SVG Area Chart Renderer (Readiness Trajectory)
   */
  const renderTrajectoryChart = (containerId) => {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Monthly data points (Jan to Jul)
    const points = [
      { month: "Jan", val: 42 },
      { month: "Feb", val: 50 },
      { month: "Mar", val: 56 },
      { month: "Apr", val: 62 },
      { month: "May", val: 68 },
      { month: "Jun", val: 72 },
      { month: "Jul", val: 78 }
    ];

    const width = 640;
    const height = 288;
    const padX = 40;
    const padTop = 30;
    const padBottom = 35;

    const chartW = width - padX * 2;
    const chartH = height - padTop - padBottom;

    // Coordinate mapping
    const coords = points.map((p, i) => {
      const x = padX + (i / (points.length - 1)) * chartW;
      const y = padTop + chartH - (p.val / 100) * chartH;
      return { x, y, ...p };
    });

    // Build Bézier cubic curve
    let curvePath = `M ${coords[0].x} ${coords[0].y}`;
    for (let i = 0; i < coords.length - 1; i++) {
      const p0 = coords[i];
      const p1 = coords[i + 1];
      const cpX1 = p0.x + (p1.x - p0.x) / 2;
      const cpY1 = p0.y;
      const cpX2 = p0.x + (p1.x - p0.x) / 2;
      const cpY2 = p1.y;
      curvePath += ` C ${cpX1} ${cpY1}, ${cpX2} ${cpY2}, ${p1.x} ${p1.y}`;
    }

    // Closed path for gradient fill
    const fillPath = `${curvePath} L ${coords[coords.length - 1].x} ${padTop + chartH} L ${coords[0].x} ${padTop + chartH} Z`;

    const svg = `
      <svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" role="img" aria-label="Readiness trajectory chart">
        <defs>
          <linearGradient id="trajectory-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="var(--ink)" stop-opacity="0.25" />
            <stop offset="100%" stop-color="var(--ink)" stop-opacity="0.00" />
          </linearGradient>
        </defs>

        <!-- Horizontal Grid Lines -->
        <line x1="${padX}" y1="${padTop}" x2="${width - padX}" y2="${padTop}" stroke="var(--border)" stroke-dasharray="3 3" />
        <line x1="${padX}" y1="${padTop + chartH * 0.5}" x2="${width - padX}" y2="${padTop + chartH * 0.5}" stroke="var(--border)" stroke-dasharray="3 3" />
        <line x1="${padX}" y1="${padTop + chartH}" x2="${width - padX}" y2="${padTop + chartH}" stroke="var(--border)" />

        <!-- Gradient Fill -->
        <path d="${fillPath}" fill="url(#trajectory-grad)" />

        <!-- Monotone Curve Stroke -->
        <path d="${curvePath}" fill="none" stroke="var(--foreground)" stroke-width="2.5" stroke-linecap="round" />

        <!-- Data Point Circles and X-Axis Labels -->
        ${coords.map(c => `
          <circle cx="${c.x}" cy="${c.y}" r="4" fill="var(--card)" stroke="var(--foreground)" stroke-width="2" />
          <text x="${c.x}" y="${height - 10}" fill="var(--muted-foreground)" font-family="var(--font-mono)" font-size="11" text-anchor="middle">
            ${c.month}
          </text>
        `).join("")}
      </svg>
    `;

    container.innerHTML = svg;
  };

  /**
   * Pure Vanilla SVG 6-Axis Spider/Radar Chart Renderer
   */
  const renderRadarChart = (containerId) => {
    const container = document.getElementById(containerId);
    if (!container) return;

    const axes = [
      { label: "Frontend", you: 65, target: 80 },
      { label: "Backend", you: 88, target: 90 },
      { label: "ML", you: 70, target: 85 },
      { label: "DevOps", you: 72, target: 75 },
      { label: "System Design", you: 60, target: 85 },
      { label: "Testing", you: 82, target: 70 }
    ];

    const size = 320;
    const cx = size / 2;
    const cy = size / 2;
    const r = 90;
    const n = axes.length;

    // Helper: angle for axis i
    const getAngle = (i) => (2 * Math.PI * i / n) - (Math.PI / 2);

    // Compute concentric polygon webs (20%, 40%, 60%, 80%, 100%)
    const webs = [0.2, 0.4, 0.6, 0.8, 1.0].map(level => {
      const pts = axes.map((_, i) => {
        const a = getAngle(i);
        const x = cx + r * level * Math.cos(a);
        const y = cy + r * level * Math.sin(a);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      }).join(" ");
      return `<polygon points="${pts}" fill="none" stroke="var(--border)" stroke-width="1" />`;
    }).join("");

    // Spokes from center
    const spokes = axes.map((_, i) => {
      const a = getAngle(i);
      const x = cx + r * Math.cos(a);
      const y = cy + r * Math.sin(a);
      return `<line x1="${cx}" y1="${cy}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}" stroke="var(--border)" stroke-width="1" />`;
    }).join("");

    // "You" Polygon
    const youPoints = axes.map((ax, i) => {
      const a = getAngle(i);
      const x = cx + r * (ax.you / 100) * Math.cos(a);
      const y = cy + r * (ax.you / 100) * Math.sin(a);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(" ");

    // "Target" Polygon
    const targetPoints = axes.map((ax, i) => {
      const a = getAngle(i);
      const x = cx + r * (ax.target / 100) * Math.cos(a);
      const y = cy + r * (ax.target / 100) * Math.sin(a);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(" ");

    // Axis Labels with text anchoring
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

        <!-- Target Series Polygon -->
        <polygon points="${targetPoints}" fill="var(--highlight)" fill-opacity="0.12" stroke="var(--highlight)" stroke-width="1.8" />

        <!-- You Series Polygon -->
        <polygon points="${youPoints}" fill="var(--foreground)" fill-opacity="0.18" stroke="var(--foreground)" stroke-width="2" />

        ${labels}
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

    let selectedFile = null;

    if (!dropZone || !fileInput) return;

    dropZone.addEventListener("click", () => fileInput.click());

    dropZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropZone.style.borderColor = "var(--foreground)";
      dropZone.style.backgroundColor = "var(--secondary)";
    });

    dropZone.addEventListener("dragleave", () => {
      dropZone.style.borderColor = "var(--border)";
      dropZone.style.backgroundColor = "transparent";
    });

    dropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropZone.style.borderColor = "var(--border)";
      dropZone.style.backgroundColor = "transparent";

      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleFileSelection(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) {
        handleFileSelection(e.target.files[0]);
      }
    });

    const handleFileSelection = (file) => {
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
      parseBtn.textContent = "Parsing document…";

      try {
        const result = await API.resume.parse(selectedFile);
        activeResumeText = result.text || "";

        if (resultsContainer) {
          resultsContainer.classList.remove("hidden");
          const count = result.metadata ? result.metadata.word_count : 0;
          resultsContainer.innerHTML = `
            <div class="alert-box success">
              <span>Successfully parsed <strong>${App.escapeHtml(selectedFile.name)}</strong> (${count} words extracted).</span>
            </div>
            <div class="card" style="margin-top:1rem;">
              <h4 style="font-family:var(--font-display); font-size:1.15rem; margin-bottom:0.75rem;">Extracted Resume Text Preview</h4>
              <p style="font-size:0.85rem; color:var(--foreground); max-height:200px; overflow-y:auto; white-space:pre-wrap; font-family:var(--font-mono); background:var(--secondary); padding:1rem; border-radius:var(--radius-sm);">
                ${App.escapeHtml(result.text.slice(0, 1000))}${result.text.length > 1000 ? "…" : ""}
              </p>
            </div>
          `;
        }

        App.showToast("Resume parsed and ingested.", "success");
      } catch (err) {
        App.showToast(err.message || "Failed to parse resume.", "error");
      } finally {
        parseBtn.disabled = false;
        parseBtn.textContent = "Parse resume";
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
      if (!jdText) return;

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
                  <h5 style="font-size:0.85rem; font-weight:600; text-transform:uppercase; margin-bottom:0.75rem;">
                    Matched Skills (${analysis.matched_count})
                  </h5>
                  <div class="flex flex-wrap gap-2">
                    ${analysis.matched_skills.length ? analysis.matched_skills.map(s => `
                      <span class="skill-tag">${App.escapeHtml(s.canonical_name || s.skill_id)}</span>
                    `).join("") : `<span style="font-size:0.8rem; color:var(--muted-foreground);">None detected in resume</span>`}
                  </div>
                </div>

                <div class="card-sm card-dashed">
                  <h5 style="font-size:0.85rem; font-weight:600; text-transform:uppercase; margin-bottom:0.75rem;">
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
        matchBtn.textContent = "Score job description";
      }
    });
  };

  return {
    init
  };
})();

window.refreshDashboard = Dashboard.init;
document.addEventListener("DOMContentLoaded", Dashboard.init);

