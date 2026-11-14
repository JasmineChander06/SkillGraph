/**
 * SkillGraph Forgot Password Controller
 * Handles password reset email initiation with enumeration protection and rate-limit feedback.
 * Paper & Ink Edition — Pure Vanilla JavaScript
 */

(() => {
  const form = document.getElementById("forgot-form");
  const emailInput = document.getElementById("forgot-email");
  const submitBtn = document.getElementById("forgot-submit-btn");
  const alertBox = document.getElementById("recovery-alert");
  const successView = document.getElementById("recovery-success-view");
  const noticeText = document.getElementById("success-email-notice");
  const tryAnotherBtn = document.getElementById("btn-try-another");

  const EMAIL_REGEX = /^[\w.\-+]+@[\w-]+\.[a-zA-Z]{2,}$/;

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

      const email = emailInput.value.trim().toLowerCase();

      // Client-side format validation
      if (!email) {
        showAlert("Please enter your registered email address.");
        emailInput.focus();
        return;
      }

      if (!EMAIL_REGEX.test(email)) {
        showAlert("Please enter a valid email address (e.g. name@domain.com).");
        emailInput.focus();
        return;
      }

      // Enter loading state
      submitBtn.disabled = true;
      submitBtn.textContent = "Sending reset link…";

      try {
        await API.auth.forgotPassword(email);

        // Hide form and show confirmation
        form.classList.add("hidden");
        if (noticeText) {
          noticeText.innerHTML = `If an account is associated with <strong>${App.escapeHtml(email)}</strong>, we have dispatched a password reset link. The link will remain active for 20 minutes.`;
        }
        successView?.classList.remove("hidden");

      } catch (err) {
        let msg = err.message || "Failed to process password reset. Please try again.";
        if (err.status === 429) {
          msg = err.message || "Too many password reset requests. Please wait a few minutes before trying again.";
        }
        showAlert(msg, "error");
        submitBtn.disabled = false;
        submitBtn.textContent = "Send Reset Link →";
      }
    });

    tryAnotherBtn?.addEventListener("click", () => {
      successView?.classList.add("hidden");
      form?.classList.remove("hidden");
      emailInput.value = "";
      submitBtn.disabled = false;
      submitBtn.textContent = "Send Reset Link →";
      hideAlert();
      emailInput.focus();
    });
  };

  document.addEventListener("DOMContentLoaded", () => {
    setupForm();
  });
})();

