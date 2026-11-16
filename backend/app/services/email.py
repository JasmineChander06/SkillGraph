"""Email dispatch service supporting Resend Transactional API and SMTP delivery."""

from __future__ import annotations

import json
import logging
import smtplib
from email.message import EmailMessage
from typing import Optional
import urllib.request
import urllib.error

from app.config import settings

logger = logging.getLogger("skillgraph.services.email")


def generate_password_reset_email_html(reset_url: str, recipient_name: Optional[str] = None) -> str:
    """Build a responsive, branded HTML email for password recovery matching SkillGraph Paper & Ink aesthetic."""
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
              <p style="font-size:15px; line-height:1.6; color:#18181B; margin:0 0 16px;">
                {greeting}
              </p>
              <p style="font-size:15px; line-height:1.6; color:#52525B; margin:0 0 16px;">
                We received a request to reset your SkillGraph account password.
              </p>
              <p style="font-size:15px; line-height:1.6; color:#52525B; margin:0 0 24px;">
                Click the button below to choose a new password:
              </p>
            </td>
          </tr>

          <!-- Action Button -->
          <tr>
            <td align="center" style="padding-bottom:28px;">
              <a href="{reset_url}" target="_blank" rel="noopener noreferrer" style="display:inline-block; background-color:#18181B; color:#FBF9F5; font-size:14px; font-weight:500; text-decoration:none; padding:13px 32px; border-radius:9999px; letter-spacing:0.02em;">
                Reset My Password &rarr;
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

          <!-- Expiry Notice -->
          <tr>
            <td style="padding:16px; background-color:#FBF9F5; border:1px solid #E4E4E7; border-radius:8px; font-size:12.5px; line-height:1.5; color:#71717A;">
              This link expires in <strong>{expiry_minutes} minutes</strong> and can only be used once.<br><br>
              If you did not request this password reset, you can safely ignore this email.
            </td>
          </tr>

          <!-- Sign-off & Footer -->
          <tr>
            <td style="padding-top:24px; font-size:14px; line-height:1.6; color:#52525B;">
              Regards,<br>
              <strong>SkillGraph Team</strong>
            </td>
          </tr>
          <tr>
            <td style="padding-top:24px; border-top:1px solid #F4F4F5; font-size:12px; color:#A1A1AA; text-align:center; line-height:1.5;">
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


def _send_via_resend(to_email: str, subject: str, html_content: str, plain_content: str) -> bool:
    """Send an email using Resend's transactional HTTPS API (recommended for Render & cloud deployment)."""
    api_key = settings.RESEND_API_KEY.strip()
    if not api_key:
        return False

    url = "https://api.resend.com/emails"
    from_email = settings.SMTP_FROM_EMAIL.strip() or "SkillGraph <onboarding@resend.dev>"
    # Ensure from_email includes a display name
    if "<" not in from_email:
        from_email = f"SkillGraph <{from_email}>"

    payload_dict = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "html": html_content,
        "text": plain_content,
    }
    payload_bytes = json.dumps(payload_dict).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload_bytes,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "SkillGraph-Auth/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            status_code = response.getcode()
            body = response.read().decode("utf-8")
            if 200 <= status_code < 300:
                resp_json = json.loads(body)
                email_id = resp_json.get("id", "ok")
                logger.info("Successfully delivered password reset email to %s via Resend API (id=%s)", to_email, email_id)
                return True
            else:
                logger.error("Resend API rejected email dispatch to %s with status %s: %s", to_email, status_code, body)
                return False
    except urllib.error.HTTPError as http_err:
        err_msg = http_err.read().decode("utf-8", errors="replace")
        logger.error("Resend HTTPError (%d) sending to %s: %s", http_err.code, to_email, err_msg)
        return False
    except Exception as exc:
        logger.error("Network or unexpected exception dispatching via Resend to %s: %s", to_email, type(exc).__name__)
        return False


