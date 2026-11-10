/**
 * SkillGraph Roadmap Controller
 * 6-Week Vertical Timeline & Progress Checklist Tracker
 */

const RoadmapView = (() => {
  let activeRoadmap = null;

  const init = async () => {
    // Phase 3 Auth Guard
    if (!API.auth.requireAuth()) return;

    await populateRoleDropdown();
    setupGenerateForm();
    await loadInitialRoadmap();
  };

  /**
   * Populate the role selector from the backend roles catalog
   */
  const populateRoleDropdown = async () => {
    const selectEl = document.getElementById("roadmap-role-select");
    if (!selectEl) return;

    let roles = [];
    try {
      const res = await API.roles.list();
      roles = (Array.isArray(res) && res.length > 0) ? res : CONFIG.DEFAULT_ROLES;
    } catch {
      roles = CONFIG.DEFAULT_ROLES;
    }

    const user = API.auth.getUser() || {};
    const urlParams = new URLSearchParams(window.location.search);
    const preselectedRole = urlParams.get("role") || user.target_role || "backend-engineer";

    selectEl.innerHTML = roles.map(role => {
      const id = role.id;
      const title = role.canonical_title || role.title;
      const isSelected = (id === preselectedRole) ? "selected" : "";
      return `<option value="${App.escapeHtml(id)}" ${isSelected}>${App.escapeHtml(title)}</option>`;
    }).join("");
  };

  /**
   * Setup roadmap generation form submission
   */
  const setupGenerateForm = () => {
    const form = document.getElementById("roadmap-gen-form");
    const generateBtn = document.getElementById("roadmap-generate-btn");

    form?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const roleId = document.getElementById("roadmap-role-select").value;
      const weeklyHours = parseInt(document.getElementById("roadmap-hours-input")?.value || "10", 10);

      if (generateBtn) {
        generateBtn.disabled = true;
        generateBtn.textContent = "Generating 6-week plan…";
      }

      try {
        const roadmapData = await API.roadmaps.generate({
          role_id: roleId,
          weekly_hours: weeklyHours
        });

        activeRoadmap = roadmapData;
        renderRoadmap(roadmapData);
        App.showToast("Personalized 6-week roadmap generated.", "success");
      } catch (err) {
        App.showToast(err.message || "Failed to generate roadmap.", "error");
      } finally {
        if (generateBtn) {
          generateBtn.disabled = false;
          generateBtn.textContent = "Generate roadmap";
        }
      }
    });
  };

  /**
   * Load either the user's latest saved roadmap or generate one for the active role
   */
  const loadInitialRoadmap = async () => {
    const timelineContainer = document.getElementById("roadmap-timeline-container");
    if (!timelineContainer) return;

    const user = API.auth.getUser() || {};
    const urlParams = new URLSearchParams(window.location.search);
    const targetRole = urlParams.get("role") || user.target_role || "backend-engineer";

    // 1. If authenticated, check if user has existing roadmaps
    if (API.auth.isAuthenticated()) {
      try {
        const savedRoadmaps = await API.roadmaps.list();
        if (savedRoadmaps && savedRoadmaps.length > 0) {
          // Find matching role or use most recent
          const match = savedRoadmaps.find(r => r.role_id === targetRole) || savedRoadmaps[0];
          const fullRoadmap = await API.roadmaps.get(match.id);
          activeRoadmap = fullRoadmap;
          renderRoadmap(fullRoadmap);
          return;
        }
      } catch (err) {
        console.warn("Could not load saved roadmap:", err);
      }
    }

    // 2. Otherwise generate a roadmap for the selected role
    try {
      const generated = await API.roadmaps.generate({
        role_id: targetRole,
        weekly_hours: 10
      });
      activeRoadmap = generated;
      renderRoadmap(generated);
    } catch (err) {
      timelineContainer.innerHTML = `
        <div class="alert-box info">
          <span>Click <strong>Generate roadmap</strong> to build a customized 6-week study path.</span>
        </div>
      `;
    }
  };

  /**
   * Render the complete 6-week vertical timeline and progress bar
   */
  const renderRoadmap = (roadmap) => {
    updateSummaryStats(roadmap);

    const timelineContainer = document.getElementById("roadmap-timeline-container");
    if (!timelineContainer) return;

    const weeks = roadmap.weeks || [];
    const allTasks = roadmap.tasks || [];

    if (weeks.length === 0 && allTasks.length > 0) {
      // Group tasks by week if flat tasks provided
      for (let w = 1; w <= 6; w++) {
        const weekTasks = allTasks.filter(t => t.week === w);
        weeks.push({
          week_number: w,
          theme: `Week ${w} Milestone`,
          weekly_hours_allocated: weekTasks.reduce((sum, t) => sum + (t.estimated_effort || 0), 0),
          tasks: weekTasks
        });
      }
    }

    const weeksHtml = weeks.map(week => {
      const weekNum = week.week_number;
      const weekTasks = week.tasks || [];
      const allDone = weekTasks.length > 0 && weekTasks.every(t => t.completion_status === "completed");

      return `
        <div class="week-block">
          <div class="week-badge ${allDone ? 'completed' : ''}" aria-label="Week ${weekNum}">
            W${weekNum}
          </div>

          <div class="week-header">
            <div>
              <h3 class="week-title">${App.escapeHtml(week.theme || `Week ${weekNum}`)}</h3>
              <span class="week-theme">${weekTasks.length} study tasks planned</span>
            </div>
            <span class="week-hours-badge">~${week.weekly_hours_allocated || 8} hrs</span>
          </div>

          <div class="tasks-list">
            ${weekTasks.map(task => {
              const isCompleted = task.completion_status === "completed";
              const taskId = task.id;
              const res = task.learning_resource || {};
              const resUrl = res.url || "#";
              const resTitle = res.title || "Curated Learning Resource";

              return `
                <div class="task-item ${isCompleted ? 'completed' : ''}" id="task-card-${taskId}">
                  <div class="task-checkbox-wrapper">
                    <input
                      type="checkbox"
                      class="task-checkbox"
                      id="checkbox-${taskId}"
                      data-task-id="${taskId}"
                      ${isCompleted ? 'checked' : ''}
                      aria-label="Mark task ${App.escapeHtml(task.title)} as complete"
                    />
                  </div>

                  <div class="task-body">
                    <div class="flex items-center justify-between">
                      <label for="checkbox-${taskId}" class="task-title" style="cursor:pointer;">
                        ${App.escapeHtml(task.title)}
                      </label>
                      <span id="save-status-${taskId}" class="save-status-indicator"></span>
                    </div>

                    <p class="task-desc">${App.escapeHtml(task.description)}</p>

                    <div class="task-meta">
                      <span class="task-skill-tag">
                        Target: ${App.escapeHtml(task.target_skill)}
                      </span>
                      <span style="color:var(--muted-foreground);">
                        Effort: ${task.estimated_effort}h
                      </span>
                      ${res.url ? `
                        <a href="${App.escapeHtml(resUrl)}" target="_blank" rel="noopener noreferrer" class="task-resource-link">
                          Resource: ${App.escapeHtml(resTitle)} &nearr;
                        </a>
                      ` : `
                        <span style="color:var(--muted-foreground);">${App.escapeHtml(resTitle)}</span>
                      `}
                    </div>
                  </div>
                </div>
              `;
            }).join("")}
          </div>
        </div>
      `;
    }).join("");

    const capstoneHtml = roadmap.capstone_project ? `
      <div class="card card-dark" style="margin-top:2.5rem; padding:2rem 2.25rem;">
        <span class="eyebrow-pill" style="background:rgba(251,249,245,0.15); border-color:rgba(251,249,245,0.25); color:var(--background); margin-bottom:0.75rem;">
          Capstone Milestone
        </span>
        <h4 style="font-family:var(--font-display); font-size:1.45rem; color:var(--background); margin-bottom:0.5rem;">
          Final Synthesis Project
        </h4>
        <p style="color:rgba(251,249,245,0.85); font-size:0.95rem; line-height:1.55;">
          ${App.escapeHtml(roadmap.capstone_project)}
        </p>
      </div>
    ` : "";

    timelineContainer.innerHTML = `
      <div class="timeline-container">
        <div class="timeline-rail" aria-hidden="true"></div>
        ${weeksHtml}
      </div>
      ${capstoneHtml}
    `;

    attachTaskListeners();
  };

  /**
   * Update Progress Summary Bar and Readout
   */
  const updateSummaryStats = (roadmap) => {
    const tasks = roadmap.tasks || [];
    const total = tasks.length;
    const completed = tasks.filter(t => t.completion_status === "completed").length;
    const pct = total > 0 ? Math.round((completed / total) * 100) : 0;

    const summaryCard = document.getElementById("roadmap-summary-card");
    if (!summaryCard) return;

    summaryCard.classList.remove("hidden");
    const pctEl = document.getElementById("summary-pct-value");
    const countEl = document.getElementById("summary-task-count");
    const fillEl = document.getElementById("summary-progress-fill");
    const titleEl = document.getElementById("summary-role-title");

    if (pctEl) pctEl.textContent = `${pct}%`;
    if (countEl) countEl.textContent = `${completed} of ${total} tasks complete`;
    if (fillEl) fillEl.style.width = `${pct}%`;
    if (titleEl) titleEl.textContent = roadmap.role_title || "Target Role";
  };

  /**
   * Attach change listeners to task checkboxes for instant state persistence
   */
  const attachTaskListeners = () => {
    const checkboxes = document.querySelectorAll(".task-checkbox");
    checkboxes.forEach(cb => {
      cb.addEventListener("change", async (e) => {
        const taskId = e.target.getAttribute("data-task-id");
        const isChecked = e.target.checked;
        const newStatus = isChecked ? "completed" : "pending";
        const taskCard = document.getElementById(`task-card-${taskId}`);
        const statusEl = document.getElementById(`save-status-${taskId}`);

        if (statusEl) statusEl.textContent = "Saving…";

        // Optimistic UI update
        if (taskCard) {
          if (isChecked) taskCard.classList.add("completed");
          else taskCard.classList.remove("completed");
        }

        // Update local object state
        if (activeRoadmap && activeRoadmap.tasks) {
          const taskObj = activeRoadmap.tasks.find(t => String(t.id) === String(taskId));
          if (taskObj) taskObj.completion_status = newStatus;
          updateSummaryStats(activeRoadmap);
        }

        try {
          const roadmapId = activeRoadmap ? activeRoadmap.id : null;
          await API.roadmaps.updateTask(roadmapId, taskId, newStatus);
          if (statusEl) {
            statusEl.textContent = "Saved";
            setTimeout(() => { if (statusEl) statusEl.textContent = ""; }, 1800);
          }
        } catch (err) {
          console.warn("Progress update note:", err.message);
          if (statusEl) statusEl.textContent = "";
        }
      });
    });
  };

  return {
    init
  };
})();

window.refreshRoadmap = RoadmapView.init;
document.addEventListener("DOMContentLoaded", RoadmapView.init);

