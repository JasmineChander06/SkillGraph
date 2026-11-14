/**
 * SkillGraph Reset Password Controller
 * Handles token verification, cryptographically secure password generation,
 * real-time strength evaluation, and submission to the backend.
 * Paper & Ink Edition — Pure Vanilla JavaScript
 */

(() => {
  // DOM Elements
  const formContainer = document.getElementById("reset-form-container");
  const invalidTokenView = document.getElementById("invalid-token-view");
  const successView = document.getElementById("reset-success-view");
  const form = document.getElementById("reset-form");
  const newPasswordInput = document.getElementById("new-password");
  const confirmPasswordInput = document.getElementById("confirm-password");
  const toggleNewBtn = document.getElementById("toggle-new-password");
  const toggleConfirmBtn = document.getElementById("toggle-confirm-password");
  const generateBtn = document.getElementById("btn-generate-password");
  const submitBtn = document.getElementById("reset-submit-btn");
  const alertBox = document.getElementById("reset-alert");
  const strengthBar = document.getElementById("strength-bar");
  const strengthLabel = document.getElementById("strength-label");
  const strengthDetail = document.getElementById("strength-detail");
  const matchStatus = document.getElementById("match-status");

  // Requirement elements
  const reqLength = document.getElementById("req-length");
  const reqUpper = document.getElementById("req-upper");
  const reqLower = document.getElementById("req-lower");
  const reqNumber = document.getElementById("req-number");
  const reqSpecial = document.getElementById("req-special");

  // Read Token from URL search parameters
  const urlParams = new URLSearchParams(window.location.search);
  const resetToken = (urlParams.get("token") || "").trim();

  const init = () => {
    if (!resetToken || resetToken.length < 16) {
      showInvalidTokenView();
      return;
    }

    setupVisibilityToggles();
    setupPasswordGenerator();
    setupRealtimeValidation();
    setupFormSubmission();
  };

  const showInvalidTokenView = () => {
    formContainer?.classList.add("hidden");
    invalidTokenView?.classList.remove("hidden");
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

  /**
   * Password Visibility Toggles
   */
  const setupVisibilityToggles = () => {
    const eyeSvg = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
        <circle cx="12" cy="12" r="3"></circle>
      </svg>`;
    const eyeOffSvg = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
        <line x1="1" y1="1" x2="23" y2="23"></line>
      </svg>`;

    const setupToggle = (btn, input) => {
      btn?.addEventListener("click", () => {
        const isPassword = input.type === "password";
        input.type = isPassword ? "text" : "password";
        btn.innerHTML = isPassword ? eyeOffSvg : eyeSvg;
        btn.setAttribute("aria-label", isPassword ? "Hide password" : "Show password");
      });
    };

    setupToggle(toggleNewBtn, newPasswordInput);
    setupToggle(toggleConfirmBtn, confirmPasswordInput);
  };

  /**
   * Cryptographically Secure Password Generator
   * Generates a 16-character high-entropy password with guaranteed character distribution.
   */
  const setupPasswordGenerator = () => {
    generateBtn?.addEventListener("click", () => {
      const uppers = "ABCDEFGHJKLMNPQRSTUVWXYZ"; // removed confusing I, O
      const lowers = "abcdefghijkmnopqrstuvwxyz"; // removed confusing l
      const digits = "23456789";                  // removed confusing 0, 1
      const symbols = "!@#$%^&*()_+~|}{[]:;?><=";
      const allChars = uppers + lowers + digits + symbols;

      // Ensure at least 2 of each category for compliance
      const getRandomChar = (pool) => {
        const array = new Uint32Array(1);
        window.crypto.getRandomValues(array);
        return pool[array[0] % pool.length];
      };

      const passwordChars = [
        getRandomChar(uppers),
        getRandomChar(uppers),
        getRandomChar(lowers),
        getRandomChar(lowers),
        getRandomChar(digits),
        getRandomChar(digits),
        getRandomChar(symbols),
        getRandomChar(symbols)
      ];

      // Fill remaining 8 characters from combined pool
      while (passwordChars.length < 16) {
        passwordChars.push(getRandomChar(allChars));
      }

      // Shuffle using Fisher-Yates with crypto random values
      for (let i = passwordChars.length - 1; i > 0; i--) {
        const array = new Uint32Array(1);
        window.crypto.getRandomValues(array);
        const j = array[0] % (i + 1);
        [passwordChars[i], passwordChars[j]] = [passwordChars[j], passwordChars[i]];
      }

      const generatedPassword = passwordChars.join("");

      // Populate both fields
      newPasswordInput.value = generatedPassword;
      confirmPasswordInput.value = generatedPassword;

      // Reveal passwords briefly so user can see what was generated
      newPasswordInput.type = "text";
      confirmPasswordInput.type = "text";
      if (toggleNewBtn) toggleNewBtn.setAttribute("aria-label", "Hide password");
      if (toggleConfirmBtn) toggleConfirmBtn.setAttribute("aria-label", "Hide password");

      evaluateStrength(generatedPassword);
      checkMatch();
      hideAlert();

      if (window.App && typeof window.App.showToast === "function") {
        window.App.showToast("Strong 16-character password generated.", "info");
      }
    });
  };

  /**
   * Evaluate Password Strength & Requirements
   */
  const evaluateStrength = (password) => {
    const hasLength = password.length >= 8;
    const hasUpper = /[A-Z]/.test(password);
    const hasLower = /[a-z]/.test(password);
    const hasNumber = /\d/.test(password);
    const hasSpecial = /[!@#$%^&*(),.?":{}|<>\-_=+[\]\\/`~;']/.test(password);

    const updateReq = (el, met, label) => {
      if (!el) return;
      if (met) {
        el.classList.add("met");
        el.innerHTML = `<span class="req-icon" style="color:#10B981;">✓</span> ${label}`;
      } else {
        el.classList.remove("met");
        el.innerHTML = `<span class="req-icon">&bull;</span> ${label}`;
      }
    };

    updateReq(reqLength, hasLength, "Minimum 8 characters");
    updateReq(reqUpper, hasUpper, "One uppercase letter (A-Z)");
    updateReq(reqLower, hasLower, "One lowercase letter (a-z)");
    updateReq(reqNumber, hasNumber, "One number (0-9)");
    updateReq(reqSpecial, hasSpecial, "One special character (!@#$%^&* etc.)");

    // Calculate score
    let score = 0;
    if (hasLength) score += 1;
    if (hasUpper) score += 1;
    if (hasLower) score += 1;
    if (hasNumber) score += 1;
    if (hasSpecial) score += 1;
    if (password.length >= 14) score += 1; // bonus entropy

    strengthBar.className = "strength-bar";

    if (password.length === 0) {
      strengthLabel.textContent = "Too short";
      strengthDetail.textContent = "Entropy calculation";
      strengthBar.style.width = "0%";
      return false;
    }

    if (score <= 2) {
      strengthBar.classList.add("weak");
      strengthLabel.textContent = "Weak";
      strengthLabel.style.color = "#EF4444";
      strengthDetail.textContent = "Missing key complexity rules";
    } else if (score === 3 || score === 4) {
      strengthBar.classList.add("fair");
      strengthLabel.textContent = "Moderate";
      strengthLabel.style.color = "#F59E0B";
      strengthDetail.textContent = "Meets basic requirements";
    } else if (score === 5) {
      strengthBar.classList.add("good");
      strengthLabel.textContent = "Strong";
      strengthLabel.style.color = "#3B82F6";
      strengthDetail.textContent = "All criteria satisfied";
    } else {
      strengthBar.classList.add("strong");
      strengthLabel.textContent = "Very Strong";
      strengthLabel.style.color = "#10B981";
      strengthDetail.textContent = "High entropy protected";
    }

    return hasLength && hasUpper && hasLower && hasNumber && hasSpecial;
  };

  /**
   * Password Confirmation Matching Status
   */
  const checkMatch = () => {
    const pw = newPasswordInput.value;
    const confirm = confirmPasswordInput.value;

    if (!confirm) {
      matchStatus.style.display = "none";
      return false;
    }

    matchStatus.style.display = "block";
    if (pw === confirm) {
      matchStatus.textContent = "✓ Passwords match";
      matchStatus.style.color = "#10B981";
      return true;
    } else {
      matchStatus.textContent = "✕ Passwords do not match";
      matchStatus.style.color = "#EF4444";
      return false;
    }
  };

  const setupRealtimeValidation = () => {
    newPasswordInput?.addEventListener("input", () => {
      evaluateStrength(newPasswordInput.value);
      if (confirmPasswordInput.value) checkMatch();
    });

    confirmPasswordInput?.addEventListener("input", () => {
      checkMatch();
    });
  };

  /**
   * Form Submission to Backend API
   */
  const setupFormSubmission = () => {
    form?.addEventListener("submit", async (e) => {
      e.preventDefault();
      hideAlert();

      const newPassword = newPasswordInput.value;
      const confirmPassword = confirmPasswordInput.value;

      // Validate all complexity criteria
      const isStrong = evaluateStrength(newPassword);
      if (!isStrong) {
        showAlert("Please ensure your new password satisfies all requirements listed below.");
        newPasswordInput.focus();
        return;
      }

      // Validate match
      if (newPassword !== confirmPassword) {
        showAlert("Password confirmation does not match. Please verify both fields.");
        confirmPasswordInput.focus();
        return;
      }

      // Enter loading state
      submitBtn.disabled = true;
      submitBtn.textContent = "Resetting password…";

      try {
        await API.auth.resetPassword(resetToken, newPassword);

        // Hide form and display success view
        formContainer.classList.add("hidden");
        successView.classList.remove("hidden");

        if (window.App && typeof window.App.showToast === "function") {
          window.App.showToast("Password reset successfully.", "success");
        }

      } catch (err) {
        let errorMsg = err.message || "Failed to reset password. The link may have expired or was already used.";
        showAlert(errorMsg, "error");
        submitBtn.disabled = false;
        submitBtn.textContent = "Reset Password →";
      }
    });
  };

  document.addEventListener("DOMContentLoaded", init);
})();
