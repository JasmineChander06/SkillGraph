/**
 * SkillGraph Global Shell & Application Bootstrap
 * Edition: "Paper & Ink"
 */

const App = (() => {
  // DOM Elements cache
  let mobileDrawer = null;
  let authModal = null;

  const init = async () => {
    setupNavigation();
    setupMobileMenu();
    setupAuthModal();
    setupAuthUI();
    setupAuthListeners();
    updateCopyright();
  };

  /**
   * Set active navigation link based on current path
   */
  const setupNavigation = () => {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll(".nav-pill, .mobile-nav-link");

    navLinks.forEach(link => {
      const href = link.getAttribute("href");
      if (!href) return;

      const isCurrent = (
        (href === "index.html" && (currentPath.endsWith("index.html") || currentPath.endsWith("/"))) ||
        (href === "dashboard.html" && currentPath.endsWith("dashboard.html")) ||
        (href === "resume-review.html" && currentPath.endsWith("resume-review.html")) ||
        (href === "roles.html" && currentPath.endsWith("roles.html")) ||
        (href === "coding.html" && currentPath.endsWith("coding.html")) ||
        (href === "roadmap.html" && currentPath.endsWith("roadmap.html"))
      );

      if (isCurrent) {
        link.classList.add("active");
      } else {
        link.classList.remove("active");
      }

      // Phase 3: Redirect unauthenticated visitors to auth.html with target parameter
      if (href !== "index.html" && !API.auth.isAuthenticated()) {
        link.addEventListener("click", (e) => {
          e.preventDefault();
          window.location.href = `auth.html?redirect=${encodeURIComponent(href)}`;
        });
      }
    });
  };

  /**
   * Toggle mobile navigation drawer
   */
  const setupMobileMenu = () => {
    const toggleBtn = document.getElementById("mobile-menu-toggle");
    mobileDrawer = document.getElementById("mobile-nav-drawer");

    if (toggleBtn && mobileDrawer) {
      toggleBtn.addEventListener("click", () => {
        const isOpen = mobileDrawer.classList.toggle("open");
        toggleBtn.setAttribute("aria-expanded", isOpen);
      });
    }
  };

  /**
   * Listen for custom auth events across modules
   */
  const setupAuthListeners = () => {
    window.addEventListener("sg:auth-expired", (e) => {
      setupAuthUI();
      showToast(e.detail?.message || "Session expired. Please sign in again.", "error");
      window.location.href = `auth.html?redirect=${encodeURIComponent(window.location.pathname.split("/").pop() || "dashboard.html")}`;
    });

    window.addEventListener("sg:auth-changed", () => {
      setupAuthUI();
      if (typeof window.refreshDashboard === "function") window.refreshDashboard();
      if (typeof window.refreshRoadmap === "function") window.refreshRoadmap();
    });
  };

  /**
   * Update header action buttons based on login state
   */
  const setupAuthUI = () => {
    const headerActions = document.getElementById("header-actions");
    if (!headerActions) return;

    const isAuth = API.auth.isAuthenticated();
    const user = API.auth.getUser();

    if (isAuth && user) {
      const displayName = user.full_name || user.name || user.email.split("@")[0];
      headerActions.innerHTML = `
        <a href="dashboard.html" class="eyebrow-pill" style="text-transform:none; font-family:var(--font-sans); text-decoration:none;" title="View Profile on Dashboard">
          ${escapeHtml(displayName)}
        </a>
        <button id="auth-signout-btn" class="btn btn-outline btn-sm" type="button">
          Sign Out
        </button>
      `;

      document.getElementById("auth-signout-btn")?.addEventListener("click", () => {
        API.auth.logout();
        showToast("Signed out successfully.", "info");
        window.location.href = "index.html";
      });
    } else {
      headerActions.innerHTML = `
        <a href="auth.html?mode=signin" class="btn btn-outline btn-sm">
          Sign In
        </a>
        <a href="auth.html?mode=signup" class="btn btn-primary btn-sm">
          Create Account
        </a>
      `;
    }
  };

  /**
   * Build and manage the Auth Modal Dialog
   */
  const setupAuthModal = () => {
    authModal = document.getElementById("auth-modal");
    if (!authModal) {
      const modalEl = document.createElement("div");
      modalEl.id = "auth-modal";
      modalEl.className = "modal-backdrop";
      modalEl.setAttribute("role", "dialog");
      modalEl.setAttribute("aria-modal", "true");
      modalEl.innerHTML = `
        <div class="modal-card">
          <div class="modal-header">
            <div class="segmented-pill">
              <button id="modal-tab-signin" class="segmented-pill-btn active" type="button">Sign in</button>
              <button id="modal-tab-signup" class="segmented-pill-btn" type="button">Create account</button>
            </div>
            <button id="modal-close" class="modal-close-btn" type="button" aria-label="Close dialog">&times;</button>
          </div>

          <div id="modal-alert-container"></div>

          <form id="modal-auth-form" novalidate>
            <div id="field-name-group" class="form-group hidden">
              <label class="form-label" for="modal-name">Full Name</label>
              <input id="modal-name" class="form-input" type="text" placeholder="Ada Lovelace" autocomplete="name" />
            </div>

            <div class="form-group">
              <label class="form-label" for="modal-email">Email Address</label>
              <input id="modal-email" class="form-input" type="email" placeholder="you@work.com" required autocomplete="email" />
            </div>

            <div class="form-group">
              <label class="form-label" for="modal-password">Password</label>
              <input id="modal-password" class="form-input" type="password" placeholder="•••••••• (min 8 characters)" required autocomplete="current-password" />
            </div>

            <button id="modal-submit-btn" class="btn btn-primary btn-lg" type="submit" style="width:100%; margin-top:1rem;">
              Sign in
            </button>
          </form>

          <p style="font-size:0.75rem; color:var(--muted-foreground); text-align:center; margin-top:1.25rem;">
            JWT authenticated &bull; Salted PBKDF2 password hashing &bull; Zero plaintext retention
          </p>
        </div>
      `;
      document.body.appendChild(modalEl);
      authModal = modalEl;
    }

    // Modal listeners
    document.getElementById("modal-close")?.addEventListener("click", closeAuthModal);
    authModal.addEventListener("click", (e) => {
      if (e.target === authModal) closeAuthModal();
    });

    // ESC key closes modal
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && authModal.classList.contains("open")) {
        closeAuthModal();
      }
    });

    const tabSignIn = document.getElementById("modal-tab-signin");
    const tabSignUp = document.getElementById("modal-tab-signup");
    const nameGroup = document.getElementById("field-name-group");
    const submitBtn = document.getElementById("modal-submit-btn");

    tabSignIn?.addEventListener("click", () => {
      tabSignIn.classList.add("active");
      tabSignUp.classList.remove("active");
      nameGroup.classList.add("hidden");
      submitBtn.textContent = "Sign in";
      clearModalAlert();
    });

    tabSignUp?.addEventListener("click", () => {
      tabSignUp.classList.add("active");
      tabSignIn.classList.remove("active");
      nameGroup.classList.remove("hidden");
      submitBtn.textContent = "Create account";
      clearModalAlert();
    });

    // Form submission with client-side validation
    const authForm = document.getElementById("modal-auth-form");
    authForm?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const isSignUp = tabSignUp.classList.contains("active");
      const email = document.getElementById("modal-email").value.trim();
      const password = document.getElementById("modal-password").value;
      const name = document.getElementById("modal-name")?.value.trim();

      // Client validation
      const emailRegex = /^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$/;
      if (!email || !emailRegex.test(email)) {
        showModalAlert("Please enter a valid email address.", "error");
        return;
      }

      if (!password || password.length < 8) {
        showModalAlert("Password must be at least 8 characters long.", "error");
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = "Authenticating…";
      clearModalAlert();

      try {
        let resp;
        if (isSignUp) {
          resp = await API.auth.register({ email, password, full_name: name || undefined });
        } else {
          resp = await API.auth.login({ email, password });
        }

        // Store only the JWT access token and public user metadata
        // Note: Password is NEVER stored in localStorage
        const token = resp.access_token || resp.token;
        if (token) {
          localStorage.setItem(CONFIG.STORAGE_KEYS.TOKEN, token);
        }
        if (resp.user) {
          localStorage.setItem(CONFIG.STORAGE_KEYS.USER, JSON.stringify(resp.user));
        }

        closeAuthModal();
        setupAuthUI();
        showToast(isSignUp ? "Account created successfully." : "Signed in successfully.", "success");

        // Trigger auth changed event
        window.dispatchEvent(new CustomEvent("sg:auth-changed"));

      } catch (err) {
        showModalAlert(err.message || "Authentication failed. Please check your credentials.", "error");
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = isSignUp ? "Create account" : "Sign in";
      }
    });
  };

  const openAuthModal = (mode = "signin") => {
    if (!authModal) setupAuthModal();
    clearModalAlert();

    const tabSignIn = document.getElementById("modal-tab-signin");
    const tabSignUp = document.getElementById("modal-tab-signup");
    const nameGroup = document.getElementById("field-name-group");
    const submitBtn = document.getElementById("modal-submit-btn");

    if (mode === "signup") {
      tabSignUp?.classList.add("active");
      tabSignIn?.classList.remove("active");
      nameGroup?.classList.remove("hidden");
      if (submitBtn) submitBtn.textContent = "Create account";
    } else {
      tabSignIn?.classList.add("active");
      tabSignUp?.classList.remove("active");
      nameGroup?.classList.add("hidden");
      if (submitBtn) submitBtn.textContent = "Sign in";
    }

    authModal.classList.add("open");
    document.getElementById("modal-email")?.focus();
  };

  const closeAuthModal = () => {
    if (authModal) {
      authModal.classList.remove("open");
    }
  };

  const showModalAlert = (msg, type = "error") => {
    const container = document.getElementById("modal-alert-container");
    if (!container) return;
    container.innerHTML = `
      <div class="alert-box ${type}" role="alert">
        <span>${escapeHtml(msg)}</span>
      </div>
    `;
  };

  const clearModalAlert = () => {
    const container = document.getElementById("modal-alert-container");
    if (container) container.innerHTML = "";
  };

  /**
   * Health check utility
   */
  const checkBackendConnectivity = async () => {
    try {
      return await API.health.check();
    } catch (err) {
      console.warn("Backend connectivity check:", err.message);
      return null;
    }
  };

  const updateCopyright = () => {
    const yearEl = document.getElementById("footer-year");
    if (yearEl) {
      yearEl.textContent = new Date().getFullYear();
    }
  };

  const showToast = (message, type = "info") => {
    let toast = document.getElementById("app-toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "app-toast";
      toast.style.cssText = `
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        z-index: 200;
        padding: 0.85rem 1.5rem;
        border-radius: var(--radius-full);
        font-size: 0.875rem;
        font-weight: 500;
        box-shadow: var(--shadow-float);
        transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.3s ease;
        transform: translateY(20px);
        opacity: 0;
        pointer-events: none;
      `;
      document.body.appendChild(toast);
    }

    if (type === "success") {
      toast.style.backgroundColor = "var(--foreground)";
      toast.style.color = "var(--background)";
      toast.style.border = "none";
    } else if (type === "error") {
      toast.style.backgroundColor = "#991B1B";
      toast.style.color = "#FFFFFF";
      toast.style.border = "none";
    } else {
      toast.style.backgroundColor = "var(--card)";
      toast.style.color = "var(--foreground)";
      toast.style.border = "1px solid var(--border)";
    }

    toast.textContent = message;
    toast.style.transform = "translateY(0)";
    toast.style.opacity = "1";

    setTimeout(() => {
      toast.style.transform = "translateY(20px)";
      toast.style.opacity = "0";
    }, 3500);
  };

  const escapeHtml = (str) => {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  };

  return {
    init,
    openAuthModal,
    closeAuthModal,
    showToast,
    escapeHtml
  };
})();

// Auto-initialize on DOM ready
document.addEventListener("DOMContentLoaded", App.init);
