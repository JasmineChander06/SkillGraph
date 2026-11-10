/**
 * SkillGraph Coding Profiles Controller (GitHub + LeetCode)
 */

const CodingProfilesView = (() => {
  const init = async () => {
    // Phase 3 Auth Guard
    if (!API.auth.requireAuth()) return;

    setupAnalyzeButton();
    await loadSavedHandles();
  };

  const loadSavedHandles = async () => {
    try {
      const ghInput = document.getElementById("input-github-user");
      const lcInput = document.getElementById("input-leetcode-user");

      // 1. Try to load cached analysis report first
      try {
        const myAnalysis = await API.profiles.getMe();
        if (myAnalysis) {
          if (myAnalysis.github_username && ghInput) ghInput.value = myAnalysis.github_username;
          if (myAnalysis.leetcode_username && lcInput) lcInput.value = myAnalysis.leetcode_username;
          if (myAnalysis.combined_signal_score !== undefined) {
            renderProfilesResults(myAnalysis);
            return;
          }
        }
      } catch {
        // Fall back to saved handles
      }

      // 2. Fall back to saved handles and trigger analysis
      const saved = await API.profiles.getSaved();
      if (saved.github_username && ghInput) ghInput.value = saved.github_username;
      if (saved.leetcode_username && lcInput) lcInput.value = saved.leetcode_username;
      if (saved.github_username || saved.leetcode_username) {
        document.getElementById("btn-analyze-profiles")?.click();
      }
    } catch {
      // Ignore if no saved handles yet
    }
  };

  const setupAnalyzeButton = () => {
    const btn = document.getElementById("btn-analyze-profiles");
    const ghInput = document.getElementById("input-github-user");
    const lcInput = document.getElementById("input-leetcode-user");

    btn?.addEventListener("click", async () => {
      const ghUser = ghInput?.value.trim() || "";
      const lcUser = lcInput?.value.trim() || "";

      if (!ghUser && !lcUser) {
        App.showToast("Please enter at least a GitHub or LeetCode username.", "error");
        return;
      }

      btn.disabled = true;
      btn.textContent = "Querying live profile signals…";

      try {
        const data = await API.profiles.analyze({
          github_username: ghUser,
          leetcode_username: lcUser
        });

        renderProfilesResults(data);
        App.showToast("Profiles analyzed and technical signal computed.", "success");
      } catch (err) {
        App.showToast(err.message || "Failed to analyze coding profiles.", "error");
      } finally {
        btn.disabled = false;
        btn.textContent = "Analyze Profiles & Score Signal";
      }
    });
  };

  const renderProfilesResults = (data) => {
    const container = document.getElementById("profiles-results-container");
    if (!container) return;

    container.classList.remove("hidden");

    // 1. Combined Score & Summary
    const scoreNum = document.getElementById("combined-score-num");
    const summaryText = document.getElementById("profiles-summary-text");
    if (scoreNum) scoreNum.textContent = data.combined_signal_score;
    if (summaryText) summaryText.textContent = data.summary;

    // 2. GitHub Card
    const gh = data.github;
    const ghCard = document.getElementById("github-card");
    if (ghCard) {
      if (!gh) {
        ghCard.classList.add("opacity-60");
        document.getElementById("gh-summary-text").textContent = "No GitHub profile analyzed or account not found.";
      } else {
        ghCard.classList.remove("opacity-60");
        document.getElementById("gh-user-title").textContent = gh.name || `@${gh.username}`;
        const link = document.getElementById("gh-profile-link");
        if (link) {
          link.href = gh.profile_url;
          link.textContent = `github.com/${gh.username}`;
        }
        document.getElementById("gh-quality-badge").textContent = `${gh.quality_score} / 100 Signal`;
        document.getElementById("gh-repos-count").textContent = gh.public_repos;
        document.getElementById("gh-stars-count").textContent = gh.total_stars;
        document.getElementById("gh-followers-count").textContent = gh.followers;
        document.getElementById("gh-summary-text").textContent = gh.summary;

        // Languages
        const langContainer = document.getElementById("gh-languages-container");
        if (langContainer) {
          const langs = gh.primary_languages || {};
          const keys = Object.keys(langs);
          if (keys.length === 0) {
            langContainer.innerHTML = `<span class="text-xs text-muted-foreground italic">No public code repos detected.</span>`;
          } else {
            langContainer.innerHTML = keys.map(k => `
              <span class="pill pill-secondary text-xs font-mono">
                ${App.escapeHtml(k)} <strong class="ml-1">${langs[k]}%</strong>
              </span>
            `).join("");
          }
        }
      }
    }

    // 3. LeetCode Card
    const lc = data.leetcode;
    const lcCard = document.getElementById("leetcode-card");
    if (lcCard) {
      if (!lc) {
        lcCard.classList.add("opacity-60");
        document.getElementById("lc-tier-badge").textContent = "Profile Not Linked";
      } else {
        lcCard.classList.remove("opacity-60");
        document.getElementById("lc-user-title").textContent = `@${lc.username}`;
        const lcLink = document.getElementById("lc-profile-link");
        if (lcLink) {
          lcLink.href = lc.profile_url;
          lcLink.textContent = `leetcode.com/${lc.username}`;
        }
        document.getElementById("lc-tier-badge").textContent = lc.dsa_readiness_tier;
        document.getElementById("lc-total-solved").textContent = lc.total_solved;
        document.getElementById("lc-easy-solved").textContent = lc.easy_solved;
        document.getElementById("lc-med-solved").textContent = lc.medium_solved;
        document.getElementById("lc-hard-solved").textContent = lc.hard_solved;

        document.getElementById("lc-dsa-score").textContent = `${lc.dsa_readiness_score} / 100`;
        const dsaBar = document.getElementById("lc-dsa-bar");
        if (dsaBar) dsaBar.style.width = `${lc.dsa_readiness_score}%`;

        // Recommendations
        const recList = document.getElementById("lc-recommendations-list");
        if (recList) {
          recList.innerHTML = (lc.interview_recommendations || []).map(r => `
            <li class="flex items-start gap-2 p-2 rounded-lg bg-secondary/50">
              <span class="text-amber-600 font-bold font-mono text-sm shrink-0">&rarr;</span>
              <span class="text-foreground leading-relaxed">${App.escapeHtml(r)}</span>
            </li>
          `).join("");
        }
      }
    }

    // 4. Multi-Signal Skill Breakdown Card
    const breakdownCard = document.getElementById("skills-breakdown-card");
    const breakdown = data.skills_breakdown;
    if (breakdownCard && breakdown) {
      breakdownCard.classList.remove("hidden");

      const proofsCount = document.getElementById("proofs-count");
      const proofsChips = document.getElementById("coding-verified-chips");
      if (proofsCount) proofsCount.textContent = `${breakdown.coding_verified_skills.length} Verified`;
      if (proofsChips) {
        proofsChips.innerHTML = breakdown.coding_verified_skills.map(s => `
          <span class="pill pill-primary text-[11px] font-mono">${App.escapeHtml(s)} &check;</span>
        `).join("") || `<span class="text-xs text-muted-foreground italic">No skills verified from code yet</span>`;
      }

      const resumeCount = document.getElementById("resume-count");
      const resumeChips = document.getElementById("resume-skills-chips");
      if (resumeCount) resumeCount.textContent = `${breakdown.resume_skills.length} Skills`;
      if (resumeChips) {
        resumeChips.innerHTML = breakdown.resume_skills.map(s => `
          <span class="pill pill-secondary text-[11px] font-mono">${App.escapeHtml(s)}</span>
        `).join("") || `<span class="text-xs text-muted-foreground italic">No resume skills recorded</span>`;
      }

      const needingCount = document.getElementById("needing-count");
      const needingChips = document.getElementById("needing-evidence-chips");
      if (needingCount) needingCount.textContent = `${breakdown.skills_needing_evidence.length} Gaps`;
      if (needingChips) {
        needingChips.innerHTML = breakdown.skills_needing_evidence.map(s => `
          <span class="pill text-[11px] font-mono bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300">
            ${App.escapeHtml(s)}
          </span>
        `).join("") || `<span class="text-xs text-emerald-600 font-mono italic">All target competencies supported!</span>`;
      }
    }

    // 5. Public Repository Projects Grid
    const projectsCard = document.getElementById("projects-evidence-card");
    const projectsGrid = document.getElementById("projects-evidence-grid");
    const projectsBadge = document.getElementById("projects-count-badge");
    const topProjects = (gh && gh.top_projects) ? gh.top_projects : [];

    if (projectsCard && topProjects.length > 0) {
      projectsCard.classList.remove("hidden");
      if (projectsBadge) projectsBadge.textContent = `${topProjects.length} Repositories`;
      if (projectsGrid) {
        projectsGrid.innerHTML = topProjects.map(proj => {
          const demonstrated = proj.demonstrated_skills || [];
          return `
            <div class="p-4 bg-secondary/50 border border-border rounded-2xl flex flex-col justify-between space-y-3">
              <div>
                <div class="flex items-center justify-between gap-2 mb-1.5">
                  <a href="${App.escapeHtml(proj.html_url)}" target="_blank" rel="noopener noreferrer" class="font-display text-base font-semibold text-foreground hover:underline">
                    ${App.escapeHtml(proj.name)} &nearr;
                  </a>
                  <div class="flex items-center gap-1.5 shrink-0">
                    ${proj.language ? `<span class="pill pill-secondary text-[10px] font-mono">${App.escapeHtml(proj.language)}</span>` : ""}
                    <span class="pill pill-secondary text-[10px] font-mono">&star; ${proj.stars || 0}</span>
                  </div>
                </div>
                <p class="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                  ${App.escapeHtml(proj.description || "Public repository with technical implementation proofs.")}
                </p>
              </div>

              <div class="pt-2 border-t border-border/60">
                <span class="text-[10px] font-mono uppercase tracking-wider text-muted-foreground block mb-1">
                  Demonstrated Skills:
                </span>
                <div class="flex flex-wrap gap-1">
                  ${demonstrated.map(s => `
                    <span class="pill pill-primary text-[10px] font-mono">${App.escapeHtml(s)}</span>
                  `).join("") || `<span class="text-[10px] text-muted-foreground italic">General codebase</span>`}
                </div>
              </div>
            </div>
          `;
        }).join("");
      }
    } else if (projectsCard) {
      projectsCard.classList.add("hidden");
    }

    container.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return { init };
})();

document.addEventListener("DOMContentLoaded", CodingProfilesView.init);

