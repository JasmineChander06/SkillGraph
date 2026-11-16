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

        // Hide form and show generic confirmation without revealing email or account existence
        form.classList.add("hidden");
        if (noticeText) {
          noticeText.textContent = "If an account exists with the email address you entered, we will send a password reset link.";
        }
        successView?.classList.remove("hidden");

      } catch (err) {
        let msg = err.message || "Failed to process password reset. Please try again.";
        if (err.status === 429) {
          msg = err.message || "Too many password reset requests. Please wait a few minutes before trying again.";
        } else if (err.status === 503) {
          msg = err.message || "Email delivery service is currently unavailable. Please try again later.";
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

