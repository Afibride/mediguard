"""
Email sending utility for MediGuard.

Uses Python's built-in smtplib so no extra dependencies are needed.
Set SMTP_USER + SMTP_PASSWORD in .env to enable; if unset every call
is a silent no-op so the app keeps working in development.
"""
import asyncio
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def email_configured() -> bool:
    from app.config import get_settings
    s = get_settings()
    return bool(s.smtp_user and s.smtp_password)


def is_rainy_season() -> bool:
    """April–October is the rainy season in Bamenda/NW Cameroon."""
    return datetime.utcnow().month in range(4, 11)


# ─── Low-level send (runs in a thread) ──────────────────────────────────────

def _send_sync(to: str, subject: str, html: str, plain: str) -> None:
    import smtplib
    from app.config import get_settings
    s = get_settings()
    from_addr = s.smtp_from or f"MediGuard Bamenda <{s.smtp_user}>"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to
    if plain:
        msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    if s.smtp_port == 465:
        import ssl
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(s.smtp_host, s.smtp_port, context=ctx, timeout=20) as srv:
            srv.login(s.smtp_user, s.smtp_password)
            srv.sendmail(from_addr, [to], msg.as_string())
    else:
        with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=20) as srv:
            srv.ehlo()
            srv.starttls()
            srv.ehlo()
            srv.login(s.smtp_user, s.smtp_password)
            srv.sendmail(from_addr, [to], msg.as_string())


async def send_email(to: str, subject: str, html: str, plain: str = "") -> bool:
    if not email_configured():
        logger.warning("SMTP not configured — email skipped for %s", to)
        return False
    try:
        await asyncio.to_thread(_send_sync, to, subject, html, plain)
        logger.info("Email sent → %s  |  %s", to, subject)
        return True
    except Exception as exc:
        logger.error("Email failed → %s: %s", to, exc)
        return False


# ─── Shared HTML base layout ─────────────────────────────────────────────────

_WRAP_OPEN = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MediGuard</title></head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:32px 16px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0"
  style="background:#fff;border-radius:12px;overflow:hidden;
         box-shadow:0 2px 12px rgba(0,0,0,0.08);max-width:600px;width:100%;">
  <tr>
    <td style="background:linear-gradient(135deg,#0891b2 0%,#0e7490 100%);padding:30px 36px;text-align:center;">
      <h1 style="color:#fff;margin:0;font-size:26px;letter-spacing:-0.5px;">MediGuard</h1>
      <p style="color:rgba(255,255,255,0.8);margin:4px 0 0;font-size:13px;">
        Community Health Platform – Bamenda, Cameroon
      </p>
    </td>
  </tr>
  <tr><td style="padding:32px 36px;">"""

_WRAP_CLOSE = """  </td></tr>
  <tr>
    <td style="background:#f8fafc;padding:20px 36px;border-top:1px solid #e2e8f0;text-align:center;">
      <p style="margin:0;font-size:11px;color:#94a3b8;">
        MediGuard Bamenda · NAHPI Campus, Mankon, Bamenda · Cameroon
      </p>
      <p style="margin:6px 0 0;font-size:11px;color:#94a3b8;">
        This is an automated message — please do not reply directly.
      </p>
    </td>
  </tr>
</table>
</td></tr>
</table>
</body></html>"""


def _wrap(body: str) -> str:
    return _WRAP_OPEN + body + _WRAP_CLOSE


# ─── Template: password reset ────────────────────────────────────────────────

def reset_password_email(reset_url: str, user_name: str) -> tuple[str, str]:
    """Return (subject, html)."""
    subject = "Reset your MediGuard password"
    html = _wrap(f"""
<h2 style="color:#0f172a;margin:0 0 16px;">Reset your password</h2>
<p style="color:#475569;margin:0 0 12px;">Hi <strong>{user_name}</strong>,</p>
<p style="color:#475569;margin:0 0 24px;">
  We received a request to reset the password for your MediGuard account.
  Click the button below — the link expires in <strong>30&nbsp;minutes</strong>.
</p>
<div style="text-align:center;margin:28px 0;">
  <a href="{reset_url}"
     style="display:inline-block;background:#0891b2;color:#fff;padding:14px 36px;
            border-radius:8px;text-decoration:none;font-weight:bold;font-size:15px;">
    Reset My Password
  </a>
</div>
<p style="color:#94a3b8;font-size:12px;margin:24px 0 8px;">
  If you didn&rsquo;t request a password reset, you can safely ignore this email —
  your password will not change.
</p>
<p style="color:#cbd5e1;font-size:11px;word-break:break-all;">
  If the button doesn&rsquo;t work, paste this link into your browser:<br/>
  <a href="{reset_url}" style="color:#0891b2;">{reset_url}</a>
</p>
""")
    return subject, html


# ─── Template: welcome ───────────────────────────────────────────────────────

def welcome_email(user_name: str) -> tuple[str, str]:
    """Return (subject, html)."""
    subject = "Welcome to MediGuard Bamenda!"
    html = _wrap(f"""