def _send_via_smtp(to_email: str, subject: str, html_content: str, plain_content: str) -> bool:
    """Send an email using standard authenticated SMTP (e.g. Gmail App Password, AWS SES, Brevo, SendGrid)."""
    msg = EmailMessage()
    msg["Subject"] = subject
    from_addr = settings.SMTP_FROM_EMAIL.strip() or settings.SMTP_USERNAME.strip()
    msg["From"] = f"SkillGraph <{from_addr}>"
    msg["To"] = to_email

    msg.set_content(plain_content)
    msg.add_alternative(html_content, subtype="html")

    host = settings.SMTP_HOST.strip()
    port = settings.SMTP_PORT
    username = settings.SMTP_USERNAME.strip()
    password = settings.SMTP_PASSWORD.strip()
    use_ssl = getattr(settings, "SMTP_SSL", False) or port == 465

    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, timeout=12)
            server.ehlo()
        else:
            server = smtplib.SMTP(host, port, timeout=12)
            server.ehlo()
            if settings.SMTP_USE_TLS:
                server.starttls()
                server.ehlo()

        server.login(username, password)
        server.send_message(msg)
        server.quit()

        logger.info("Successfully delivered password reset email to %s via SMTP (%s:%d)", to_email, host, port)
        return True

    except smtplib.SMTPAuthenticationError as auth_err:
        logger.error("SMTP Authentication Failed for %s on %s:%d: %s", username, host, port, auth_err)
        return False
    except smtplib.SMTPException as smtp_err:
        logger.error("SMTP error dispatching to %s via %s:%d: %s", to_email, host, port, smtp_err)
        return False
    except Exception as exc:
        logger.error("Unexpected error connecting to SMTP server %s:%d: %s", host, port, type(exc).__name__)
        return False


def send_password_reset_email(to_email: str, recipient_name: Optional[str], reset_token: str) -> bool:
    """Send a secure password reset email using the configured delivery provider (Resend API or SMTP).
    
    Returns True if an email provider successfully accepted the message for delivery.
    Returns False if no provider is configured or if delivery failed.
    """
    reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/frontend/reset-password.html?token={reset_token}"
    expiry_minutes = settings.RESET_TOKEN_EXPIRE_MINUTES

    subject = "Reset Your SkillGraph Password"
    greeting = f"Hello {recipient_name}," if recipient_name else "Hello,"
    plain_content = (
        f"{greeting}\n\n"
        f"We received a request to reset your SkillGraph account password.\n\n"
        f"Click the link below to choose a new password:\n"
        f"{reset_url}\n\n"
        f"This link expires in {expiry_minutes} minutes and can only be used once.\n\n"
        f"If you did not request this password reset, you can safely ignore this email.\n\n"
        f"Regards,\n"
        f"SkillGraph Team\n"
    )
    html_content = generate_password_reset_email_html(reset_url=reset_url, recipient_name=recipient_name)

    # 1. Try Resend API (HTTP port 443 — most reliable on cloud platforms like Render)
    if settings.RESEND_API_KEY and settings.RESEND_API_KEY.strip():
        logger.info("Dispatching password reset email to %s via Resend API", to_email)
        return _send_via_resend(to_email, subject, html_content, plain_content)

    # 2. Try SMTP if username and password are provided
    if settings.SMTP_HOST and settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
        logger.info("Dispatching password reset email to %s via SMTP (%s:%d)", to_email, settings.SMTP_HOST, settings.SMTP_PORT)
        return _send_via_smtp(to_email, subject, html_content, plain_content)

    # 3. Unconfigured Provider:
    # Log clearly that no live email provider credentials are set.
    logger.error(
        "NO EMAIL SERVICE CONFIGURED: Neither RESEND_API_KEY nor SMTP credentials (SMTP_USERNAME/SMTP_PASSWORD) are set. "
        "Email cannot be dispatched to %s.",
        to_email,
    )
    # In development mode only, log the recovery link for local manual testing
    if settings.ENVIRONMENT.lower() == "development":
        logger.info(
            "LOCAL DEV FALLBACK: Password recovery link for %s: %s",
            to_email,
            reset_url,
        )

    return False
