"""Email dispatch service supporting SMTP delivery with secure templates and logging fallback."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Optional

from app.config import settings

logger = logging.getLogger("skillgraph.services.email")


def generate_password_reset_email_html(reset_url: str, recipient_name: Optional[str] = None) -> str:
    """Build a responsive, branded HTML email for password recovery."""
    greeting = f"Hello {recipient_name}," if recipient_name else "Hello,"
    expiry_minutes = settings.RESET_TOKEN_EXPIRE_MINUTES

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Reset Your SkillGraph Password</title>
</head>
<body style="margin:0; padding:0; background-color:#FBF9F5; font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif; color:#18181B;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#FBF9F5; padding:40px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width:540px; background-color:#FFFFFF; border:1px solid #E4E4E7; border-radius:12px; padding:36px; box-shadow:0 4px 12px rgba(0,0,0,0.03);">
          <!-- Logo & Brand Header -->
          <tr>
            <td style="padding-bottom:24px; border-bottom:1px solid #F4F4F5;">
              <table role="presentation" cellspacing="0" cellpadding="0">
                <tr>
                  <td style="width:32px; height:32px; background-color:#18181B; border-radius:50%; text-align:center; vertical-align:middle; color:#FFFFFF; font-family:'Fraunces',Georgia,serif; font-weight:700; font-size:16px;">
                    S
                  </td>
                  <td style="padding-left:10px; font-family:'Fraunces',Georgia,serif; font-size:20px; font-weight:600; color:#18181B; letter-spacing:-0.01em;">
                    SkillGraph
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Main Content -->
          <tr>
            <td style="padding-top:28px; padding-bottom:8px;">
              <h1 style="font-family:'Fraunces',Georgia,serif; font-size:22px; font-weight:600; color:#18181B; margin:0 0 16px; line-height:1.25;">
                Reset Your Password
              </h1>
              <p style="font-size:15px; line-height:1.6; color:#52525B; margin:0 0 16px;">
                {greeting}
              </p>
              <p style="font-size:15px; line-height:1.6; color:#52525B; margin:0 0 24px;">
                We received a request to reset the password for your SkillGraph account. Click the button below to choose a new password:
              </p>
            </td>
          </tr>

          <!-- Action Button -->
          <tr>
            <td align="center" style="padding-bottom:28px;">
              <a href="{reset_url}" target="_blank" rel="noopener noreferrer" style="display:inline-block; background-color:#18181B; color:#FBF9F5; font-size:14px; font-weight:500; text-decoration:none; padding:12px 28px; border-radius:9999px; letter-spacing:0.02em;">
                Reset Password &rarr;
              </a>
            </td>
          </tr>

          <!-- Fallback URL -->
          <tr>
            <td style="padding-bottom:24px; font-size:13px; line-height:1.6; color:#71717A; word-break:break-all;">
              If the button above does not work, copy and paste this link into your browser:<br>
              <a href="{reset_url}" style="color:#18181B; text-decoration:underline;">{reset_url}</a>
            </td>
          </tr>

          <!-- Expiry & Security Warning -->
          <tr>
            <td style="padding:16px; background-color:#FBF9F5; border:1px solid #E4E4E7; border-radius:8px; font-size:12.5px; line-height:1.5; color:#71717A;">
              <strong>Security Notice:</strong> This password reset link is valid for <strong>{expiry_minutes} minutes</strong> and can only be used once. If you did not request this change, you can safely ignore this email—your password will remain secure.
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding-top:28px; border-top:1px solid #F4F4F5; font-size:12px; color:#A1A1AA; text-align:center; line-height:1.5;">
              &copy; 2026 SkillGraph &bull; Deterministic Career Readiness & Graph Analysis.<br>
              Zero plaintext password retention &bull; Salted PBKDF2 cryptography.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_password_reset_email(to_email: str, recipient_name: Optional[str], reset_token: str) -> bool:
    """Send a secure password reset email via SMTP, falling back to secure local logging if SMTP is unconfigured."""
    reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/frontend/reset-password.html?token={reset_token}"
    expiry_minutes = settings.RESET_TOKEN_EXPIRE_MINUTES

    # Always log the recovery action securely on the backend for auditing & development
    logger.info("Initiated password reset request for %s (link valid for %d minutes)", to_email, expiry_minutes)

    # Check if SMTP credentials are configured
    is_smtp_configured = bool(settings.SMTP_HOST and settings.SMTP_USERNAME and settings.SMTP_PASSWORD)

    if not is_smtp_configured:
        # Development / staging fallback without live mail credentials:
        # We log the generated link so administrators and automated test harnesses can simulate the user flow
        logger.warning(
            "SMTP credentials not fully configured (SMTP_USERNAME/SMTP_PASSWORD empty). "
            "SIMULATED EMAIL DISPATCH -> Reset Link for %s: %s",
            to_email,
            reset_url,
        )
        return True

    # Real SMTP Dispatch
    msg = EmailMessage()
    msg["Subject"] = "Reset Your SkillGraph Password"
    msg["From"] = f"SkillGraph <{settings.SMTP_FROM_EMAIL}>"
    msg["To"] = to_email

    plain_content = (
        f"Reset Your SkillGraph Password\n\n"
        f"We received a request to reset your password. Use the link below to select a new password:\n"
        f"{reset_url}\n\n"
        f"This link will expire in {expiry_minutes} minutes.\n"
        f"If you did not request this, please disregard this email."
    )
    msg.set_content(plain_content)

    html_content = generate_password_reset_email_html(reset_url=reset_url, recipient_name=recipient_name)
    msg.add_alternative(html_content, subtype="html")

    try:
        if settings.SMTP_USE_TLS:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)

        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()

        logger.info("Successfully delivered password reset email to %s via SMTP (%s:%d)", to_email, settings.SMTP_HOST, settings.SMTP_PORT)
        return True

    except Exception as exc:
        logger.error("Failed to deliver SMTP password reset email to %s: %s", to_email, exc)
        # Even if SMTP provider fails, log the recovery link for operational reliability
        logger.info("FALLBACK RECOVERY LINK for %s: %s", to_email, reset_url)
        return False