<h2 style="color:#0f172a;margin:0 0 16px;">Welcome to MediGuard!</h2>
<p style="color:#475569;margin:0 0 12px;">Hi <strong>{user_name}</strong>,</p>
<p style="color:#475569;margin:0 0 16px;">Your account is ready. Here is what you can do:</p>
<ul style="color:#475569;margin:0 0 24px;padding-left:20px;line-height:2.0;">
  <li><strong>Symptom Checker</strong> — AI-powered disease assessment in seconds</li>
  <li><strong>MediGuard AI Chat</strong> — Ask any health question in plain language</li>
  <li><strong>Health History</strong> — Review past checks and chats</li>
  <li><strong>Trends Dashboard</strong> — Live disease patterns in Bamenda</li>
</ul>
<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:16px;margin:0 0 20px;">
  <p style="color:#166534;margin:0;font-size:13px;">
    <strong>Important:</strong> MediGuard is a pre-consultation tool, not a replacement
    for professional medical care. Always visit a qualified health professional for diagnosis and treatment.
  </p>
</div>
<p style="color:#475569;margin:0;">Stay healthy,<br/><strong>The MediGuard Team</strong></p>
""")
    return subject, html


# ─── Template: outbreak alert ────────────────────────────────────────────────

def outbreak_alert_email(
    user_name: str,
    alerts: list[dict],
    prevention_tips: list[dict],
) -> tuple[str, str]:
    """Return (subject, html).
    alerts: list of {disease, count, pct, level, reason}
    prevention_tips: list of {disease, tip}
    """
    if not alerts:
        return "", ""

    top_level = max(alerts, key=lambda a: {"high": 2, "medium": 1, "watch": 0}[a["level"]])["level"]
    level_labels = {"high": "HIGH RISK", "medium": "ELEVATED", "watch": "WATCH"}
    level_colors = {"high": "#dc2626", "medium": "#ea580c", "watch": "#ca8a04"}
    bg_colors    = {"high": "#fef2f2", "medium": "#fff7ed", "watch": "#fefce8"}
    border_colors = {"high": "#dc2626", "medium": "#ea580c", "watch": "#ca8a04"}

    subject = f"[MediGuard Alert] {level_labels[top_level]} – Disease Surveillance for Bamenda"

    # Build alert rows
    alert_rows_html = ""
    for a in alerts[:5]:
        bg = bg_colors[a["level"]]
        bc = border_colors[a["level"]]
        bl = level_labels[a["level"]]
        cnt = f"{a['count']:,}"
        alert_rows_html += (
            f'<tr><td style="padding:12px 16px;border-bottom:1px solid #f1f5f9;'
            f'background:{bg};border-left:4px solid {bc};">'
            f'<strong style="color:#0f172a;">{a["disease"]}</strong>'
            f'&nbsp;<span style="background:{bc};color:white;padding:2px 8px;'
            f'border-radius:4px;font-size:10px;font-weight:bold;">{bl}</span>'
            f'<br/><small style="color:#64748b;">{a["reason"]} &middot; {cnt} screenings</small>'
            f'</td></tr>'
        )

    # Build tip rows
    tip_rows_html = ""
    for t in prevention_tips[:5]:
        tip_rows_html += (
            f'<li style="margin:0 0 12px;color:#475569;line-height:1.6;">'
            f'<strong style="color:#0f172a;">{t["disease"]}:</strong> {t["tip"]}</li>'
        )

    rainy = is_rainy_season()
    season_label = "Rainy Season" if rainy else "Dry Season"

    html = _wrap(f"""
<div style="background:{level_colors[top_level]};color:white;padding:12px 20px;
     border-radius:8px;margin:0 0 24px;text-align:center;">
  <strong style="font-size:14px;">Disease Outbreak Surveillance Alert — {level_labels[top_level]}</strong>
</div>

<h2 style="color:#0f172a;margin:0 0 8px;">Health Alert – Bamenda Region</h2>
<p style="color:#475569;margin:0 0 20px;">
  Hi <strong>{user_name}</strong>, MediGuard has detected elevated disease activity in Bamenda
  based on current screening patterns. Please read the prevention tips below and share them
  with your family and community.
</p>

<h3 style="color:#0f172a;margin:0 0 10px;font-size:13px;
    text-transform:uppercase;letter-spacing:0.6px;border-bottom:1px solid #e2e8f0;padding-bottom:8px;">
  Current Alert Conditions
</h3>
<table width="100%" cellpadding="0" cellspacing="0"
  style="border-radius:8px;overflow:hidden;border:1px solid #e2e8f0;margin:0 0 28px;">
  {alert_rows_html}
</table>

<h3 style="color:#0f172a;margin:0 0 10px;font-size:13px;
    text-transform:uppercase;letter-spacing:0.6px;border-bottom:1px solid #e2e8f0;padding-bottom:8px;">
  {season_label} Prevention Tips
</h3>
<ul style="padding-left:20px;margin:0 0 24px;">
  {tip_rows_html}
</ul>

<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:16px;margin:0 0 20px;">
  <p style="color:#0369a1;margin:0;font-size:13px;line-height:1.6;">
    <strong>Nearest facility:</strong> Bamenda Regional Hospital (Hospital Roundabout) &middot;
    Baptist Hospital Bamenda (Nkwen) &middot; NAHPI Medical Centre (Mankon).
    For emergencies, go immediately — do not wait.
  </p>
</div>

<p style="color:#94a3b8;font-size:11px;margin:0;line-height:1.7;">
  You received this alert because you opted into health notifications on MediGuard.<br/>
  To unsubscribe, visit your <strong>Profile &rarr; Notification Settings</strong>.
</p>
""")
    return subject, html
