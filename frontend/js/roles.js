/**
 * SkillGraph Role Discovery, Taxonomy Explorer & Comparison Controller
 * Pure Vanilla JavaScript (Zero Frameworks, Native Fetch & DOM APIs)
 */

const RolesView = (() => {
  let allRoles = [];
  let activeFilterFamily = "";
  let activeFilterLevel = "";
  let activeFilterMaturity = "all";
  let activeSearchQuery = "";

  const init = async () => {
    // Phase 3 Auth Guard
    if (!API.auth.requireAuth()) return;

    setupFilters();
    setupComparisonForm();
    setupModalListeners();
    await loadRoles();
    handleUrlParameters();
  };

  /**
   * Fetch all roles from the backend catalogue
   */
  const loadRoles = async () => {
    const loadingEl = document.getElementById("roles-loading");
    const gridEl = document.getElementById("roles-grid");

    try {
      allRoles = await API.roles.list();
      if (loadingEl) loadingEl.classList.add("hidden");
      populateComparisonDropdowns(allRoles);
      renderRolesGrid();
    } catch (err) {
      if (loadingEl) {
        loadingEl.className = "alert-box error";
        loadingEl.textContent = "Failed to load role catalogue. Please check backend connectivity.";
      }
    }
  };

  /**
   * Handle pre-selected role in query string (e.g. ?role=harness-engineer or ?compare=backend-engineer,data-engineer)
   */
  const handleUrlParameters = () => {
    const params = new URLSearchParams(window.location.search);
    const roleId = params.get("role");
    const compareParam = params.get("compare");

    if (roleId) {
      openRoleDetails(roleId);
    }

    if (compareParam) {
      const parts = compareParam.split(",");
      if (parts.length === 2) {
        const selectA = document.getElementById("compare-select-a");
        const selectB = document.getElementById("compare-select-b");
        if (selectA && selectB) {
          selectA.value = parts[0];
          selectB.value = parts[1];
          runRoleComparison(parts[0], parts[1]);
          document.getElementById("compare-section")?.scrollIntoView({ behavior: "smooth" });
        }
      }
    }
  };

  /**
   * Setup toolbar filter event listeners
   */
  const setupFilters = () => {
    const searchInput = document.getElementById("roles-search-input");
    const familyFilter = document.getElementById("roles-family-filter");
    const levelFilter = document.getElementById("roles-level-filter");

    const tabAll = document.getElementById("maturity-filter-all");
    const tabEstablished = document.getElementById("maturity-filter-established");
    const tabEmerging = document.getElementById("maturity-filter-emerging");

    searchInput?.addEventListener("input", (e) => {
      activeSearchQuery = e.target.value.trim().toLowerCase();
      renderRolesGrid();
    });

    familyFilter?.addEventListener("change", (e) => {
      activeFilterFamily = e.target.value;
      renderRolesGrid();
    });

    levelFilter?.addEventListener("change", (e) => {
      activeFilterLevel = e.target.value;
      renderRolesGrid();
    });

    const setMaturityTab = (tab, val) => {
      [tabAll, tabEstablished, tabEmerging].forEach(t => t?.classList.remove("active"));
      tab?.classList.add("active");
      activeFilterMaturity = val;
      renderRolesGrid();
    };

    tabAll?.addEventListener("click", () => setMaturityTab(tabAll, "all"));
    tabEstablished?.addEventListener("click", () => setMaturityTab(tabEstablished, "established"));
    tabEmerging?.addEventListener("click", () => setMaturityTab(tabEmerging, "emerging"));
  };

  /**
   * Filter and render role cards to the grid
   */
  const renderRolesGrid = () => {
    const gridEl = document.getElementById("roles-grid");
    if (!gridEl) return;

    const filtered = allRoles.filter(role => {
      // Family filter
      if (activeFilterFamily && role.role_family.toLowerCase() !== activeFilterFamily.toLowerCase()) {
        return false;
      }
      // Experience level filter
      if (activeFilterLevel && role.experience_level.toLowerCase() !== activeFilterLevel.toLowerCase()) {
        return false;
      }
      // Maturity filter
      if (activeFilterMaturity !== "all") {
        if (role.maturity !== activeFilterMaturity) return false;
      }
      // Text search
      if (activeSearchQuery) {
        const title = (role.canonical_title || role.title || "").toLowerCase();
        const desc = (role.description || "").toLowerCase();
        const family = (role.role_family || "").toLowerCase();
        const skills = (role.highlight_skills || []).join(" ").toLowerCase();
        if (!title.includes(activeSearchQuery) && !desc.includes(activeSearchQuery) && !family.includes(activeSearchQuery) && !skills.includes(activeSearchQuery)) {
          return false;
        }
      }
      return true;
    });

    if (filtered.length === 0) {
      gridEl.innerHTML = `
        <div class="card" style="grid-column: 1 / -1; text-align: center; padding: 3rem 1.5rem;">
          <h4 style="font-family:var(--font-display); font-size:1.25rem; margin-bottom:0.5rem;">No matching roles found</h4>
          <p style="color:var(--muted-foreground); font-size:0.9rem;">
            Try broadening your search term or resetting the family and maturity filters.
          </p>
        </div>
      `;
      return;
    }

    gridEl.innerHTML = filtered.map(role => {
      const isEmerging = role.maturity === "emerging";
      const isEntry = role.entry_level_accessible;

      const skillsHtml = (role.highlight_skills || []).map(skill => `
        <span class="skill-tag">${App.escapeHtml(skill)}</span>
      `).join("");

      return `
        <div class="card role-card" id="card-${role.id}">
          <div>
            <div class="role-card-header">
              <span class="eyebrow-pill">${App.escapeHtml(role.role_family)}</span>
              ${isEmerging
                ? `<span class="badge-emerging" title="Emerging specialized discipline"><span class="status-dot awaiting" style="width:6px; height:6px;"></span> Emerging</span>`
                : `<span class="badge-established">Established</span>`
              }
            </div>

            <h3 class="role-card-title">${App.escapeHtml(role.canonical_title || role.title)}</h3>

            <div style="margin-bottom: 0.75rem;">
              ${isEntry
                ? `<span class="accessibility-pill accessible"><span style="color:#059669; font-weight:bold;">&bull;</span> Entry Accessible</span>`
                : `<span class="accessibility-pill prereqs"><span style="color:oklch(0.45 0.12 60); font-weight:bold;">&bull;</span> Prerequisites Required</span>`
              }
              <span style="font-size:0.75rem; color:var(--muted-foreground); margin-left:0.5rem;">&bull; ${App.escapeHtml(role.experience_level.toUpperCase())}</span>
            </div>

            <p class="role-card-desc">${App.escapeHtml(role.description)}</p>

            <div class="role-card-skills">
              ${skillsHtml}
              ${role.core_skill_count > 4 ? `<span style="font-size:0.75rem; color:var(--muted-foreground); align-self:center;">+${role.core_skill_count - 4} more</span>` : ''}
            </div>
          </div>

          <div class="role-card-footer">
            <button class="btn btn-outline btn-sm view-details-btn" data-role-id="${role.id}" type="button">
              Explore details &rarr;
            </button>
            <button class="btn btn-outline btn-sm quick-compare-btn" data-role-id="${role.id}" type="button" title="Select for comparison">
              Compare
            </button>
          </div>
        </div>
      `;
    }).join("");

    // Attach card event listeners
    gridEl.querySelectorAll(".view-details-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const roleId = btn.getAttribute("data-role-id");
        if (roleId) openRoleDetails(roleId);
      });
    });

    gridEl.querySelectorAll(".quick-compare-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const roleId = btn.getAttribute("data-role-id");
        const selectA = document.getElementById("compare-select-a");
        if (selectA && roleId) {
          selectA.value = roleId;
          document.getElementById("compare-section")?.scrollIntoView({ behavior: "smooth" });
          App.showToast(`Selected ${roleId} as Role A for comparison.`, "info");
        }
      });
    });
  };

  /**
   * Open Role Full Details Modal
   */
  const openRoleDetails = async (roleId) => {
    const modal = document.getElementById("role-details-modal");
    const content = document.getElementById("role-modal-content");
    if (!modal || !content) return;

    modal.classList.add("open");
    content.innerHTML = `
      <div style="padding: 2.5rem; text-align: center;">
        <span class="status-dot awaiting"></span>
        <p style="margin-top: 1rem; color: var(--muted-foreground);">Loading profile details for <strong>${App.escapeHtml(roleId)}</strong>…</p>
      </div>
    `;

    try {
      const details = await API.roles.get(roleId);

      const isEmerging = details.maturity === "emerging";
      const isEntry = details.entry_level_accessible;

      // Responsibilities list
      const respHtml = (details.responsibilities || []).map(r => `
        <li style="margin-bottom:0.4rem;">${App.escapeHtml(r)}</li>
      `).join("");

      // Prerequisites tags
      const prereqsHtml = (details.prerequisites_details || []).map(p => `
        <span class="skill-tag" style="background:var(--secondary); border-color:var(--border); color:var(--foreground);">
          ${App.escapeHtml(p.canonical_name)}
        </span>
      `).join("") || `<span style="font-size:0.85rem; color:var(--muted-foreground);">None formally required</span>`;

      // Core skills tags
      const coreSkillsHtml = (details.core_skills_details || []).map(s => `
        <span class="skill-tag" title="Importance: ${App.escapeHtml(s.importance)} &bull; ~${s.estimated_hours}h study">
          ${App.escapeHtml(s.canonical_name)} <span style="opacity:0.7;">(~${s.estimated_hours}h)</span>
        </span>
      `).join("");

      // Optional skills tags
      const optionalSkillsHtml = (details.optional_skills_details || []).map(s => `
        <span class="skill-tag" style="background:transparent; border-color:var(--border); color:var(--muted-foreground);">
          ${App.escapeHtml(s.canonical_name)}
        </span>
      `).join("") || `<span style="font-size:0.85rem; color:var(--muted-foreground);">None specified</span>`;

      // Example projects
      const projectsHtml = (details.example_projects || []).map(proj => `
        <div style="padding:0.75rem 1rem; background:var(--secondary); border:1px solid var(--border); border-radius:var(--radius-sm); margin-bottom:0.6rem;">
          <p style="font-size:0.85rem; color:var(--foreground); line-height:1.45;">${App.escapeHtml(proj)}</p>
        </div>
      `).join("");

      // Related roles cards
      const relatedHtml = (details.related_roles || []).map(rel => `
        <div class="card-sm card-dashed" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
          <div>
            <strong style="font-size:0.9rem;">${App.escapeHtml(rel.canonical_title)}</strong>
            <div style="font-size:0.75rem; color:var(--muted-foreground); margin-top:0.2rem;">
              ${rel.overlap_percentage}% skill overlap &bull; ${rel.shared_core_count} shared core skills
            </div>
          </div>
          <button class="btn btn-outline btn-sm modal-compare-link" data-role-a="${roleId}" data-role-b="${rel.role_id}" type="button">
            Compare &rarr;
          </button>
        </div>
      `).join("") || `<p style="font-size:0.85rem; color:var(--muted-foreground);">No direct matches found</p>`;

      // Market summary block (Evidence-Aware vs Curated Guidance)
      const market = details.market_summary || {};
      let marketHtml = "";

      if (market.has_verified_data && market.metadata) {
        const topReqHtml = (market.top_required_skills || []).map(s => `
          <div style="margin-bottom:0.5rem;">
            <div class="flex justify-between" style="font-size:0.8rem; margin-bottom:0.2rem;">
              <span>${App.escapeHtml(s.canonical_name)}</span>
              <span style="font-family:var(--font-mono); font-weight:600;">${s.frequency_percent}% (${s.frequency_count} postings)</span>
            </div>
            <div class="progress-track" style="height:6px;">
              <div class="progress-fill" style="width:${s.frequency_percent}%;"></div>
            </div>
          </div>
        `).join("");

        marketHtml = `
          <div style="background:var(--secondary); border:1px solid var(--border); border-radius:var(--radius-sm); padding:1.25rem;">
            <div class="flex items-center justify-between" style="margin-bottom:0.75rem;">
              <span class="eyebrow-pill" style="color:#059669; border-color:#059669; background:oklch(0.95 0.04 145);">Verified Empirical Dataset</span>
              <span style="font-family:var(--font-mono); font-size:0.75rem; color:var(--muted-foreground);">
                n = ${market.metadata.sample_size} postings &bull; ${App.escapeHtml(market.metadata.geography)}
              </span>
            </div>
            <p style="font-size:0.8rem; color:var(--muted-foreground); margin-bottom:1rem;">
              Source: ${App.escapeHtml(market.metadata.source)} (${App.escapeHtml(market.metadata.collection_date)}).
            </p>
            <h5 style="font-size:0.85rem; font-weight:600; text-transform:uppercase; margin-bottom:0.75rem;">
              Top Stated Required Skills in Verified Sample:
            </h5>
            ${topReqHtml}
          </div>
        `;
      } else {
        marketHtml = `
          <div style="background:var(--secondary); border:1px solid var(--border); border-radius:var(--radius-sm); padding:1.25rem;">
            <div class="flex items-center justify-between" style="margin-bottom:0.75rem;">
              <span class="eyebrow-pill" style="color:oklch(0.45 0.12 60); border-color:oklch(0.80 0.12 70);">Curated Competency Framework</span>
              <span style="font-family:var(--font-mono); font-size:0.75rem; color:var(--muted-foreground);">Empirical Data Unverified</span>
            </div>
            <p style="font-size:0.82rem; color:var(--muted-foreground); line-height:1.55; margin-bottom:0.75rem;">
              ${App.escapeHtml(market.data_notice || "Curated guidance: No statistically verified dataset of job postings with sufficient sample size is currently available for this role.")}
            </p>
            <p style="font-size:0.8rem; color:var(--muted-foreground); font-style:italic;">
              ${App.escapeHtml(market.recommendation || "Treat curated skills and projects as foundational self-assessment benchmarks rather than empirical market statistics.")}
            </p>
          </div>
        `;
      }

      content.innerHTML = `
        <div style="margin-bottom: 1.5rem;">
          <div class="flex items-center gap-2" style="margin-bottom: 0.5rem;">
            <span class="eyebrow-pill">${App.escapeHtml(details.role_family)}</span>
            ${isEmerging
              ? `<span class="badge-emerging"><span class="status-dot awaiting" style="width:6px; height:6px;"></span> Emerging Discipline</span>`
              : `<span class="badge-established">Established Discipline</span>`
            }
            <span class="badge-established">${App.escapeHtml(details.experience_level.toUpperCase())}</span>
          </div>

          <h2 id="modal-role-title" style="font-family:var(--font-display); font-size:2rem; line-height:1.2; margin-bottom:0.5rem;">
            ${App.escapeHtml(details.canonical_title)}
          </h2>
          <p style="color:var(--muted-foreground); font-size:0.95rem; line-height:1.55;">
            ${App.escapeHtml(details.description)}
          </p>
        </div>

        ${isEmerging && details.emerging_context ? `
          <div style="background:oklch(0.97 0.04 70); border:1px solid oklch(0.85 0.10 70); border-radius:var(--radius-sm); padding:1rem 1.25rem; margin-bottom:1.5rem;">
            <strong style="display:block; font-size:0.85rem; color:oklch(0.35 0.12 60); margin-bottom:0.25rem; font-family:var(--font-mono); text-transform:uppercase;">
              Emerging Role Context & Industry Maturity
            </strong>
            <p style="font-size:0.85rem; color:var(--foreground); line-height:1.5;">
              ${App.escapeHtml(details.emerging_context)}
            </p>
          </div>
        ` : ''}

        <!-- Entry-level Accessibility Guidance -->
        <div style="padding:0.85rem 1.15rem; background:var(--secondary); border:1px solid var(--border); border-radius:var(--radius-sm); margin-bottom:1.5rem;">
          <span style="font-size:0.75rem; font-family:var(--font-mono); font-weight:600; text-transform:uppercase; color:var(--muted-foreground);">
            Accessibility Assessment:
          </span>
          <p style="font-size:0.85rem; margin-top:0.2rem; color:var(--foreground); line-height:1.45;">
            ${App.escapeHtml(details.accessibility_guidance || (isEntry ? "Accessible to entry-level candidates." : "Specialized role requiring prior industry experience."))}
          </p>
        </div>

        <!-- 1. Responsibilities -->
        <div class="role-modal-section">
          <h4>Core Responsibilities</h4>
          <ul style="padding-left:1.25rem; font-size:0.88rem; color:var(--foreground); line-height:1.6;">
            ${respHtml}
          </ul>
        </div>

        <!-- 2. Prerequisites & Skills -->
        <div class="role-modal-section">
          <h4>Prerequisites & Recommended Background</h4>
          <div class="flex flex-wrap gap-2" style="margin-bottom:1.25rem;">
            ${prereqsHtml}
          </div>

          <h4>Core Required Competencies (${(details.core_skills_details || []).length})</h4>
          <div class="flex flex-wrap gap-2" style="margin-bottom:1.25rem;">
            ${coreSkillsHtml}
          </div>

          <h4>Optional & Recommended Skills</h4>
          <div class="flex flex-wrap gap-2">
            ${optionalSkillsHtml}
          </div>
        </div>

        <!-- 3. Example Projects -->
        <div class="role-modal-section">
          <h4>Example Milestone Projects</h4>
          ${projectsHtml}
        </div>

        <!-- 4. Market Insights -->
        <div class="role-modal-section">
          <h4>Market Insights & Provenance</h4>
          ${marketHtml}
        </div>

        <!-- 5. Related Roles -->
        <div class="role-modal-section">
          <h4>Related Roles & Skill Overlap</h4>
          ${relatedHtml}
        </div>

        <!-- Action Footer -->
        <div style="margin-top:2rem; padding-top:1.5rem; border-top:1px solid var(--border); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem;">
          <a href="roadmap.html?role=${encodeURIComponent(roleId)}" class="btn btn-primary">
            Generate 6-week roadmap for ${App.escapeHtml(details.canonical_title)} &rarr;
          </a>
          <button id="modal-compare-this-btn" class="btn btn-outline" data-role-id="${roleId}" type="button">
            Compare this role with another &darr;
          </button>
        </div>
      `;

      // Attach compare handlers inside modal
      content.querySelectorAll(".modal-compare-link").forEach(link => {
        link.addEventListener("click", () => {
          const rA = link.getAttribute("data-role-a");
          const rB = link.getAttribute("data-role-b");
          closeRoleModal();
          const selectA = document.getElementById("compare-select-a");
          const selectB = document.getElementById("compare-select-b");
          if (selectA && selectB) {
            selectA.value = rA;
            selectB.value = rB;
            runRoleComparison(rA, rB);
            document.getElementById("compare-section")?.scrollIntoView({ behavior: "smooth" });
          }
        });
      });

      document.getElementById("modal-compare-this-btn")?.addEventListener("click", () => {
        closeRoleModal();
        const selectA = document.getElementById("compare-select-a");
        if (selectA) {
          selectA.value = roleId;
          document.getElementById("compare-section")?.scrollIntoView({ behavior: "smooth" });
        }
      });

    } catch (err) {
      content.innerHTML = `
        <div class="alert-box error">
          <span>Failed to load details for role: ${App.escapeHtml(err.message)}</span>
        </div>
      `;
    }
  };

  const closeRoleModal = () => {
    const modal = document.getElementById("role-details-modal");
    if (modal) modal.classList.remove("open");
  };

  const setupModalListeners = () => {
    const modal = document.getElementById("role-details-modal");
    const closeBtn = document.getElementById("role-modal-close");

    closeBtn?.addEventListener("click", closeRoleModal);
    modal?.addEventListener("click", (e) => {
      if (e.target === modal) closeRoleModal();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modal?.classList.contains("open")) {
        closeRoleModal();
      }
    });
  };

  /**
   * Populate comparison dropdown selectors
   */
  const populateComparisonDropdowns = (roles) => {
    const selectA = document.getElementById("compare-select-a");
    const selectB = document.getElementById("compare-select-b");
    if (!selectA || !selectB) return;

    const optionsHtml = roles.map(r => `
      <option value="${r.id}">${App.escapeHtml(r.canonical_title || r.title)} (${App.escapeHtml(r.role_family)})</option>
    `).join("");

    selectA.innerHTML = optionsHtml;
    selectB.innerHTML = optionsHtml;

    // Set defaults: backend-engineer vs data-engineer (or second item)
    if (roles.length > 1) {
      selectA.value = roles[0].id;
      selectB.value = roles[1].id;
    }
  };

  /**
   * Setup comparison submit handler
   */
  const setupComparisonForm = () => {
    const runBtn = document.getElementById("compare-run-btn");
    runBtn?.addEventListener("click", () => {
      const roleA = document.getElementById("compare-select-a")?.value;
      const roleB = document.getElementById("compare-select-b")?.value;
      if (roleA && roleB) {
        runRoleComparison(roleA, roleB);
      }
    });
  };

  /**
   * Execute comparison between Role A and Role B
   */
  const runRoleComparison = async (roleA, roleB) => {
    const resultsContainer = document.getElementById("compare-results-container");
    const runBtn = document.getElementById("compare-run-btn");
    if (!resultsContainer) return;

    resultsContainer.classList.remove("hidden");
    if (runBtn) {
      runBtn.disabled = true;
      runBtn.textContent = "Computing overlap…";
    }

    try {
      const data = await API.roles.compare(roleA, roleB);

      const sharedHtml = (data.shared_core_skills || []).map(s => `
        <span class="skill-tag">${App.escapeHtml(s.canonical_name)}</span>
      `).join("") || `<span style="font-size:0.8rem; color:var(--muted-foreground);">No shared core skills</span>`;

      const uniqueAHtml = (data.unique_to_role_a || []).map(s => `
        <span class="skill-tag" style="background:var(--secondary); border-color:var(--border); color:var(--foreground);">
          ${App.escapeHtml(s.canonical_name)}
        </span>
      `).join("") || `<span style="font-size:0.8rem; color:var(--muted-foreground);">None</span>`;

      const uniqueBHtml = (data.unique_to_role_b || []).map(s => `
        <span class="skill-tag missing">
          ${App.escapeHtml(s.canonical_name)}
        </span>
      `).join("") || `<span style="font-size:0.8rem; color:var(--muted-foreground);">None</span>`;

      // Bridge A -> B
      const bridgeAtoB = data.transition_a_to_b || {};
      const bridgeAtoBSkillsHtml = (bridgeAtoB.bridge_skills || []).map(s => `
        <span class="skill-tag missing" title="~${s.estimated_hours}h estimated study">
          ${App.escapeHtml(s.canonical_name)} (${s.estimated_hours}h)
        </span>
      `).join("") || `<span style="font-size:0.8rem; color:#059669;">Seamless transition &bull; Zero missing core skills</span>`;

      // Bridge B -> A
      const bridgeBtoA = data.transition_b_to_a || {};
      const bridgeBtoASkillsHtml = (bridgeBtoA.bridge_skills || []).map(s => `
        <span class="skill-tag missing" title="~${s.estimated_hours}h estimated study">
          ${App.escapeHtml(s.canonical_name)} (${s.estimated_hours}h)
        </span>
      `).join("") || `<span style="font-size:0.8rem; color:#059669;">Seamless transition &bull; Zero missing core skills</span>`;

      resultsContainer.innerHTML = `
        <div style="margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid var(--border);">
          <!-- Comparison Summary Header -->
          <div class="flex items-center justify-between" style="margin-bottom: 1rem; flex-wrap:wrap; gap:1rem;">
            <div>
              <span class="eyebrow-pill">Jaccard Skill Overlap</span>
              <h3 style="font-family:var(--font-display); font-size:1.5rem; margin-top:0.25rem;">
                ${App.escapeHtml(data.role_a.canonical_title)} vs. ${App.escapeHtml(data.role_b.canonical_title)}
              </h3>
            </div>
            <div style="text-align:right;">
              <span style="font-family:var(--font-mono); font-size:2rem; font-weight:700;">
                ${data.overlap_percentage}%
              </span>
              <div style="font-size:0.75rem; color:var(--muted-foreground);">
                ${data.shared_core_count} shared of ${data.total_unique_core_count} unique core skills
              </div>
            </div>
          </div>

          <!-- Overlap Gauge -->
          <div class="progress-track thick" style="margin-bottom: 1.75rem;">
            <div class="progress-fill" style="width: ${data.overlap_percentage}%;"></div>
          </div>

          <!-- 3-Column Skill Breakdown -->
          <div class="grid" style="grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
            <!-- Shared -->
            <div class="card-sm card-dashed">
              <h5 style="font-size:0.8rem; font-weight:600; text-transform:uppercase; margin-bottom:0.75rem; color:#059669;">
                Shared Core Skills (${data.shared_core_count})
              </h5>
              <div class="flex flex-wrap gap-2">
                ${sharedHtml}
              </div>
            </div>

            <!-- Unique to A -->
            <div class="card-sm card-dashed">
              <h5 style="font-size:0.8rem; font-weight:600; text-transform:uppercase; margin-bottom:0.75rem; color:var(--foreground);">
                Unique to ${App.escapeHtml(data.role_a.canonical_title)} (${(data.unique_to_role_a || []).length})
              </h5>
              <div class="flex flex-wrap gap-2">
                ${uniqueAHtml}
              </div>
            </div>

            <!-- Unique to B -->
            <div class="card-sm card-dashed">
              <h5 style="font-size:0.8rem; font-weight:600; text-transform:uppercase; margin-bottom:0.75rem; color:oklch(0.45 0.12 60);">
                Unique to ${App.escapeHtml(data.role_b.canonical_title)} (${(data.unique_to_role_b || []).length})
              </h5>
              <div class="flex flex-wrap gap-2">
                ${uniqueBHtml}
              </div>
            </div>
          </div>

          <!-- Bidirectional Transition Analysis -->
          <h4 style="font-family:var(--font-display); font-size:1.25rem; margin-bottom:1rem;">
            Transition Roadmaps & Bridge Skills
          </h4>

          <div class="compare-grid">
            <!-- A to B Bridge -->
            <div class="bridge-box">
              <div class="flex items-center justify-between" style="margin-bottom:0.75rem;">
                <span style="font-family:var(--font-mono); font-size:0.75rem; text-transform:uppercase; font-weight:600; color:var(--muted-foreground);">
                  Path: ${App.escapeHtml(data.role_a.canonical_title)} &rarr; ${App.escapeHtml(data.role_b.canonical_title)}
                </span>
                <span class="eyebrow-pill">~${bridgeAtoB.estimated_hours}h effort</span>
              </div>
              <p style="font-size:0.85rem; color:var(--foreground); margin-bottom:1rem;">
                To transition to <strong>${App.escapeHtml(data.role_b.canonical_title)}</strong>, focus on closing these ${bridgeAtoB.bridge_skills_count} core gap skills:
              </p>
              <div class="flex flex-wrap gap-2" style="margin-bottom:1.25rem;">
                ${bridgeAtoBSkillsHtml}
              </div>
              <a href="roadmap.html?role=${encodeURIComponent(data.role_b.id)}" class="btn btn-outline btn-sm">
                Generate 6-week curriculum for ${App.escapeHtml(data.role_b.canonical_title)} &rarr;
              </a>
            </div>

            <!-- B to A Bridge -->
            <div class="bridge-box">
              <div class="flex items-center justify-between" style="margin-bottom:0.75rem;">
                <span style="font-family:var(--font-mono); font-size:0.75rem; text-transform:uppercase; font-weight:600; color:var(--muted-foreground);">
                  Path: ${App.escapeHtml(data.role_b.canonical_title)} &rarr; ${App.escapeHtml(data.role_a.canonical_title)}
                </span>
                <span class="eyebrow-pill">~${bridgeBtoA.estimated_hours}h effort</span>
              </div>
              <p style="font-size:0.85rem; color:var(--foreground); margin-bottom:1rem;">
                To transition to <strong>${App.escapeHtml(data.role_a.canonical_title)}</strong>, focus on closing these ${bridgeBtoA.bridge_skills_count} core gap skills:
              </p>
              <div class="flex flex-wrap gap-2" style="margin-bottom:1.25rem;">
                ${bridgeBtoASkillsHtml}
              </div>
              <a href="roadmap.html?role=${encodeURIComponent(data.role_a.id)}" class="btn btn-outline btn-sm">
                Generate 6-week curriculum for ${App.escapeHtml(data.role_a.canonical_title)} &rarr;
              </a>
            </div>
          </div>
        </div>
      `;

    } catch (err) {
      resultsContainer.innerHTML = `
        <div class="alert-box error" style="margin-top:1.5rem;">
          <span>Failed to compare roles: ${App.escapeHtml(err.message)}</span>
        </div>
      `;
    } finally {
      if (runBtn) {
        runBtn.disabled = false;
        runBtn.textContent = "Calculate skill overlap →";
      }
    }
  };

  return {
    init,
    openRoleDetails,
    runRoleComparison
  };
})();

document.addEventListener("DOMContentLoaded", RolesView.init);

