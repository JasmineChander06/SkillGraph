/**
 * SkillGraph Authentication Controller
 * Handles Account Creation, Sign In, and Session Routing
 * Paper & Ink Edition — Pure Vanilla JavaScript
 */

(() => {
  // DOM Elements
  const tabSignIn = document.getElementById("tab-signin");
  const tabSignUp = document.getElementById("tab-signup");
  const form = document.getElementById("auth-form");
  const heading = document.getElementById("auth-heading");
  const subheading = document.getElementById("auth-subheading");
  const nameContainer = document.getElementById("field-name-container");
  const nameInput = document.getElementById("auth-name");
  const emailInput = document.getElementById("auth-email");
  const passwordInput = document.getElementById("auth-password");
  const passwordHint = document.getElementById("password-hint");
  const submitBtn = document.getElementById("auth-submit-btn");
  const alertBox = document.getElementById("auth-alert");

  let currentMode = "signin"; // 'signin' or 'signup'

  // Read URL parameters
  const params = new URLSearchParams(window.location.search);
  const redirectTarget = params.get("redirect") || "dashboard.html";
  const initialMode = params.get("mode") === "signup" ? "signup" : "signin";

  const init = () => {
    // If user is already authenticated with a valid token, redirect to target
    if (API.auth.isAuthenticated()) {
      window.location.href = redirectTarget;
      return;
    }

    setupTabs();
    setupForm();
    setMode(initialMode);
  };

  const setMode = (mode) => {
    currentMode = mode;
    hideAlert();

    if (mode === "signup") {
      tabSignUp.classList.add("active");
      tabSignIn.classList.remove("active");
      heading.textContent = "Create your SkillGraph account";
      subheading.textContent = "Get a personalized career readiness graph, gap analysis, and 6-week roadmap.";
      nameContainer.classList.remove("hidden");
      nameInput.required = true;
      passwordHint.style.display = "inline";
      submitBtn.textContent = "Create account →";
      passwordInput.setAttribute("autocomplete", "new-password");
    } else {
      tabSignIn.classList.add("active");
      tabSignUp.classList.remove("active");
      heading.textContent = "Sign in to SkillGraph";
      subheading.textContent = "Access your personal career readiness graph, saved analyses, and learning roadmaps.";
      nameContainer.classList.add("hidden");
      nameInput.required = false;
      passwordHint.style.display = "none";
      submitBtn.textContent = "Sign in →";
      passwordInput.setAttribute("autocomplete", "current-password");
    }
  };

  const setupTabs = () => {
    tabSignIn?.addEventListener("click", () => setMode("signin"));
    tabSignUp?.addEventListener("click", () => setMode("signup"));
  };

  const showAlert = (message, type = "error") => {
    if (!alertBox) return;
    alertBox.textContent = message;
    alertBox.className = `alert-box ${type}`;
    alertBox.classList.remove("hidden");
  };

  const hideAlert = () => {
    if (!alertBox) return;
    alertBox.classList.add("hidden");
    alertBox.textContent = "";
  };

  const setupForm = () => {
    form?.addEventListener("submit", async (e) => {
      e.preventDefault();
      hideAlert();

      const email = emailInput.value.trim();
      const password = passwordInput.value;
      const name = nameInput.value.trim();

      // Client-side validations
      if (!email) {
        showAlert("Please enter your email address.");
        emailInput.focus();
        return;
      }

      const emailRegex = /^[\w.\-+]+@[\w-]+\.[a-zA-Z]{2,}$/;
      if (!emailRegex.test(email)) {
        showAlert("Please enter a valid email address (e.g. name@domain.com).");
        emailInput.focus();
        return;
      }

      if (!password) {
        showAlert("Please enter your password.");
        passwordInput.focus();
        return;
      }

      if (currentMode === "signup") {
        if (!name) {
          showAlert("Please enter your full name.");
          nameInput.focus();
          return;
        }
        if (password.length < 8) {
          showAlert("Password must be at least 8 characters long.");
          passwordInput.focus();
          return;
        }
      }

      // Submit to backend
      submitBtn.disabled = true;
      submitBtn.textContent = currentMode === "signup" ? "Creating account…" : "Signing in…";

      try {
        let authResponse;
        if (currentMode === "signup") {
          authResponse = await API.auth.register({
            email,
            password,
            full_name: name
          });
        } else {
          authResponse = await API.auth.login({
            email,
            password
          });
        }

        // Store JWT token and user profile in localStorage
        const token = authResponse.access_token || authResponse.token;
        const user = authResponse.user;

        if (!token) {
          throw new Error("Authentication response did not return a valid session token.");
        }

        localStorage.setItem(CONFIG.STORAGE_KEYS.TOKEN, token);
        localStorage.setItem(CONFIG.STORAGE_KEYS.USER, JSON.stringify(user));

        // Dispatch auth-changed event across the app
        window.dispatchEvent(new CustomEvent("sg:auth-changed", { detail: { user } }));

        // First-time user onboarding check
        if (currentMode === "signup" || !user.onboarding_completed) {
          window.location.href = `dashboard.html?onboarding=true&redirect=${encodeURIComponent(redirectTarget)}`;
        } else {
          window.location.href = redirectTarget;
        }

      } catch (err) {
        let msg = err.message || "Authentication failed. Please verify your credentials.";
        if (msg.includes("409") || msg.toLowerCase().includes("already registered")) {
          msg = "An account with this email address already exists. Please sign in instead.";
        } else if (msg.includes("401") || msg.toLowerCase().includes("incorrect email or password")) {
          msg = "Incorrect email or password. Please try again.";
        }
        showAlert(msg, "error");
        submitBtn.disabled = false;
        submitBtn.textContent = currentMode === "signup" ? "Create account →" : "Sign in →";
      }
    });
  };

  document.addEventListener("DOMContentLoaded", init);
})();
