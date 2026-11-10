/**
 * SkillGraph Market Analytics Controller
 */

const AnalyticsView = (() => {
  let activeFamily = "";

  const init = async () => {
    setupFilterButtons();
    await loadMarketData();
  };

  const setupFilterButtons = () => {
    const container = document.getElementById("family-filter-container");
    if (!container) return;

    container.addEventListener("click", async (e) => {
      const btn = e.target.closest(".filter-btn");
      if (!btn) return;

      container.querySelectorAll(".filter-btn").forEach(b => {
        b.classList.remove("pill-primary", "active");
        b.classList.add("pill-secondary");
      });

      btn.classList.remove("pill-secondary");
      btn.classList.add("pill-primary", "active");

      activeFamily = btn.getAttribute("data-family") || "";
      await loadMarketData();
    });
  };

  const loadMarketData = async () => {
    try {
      const data = await API.jobs.getMarketTrends(activeFamily);
      renderMarketData(data);
    } catch (err) {
      App.showToast(err.message || "Failed to load market trends.", "error");
    }
  };

  const renderMarketData = (data) => {
    // 1. Roles analyzed count
    const countEl = document.getElementById("roles-analyzed-count");
    if (countEl) countEl.textContent = `${data.total_roles_analyzed} Roles Analyzed`;

    // 2. KPIs
    const mb = data.maturity_breakdown || {};
    const estEl = document.getElementById("stat-est-roles");
    const emgEl = document.getElementById("stat-emg-roles");
    const topToolEl = document.getElementById("stat-top-tool");

    if (estEl) estEl.textContent = mb.established_roles ?? 0;
    if (emgEl) emgEl.textContent = mb.emerging_roles ?? 0;

    const topSkills = data.top_in_demand_skills || [];
    if (topToolEl && topSkills.length > 0) {
      topToolEl.textContent = topSkills[0].skill;
    }

    // 3. Top Demand Bars
    const barsContainer = document.getElementById("skills-demand-bars");
    if (barsContainer) {
      barsContainer.innerHTML = topSkills.slice(0, 10).map((s, idx) => `
        <div class="space-y-1">
          <div class="flex justify-between text-xs font-medium">
            <span class="flex items-center gap-2">
              <span class="font-mono text-[10px] text-muted-foreground w-4">${idx + 1}.</span>
              <span class="text-foreground">${App.escapeHtml(s.skill)}</span>
            </span>
            <span class="font-mono text-muted-foreground">${s.demand_index}% demand</span>
          </div>
          <div class="h-2 w-full bg-secondary rounded-full overflow-hidden">
            <div class="h-full bg-foreground rounded-full transition-all duration-700" style="width: ${s.demand_index}%"></div>
          </div>
        </div>
      `).join("");
    }

    // 4. Skill Pairs
    const pairsContainer = document.getElementById("skill-pairs-container");
    if (pairsContainer) {
      const pairs = data.skill_pairs || [];
      pairsContainer.innerHTML = pairs.map(p => `
        <div class="p-3.5 rounded-xl border border-border bg-card space-y-1.5">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-1.5 font-mono text-xs font-semibold text-ink">
              <span class="pill pill-primary text-[10px] px-2 py-0.5">${App.escapeHtml(p.pair[0])}</span>
              <span class="text-muted-foreground">+</span>
              <span class="pill pill-secondary text-[10px] px-2 py-0.5">${App.escapeHtml(p.pair[1])}</span>
            </div>
            <span class="text-xs font-mono text-muted-foreground">${p.overlap_pct}% co-occur</span>
          </div>
          <p class="text-[11px] text-muted-foreground">${App.escapeHtml(p.relevance)}</p>
        </div>
      `).join("");
    }

    // 5. Empirical Benchmarks
    const benchmarksGrid = document.getElementById("empirical-benchmarks-grid");
    if (benchmarksGrid) {
      const benchmarks = data.empirical_benchmarks || [];
      benchmarksGrid.innerHTML = benchmarks.map(b => {
        const prov = b.provenance || {};
        const skills = b.top_demanded_skills || [];
        return `
          <div class="p-5 rounded-2xl border border-border bg-secondary/30 space-y-3">
            <div class="flex items-center justify-between border-b border-border pb-2">
              <h4 class="font-display font-semibold text-base">${App.escapeHtml(b.role_title)}</h4>
              <span class="pill pill-secondary text-[10px] font-mono">n=${b.sample_size}</span>
            </div>
            <p class="text-[11px] text-muted-foreground font-mono">
              Source: ${App.escapeHtml(prov.source || "Curated")} (${App.escapeHtml(prov.collection_date || "2026")})
            </p>
            <div class="space-y-1 pt-1">
              <div class="text-[10px] uppercase font-mono text-muted-foreground">Verified In-Demand Skills</div>
              <div class="flex flex-wrap gap-1">
                ${skills.map(s => `
                  <span class="pill pill-outline text-[10px] px-2 py-0.5">
                    ${App.escapeHtml(s.name)} ${s.frequency_percent ? `(${s.frequency_percent}%)` : ""}
                  </span>
                `).join("")}
              </div>
            </div>
          </div>
        `;
      }).join("");
    }
  };

  return { init };
})();

document.addEventListener("DOMContentLoaded", AnalyticsView.init);

