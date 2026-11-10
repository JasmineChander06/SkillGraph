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
      const saved = await API.profiles.getSaved();
      const ghInput = document.getElementById("input-github-user");
      const lcInput = document.getElementById("input-leetcode-user");
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
          recList.innerHTML = lc.interview_recommendations.map(r => `
            <li class="flex items-start gap-2 p-2 rounded-lg bg-secondary/50">
              <span class="text-amber-600 font-bold font-mono text-sm shrink-0">→</span>
              <span class="text-foreground leading-relaxed">${App.escapeHtml(r)}</span>
            </li>
          `).join("");
        }
      }
    }

    container.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return { init };
})();

document.addEventListener("DOMContentLoaded", CodingProfilesView.init);

