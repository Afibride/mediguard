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
        Community Health Platform &ndash; Bamenda, Cameroon
      </p>
    </td>
  </tr>
  <tr><td style="padding:32px 36px;">"""

_WRAP_CLOSE = """  </td></tr>
  <tr>
    <td style="background:#f8fafc;padding:20px 36px;border-top:1px solid #e2e8f0;text-align:center;">
      <p style="margin:0;font-size:11px;color:#94a3b8;">
        MediGuard Bamenda &middot; NAHPI Campus, Mankon, Bamenda &middot; Cameroon
      </p>
      <p style="margin:6px 0 0;font-size:11px;color:#94a3b8;">
        This is an automated message &mdash; please do not reply directly.
      </p>
    </td>
  </tr>
</table>
</td></tr>
</table>
</body></html>"""


def _wrap(body: str) -> str:
    return _WRAP_OPEN + body + _WRAP_CLOSE


# ─── Template: welcome ───────────────────────────────────────────────────────

def welcome_email(user_name: str) -> tuple[str, str]:
    """Return (subject, html)."""
    subject = "Welcome to MediGuard Bamenda!"
    html = _wrap(f"""
<h2 style="color:#0f172a;margin:0 0 16px;">Welcome to MediGuard! 🎉</h2>
<p style="color:#475569;margin:0 0 12px;">Hi <strong>{user_name}</strong>,</p>
<p style="color:#475569;margin:0 0 16px;">
  Your account is ready. Here is what you can do with MediGuard:
</p>
<ul style="color:#475569;margin:0 0 24px;padding-left:20px;line-height:2.2;">
  <li><strong>Symptom Checker</strong> &mdash; AI-powered disease assessment in seconds</li>
  <li><strong>MediGuard AI Chat</strong> &mdash; Ask any health question in plain language</li>
  <li><strong>Health History</strong> &mdash; Review past checks and results</li>
  <li><strong>Trends Dashboard</strong> &mdash; Live disease patterns in Bamenda</li>
  <li><strong>Nearby Facilities</strong> &mdash; Find clinics and hospitals near you</li>
</ul>
<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:16px;margin:0 0 24px;">
  <p style="color:#166534;margin:0;font-size:13px;line-height:1.6;">
    <strong>Important:</strong> MediGuard is a pre-consultation screening tool, not a replacement
    for professional medical care. Always visit a qualified health professional for diagnosis and treatment.
  </p>
</div>
<div style="text-align:center;margin:0 0 24px;">
  <a href="https://mediguard.app/symptom-checker"
     style="display:inline-block;background:#0891b2;color:#fff;padding:14px 36px;
            border-radius:8px;text-decoration:none;font-weight:bold;font-size:15px;">
    Start Your First Check
  </a>
</div>
<p style="color:#475569;margin:0;">Stay healthy,<br/><strong>The MediGuard Team</strong></p>
""")
    plain = (
        f"Welcome to MediGuard, {user_name}!\n\n"
        "Your account is ready. Visit https://mediguard.app to get started.\n\n"
        "Features: Symptom Checker, AI Chat, Health History, Trends Dashboard, Nearby Facilities.\n\n"
        "MediGuard is a pre-consultation tool — always consult a qualified health professional.\n\n"
        "– The MediGuard Team"
    )
    return subject, html, plain


# ─── Template: password reset ────────────────────────────────────────────────

def reset_password_email(reset_url: str, user_name: str, otp_code: str = "") -> tuple[str, str, str]:
    """Return (subject, html, plain).

    Both a clickable reset link and a 6-digit OTP code are included so the user
    can choose whichever method works best for them.
    """
    subject = "Reset your MediGuard password"

    otp_block = ""
    otp_plain = ""
    if otp_code:
        otp_block = f"""
<div style="background:#f8fafc;border:2px dashed #0891b2;border-radius:10px;
     padding:20px;margin:20px 0;text-align:center;">
  <p style="color:#64748b;margin:0 0 8px;font-size:12px;text-transform:uppercase;letter-spacing:0.8px;">
    Or enter this code on the reset page
  </p>
  <p style="font-size:36px;font-weight:bold;letter-spacing:10px;color:#0f172a;margin:0;
            font-family:'Courier New',monospace;">
    {otp_code}
  </p>
  <p style="color:#94a3b8;margin:8px 0 0;font-size:11px;">
    Valid for 30 minutes &mdash; do not share this code with anyone
  </p>
</div>"""
        otp_plain = f"\n\nOr enter this 6-digit code on the reset page: {otp_code}\n(Valid for 30 minutes — do not share)"

    html = _wrap(f"""
<h2 style="color:#0f172a;margin:0 0 16px;">Reset your password</h2>
<p style="color:#475569;margin:0 0 12px;">Hi <strong>{user_name}</strong>,</p>
<p style="color:#475569;margin:0 0 24px;">
  We received a request to reset the password for your MediGuard account.
  Click the button below &mdash; the link expires in <strong>30&nbsp;minutes</strong>.
</p>
<div style="text-align:center;margin:28px 0;">
  <a href="{reset_url}"
     style="display:inline-block;background:#0891b2;color:#fff;padding:14px 36px;
            border-radius:8px;text-decoration:none;font-weight:bold;font-size:15px;">
    Reset My Password
  </a>
</div>
{otp_block}
<p style="color:#94a3b8;font-size:12px;margin:24px 0 8px;">
  If you didn&rsquo;t request a password reset, you can safely ignore this email &mdash;
  your password will not change.
</p>
<p style="color:#cbd5e1;font-size:11px;word-break:break-all;">
  If the button doesn&rsquo;t work, paste this link into your browser:<br/>
  <a href="{reset_url}" style="color:#0891b2;">{reset_url}</a>
</p>
""")
    plain = (
        f"Hi {user_name},\n\n"
        f"Reset your MediGuard password by visiting:\n{reset_url}\n"
        f"{otp_plain}\n\n"
        "This link/code expires in 30 minutes.\n"
        "If you didn't request this, ignore this email — your password won't change.\n\n"
        "– The MediGuard Team"
    )
    return subject, html, plain


# ─── Template: newsletter subscription confirmation ──────────────────────────

def subscription_confirmation_email(name: str, unsubscribe_url: str) -> tuple[str, str, str]:
    """Return (subject, html, plain)."""
    subject = "You're subscribed to MediGuard Health Alerts"
    html = _wrap(f"""
<h2 style="color:#0f172a;margin:0 0 16px;">You're subscribed! 🏥</h2>
<p style="color:#475569;margin:0 0 12px;">Hi <strong>{name}</strong>,</p>
<p style="color:#475569;margin:0 0 16px;">
  You have successfully subscribed to <strong>MediGuard Health Alerts</strong> for Bamenda, Cameroon.
</p>
<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:16px;margin:0 0 24px;">
  <p style="color:#0369a1;margin:0;font-size:13px;line-height:1.6;">
    <strong>What you'll receive:</strong><br/>
    &bull; Monthly disease trends digest for the Bamenda region<br/>
    &bull; Outbreak alerts when elevated disease activity is detected<br/>
    &bull; Seasonal prevention tips
  </p>
</div>
<p style="color:#475569;margin:0 0 16px;">
  You can also use the <strong>Symptom Checker</strong> and <strong>AI Chat</strong> on MediGuard
  any time &mdash; no registration needed.
</p>
<div style="text-align:center;margin:0 0 28px;">
  <a href="https://mediguard.app"
     style="display:inline-block;background:#0891b2;color:#fff;padding:12px 32px;
            border-radius:8px;text-decoration:none;font-weight:bold;font-size:14px;">
    Visit MediGuard
  </a>
</div>
<p style="color:#94a3b8;font-size:11px;margin:0;line-height:1.7;">
  To unsubscribe at any time, click here:
  <a href="{unsubscribe_url}" style="color:#0891b2;">Unsubscribe</a>
</p>
""")
    plain = (
        f"Hi {name},\n\n"
        "You're subscribed to MediGuard Health Alerts for Bamenda, Cameroon.\n\n"
        "You'll receive:\n"
        "- Monthly disease trends digest\n"
        "- Outbreak alerts\n"
        "- Seasonal prevention tips\n\n"
        f"To unsubscribe: {unsubscribe_url}\n\n"
        "– The MediGuard Team"
    )
    return subject, html, plain


# ─── Template: registered-user notification opt-in ───────────────────────────

def registered_subscription_email(user_name: str) -> tuple[str, str, str]:
    """Sent to a registered user when they opt-in (or re-confirm) email notifications.

    Unlike guest subscription, there is no unsubscribe token in the email body
    because registered users manage their preferences from their profile page.
    """
    subject = "MediGuard email notifications are ON"
    html = _wrap(f"""
<h2 style="color:#0f172a;margin:0 0 16px;">You're all set! ✅</h2>
<p style="color:#475569;margin:0 0 12px;">Hi <strong>{user_name}</strong>,</p>
<p style="color:#475569;margin:0 0 16px;">
  Email notifications are now <strong>enabled</strong> on your MediGuard account.
  You'll hear from us when it matters most:
</p>
<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:16px;margin:0 0 24px;">
  <p style="color:#0369a1;margin:0;font-size:13px;line-height:1.8;">
    <strong>What you'll receive:</strong><br/>
    &bull; <strong>Monthly health digest</strong> &mdash; top disease trends for Bamenda every 1st of the month<br/>
    &bull; <strong>Outbreak alerts</strong> &mdash; immediate notice when elevated activity is detected<br/>
    &bull; <strong>Seasonal prevention tips</strong> &mdash; rainy-season and dry-season advisories
  </p>
</div>
<p style="color:#475569;margin:0 0 16px;">
  You can turn off email notifications any time from your
  <strong>Profile &rsaquo; Notification Settings</strong> page.
</p>
<div style="text-align:center;margin:0 0 28px;">
  <a href="https://mediguard.app/profile"
     style="display:inline-block;background:#0891b2;color:#fff;padding:12px 32px;
            border-radius:8px;text-decoration:none;font-weight:bold;font-size:14px;">
    Go to My Profile
  </a>
</div>
<p style="color:#475569;margin:0;">Stay safe,<br/><strong>The MediGuard Team</strong></p>
""")
    plain = (
        f"Hi {user_name},\n\n"
        "Email notifications are now enabled on your MediGuard account.\n\n"
        "You'll receive:\n"
        "- Monthly disease trends digest (1st of each month)\n"
        "- Outbreak alerts when elevated activity is detected\n"
        "- Seasonal prevention tips\n\n"
        "Manage notifications at: https://mediguard.app/profile\n\n"
        "– The MediGuard Team"
    )
    return subject, html, plain


# ─── Template: monthly health digest ─────────────────────────────────────────

def monthly_digest_email(
    user_name: str,
    top_diseases: list[dict],
    alerts: list[dict],
    prevention_tips: list[dict],
    month_year: str,
    unsubscribe_url: str = "",
) -> tuple[str, str, str]:
    """Return (subject, html, plain).

    top_diseases: list of {disease, count, pct}
    alerts:       list of {disease, count, pct, level, reason}
    prevention_tips: list of {disease, tip}
    """
    subject = f"MediGuard Monthly Health Report — {month_year}"

    # ── Top diseases rows ──
    disease_rows = ""
    for i, d in enumerate(top_diseases[:5], 1):
        bar_width = max(6, int(d.get("pct", 0) * 1.8))
        disease_rows += (
            f'<tr>'
            f'<td style="padding:10px 0;border-bottom:1px solid #f1f5f9;color:#0f172a;font-weight:600;">'
            f'{i}. {d["disease"]}</td>'
            f'<td style="padding:10px 0;border-bottom:1px solid #f1f5f9;text-align:right;'
            f'color:#64748b;white-space:nowrap;">'
            f'<span style="display:inline-block;height:8px;width:{bar_width}px;'
            f'background:#0891b2;border-radius:4px;vertical-align:middle;margin-right:8px;"></span>'
            f'{d.get("pct", 0)}%</td>'
            f'</tr>'
        )

    # ── Alert rows ──
    level_colors  = {"high": "#dc2626", "medium": "#ea580c", "watch": "#ca8a04"}
    level_labels  = {"high": "HIGH RISK", "medium": "ELEVATED", "watch": "WATCH"}
    alert_rows = ""
    if alerts:
        for a in alerts[:3]:
            c = level_colors.get(a["level"], "#64748b")
            lbl = level_labels.get(a["level"], a["level"].upper())
            alert_rows += (
                f'<tr><td style="padding:10px 16px;border-bottom:1px solid #f1f5f9;">'
                f'<strong style="color:#0f172a;">{a["disease"]}</strong>'
                f'&nbsp;<span style="background:{c};color:#fff;padding:1px 7px;'
                f'border-radius:4px;font-size:10px;font-weight:bold;">{lbl}</span>'
                f'<br/><small style="color:#64748b;">{a["reason"]}</small>'
                f'</td></tr>'
            )

    # ── Tip rows ──
    tip_rows = "".join(
        f'<li style="color:#475569;margin:0 0 10px;line-height:1.6;">'
        f'<strong style="color:#0f172a;">{t["disease"]}:</strong> {t["tip"]}</li>'
        for t in prevention_tips[:4]
    )

    rainy = is_rainy_season()
    season_note = "Rainy season is active — malaria and water-borne disease risk is elevated." if rainy \
        else "Dry season — harmattan dust increases respiratory and meningitis risk."

    unsubscribe_section = ""
    if unsubscribe_url:
        unsubscribe_section = (
            f'<p style="color:#94a3b8;font-size:11px;margin:0;line-height:1.7;">'
            f'You received this because you subscribed to MediGuard health alerts.<br/>'
            f'<a href="{unsubscribe_url}" style="color:#0891b2;">Unsubscribe</a></p>'
        )

    html = _wrap(f"""
<h2 style="color:#0f172a;margin:0 0 6px;">Monthly Health Report</h2>
<p style="color:#64748b;margin:0 0 24px;font-size:13px;">{month_year} &middot; Bamenda Region, Cameroon</p>

<p style="color:#475569;margin:0 0 20px;">Hi <strong>{user_name}</strong>,</p>

<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:12px 16px;margin:0 0 24px;">
  <p style="color:#0369a1;margin:0;font-size:12px;">{season_note}</p>
</div>

<h3 style="color:#0f172a;font-size:13px;text-transform:uppercase;letter-spacing:0.5px;
    border-bottom:1px solid #e2e8f0;padding-bottom:8px;margin:0 0 4px;">
  Top Diseases This Month
</h3>
<table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
  {disease_rows if disease_rows else '<tr><td style="color:#94a3b8;padding:12px 0;">No screening data recorded this month.</td></tr>'}
</table>

{'<h3 style="color:#0f172a;font-size:13px;text-transform:uppercase;letter-spacing:0.5px;border-bottom:1px solid #e2e8f0;padding-bottom:8px;margin:0 0 4px;">Active Outbreak Alerts</h3><table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;margin:0 0 28px;">' + alert_rows + '</table>' if alerts else ''}

<h3 style="color:#0f172a;font-size:13px;text-transform:uppercase;letter-spacing:0.5px;
    border-bottom:1px solid #e2e8f0;padding-bottom:8px;margin:0 0 12px;">
  Prevention Tips
</h3>
<ul style="padding-left:20px;margin:0 0 28px;">
  {tip_rows}
</ul>

<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:14px 16px;margin:0 0 24px;">
  <p style="color:#475569;margin:0;font-size:12px;line-height:1.7;">
    <strong>Nearest facilities:</strong> Bamenda Regional Hospital &middot;
    Baptist Hospital Bamenda (Nkwen) &middot; NAHPI Medical Centre (Mankon).
    Visit <a href="https://mediguard.app/nearby-facilities" style="color:#0891b2;">MediGuard Facilities</a>
    for directions and contact numbers.
  </p>
</div>

<div style="text-align:center;margin:0 0 24px;">
  <a href="https://mediguard.app/trends"
     style="display:inline-block;background:#0891b2;color:#fff;padding:12px 32px;
            border-radius:8px;text-decoration:none;font-weight:bold;font-size:14px;">
    View Full Trends Dashboard
  </a>
</div>

{unsubscribe_section}
""")
    plain = (
        f"Monthly Health Report — {month_year}\nBamenda Region, Cameroon\n\n"
        f"Hi {user_name},\n\n{season_note}\n\n"
        "Top Diseases This Month:\n" +
        "\n".join(f"  {i+1}. {d['disease']} ({d.get('pct',0)}%)" for i, d in enumerate(top_diseases[:5])) +
        ("\n\nOutbreak Alerts:\n" + "\n".join(f"  - {a['disease']} [{a['level'].upper()}]: {a['reason']}" for a in alerts[:3]) if alerts else "") +
        "\n\nPrevention Tips:\n" +
        "\n".join(f"  - {t['disease']}: {t['tip']}" for t in prevention_tips[:4]) +
        "\n\nView full trends: https://mediguard.app/trends\n\n"
        + (f"Unsubscribe: {unsubscribe_url}\n\n" if unsubscribe_url else "") +
        "– The MediGuard Team"
    )
    return subject, html, plain


# ─── Template: outbreak alert ────────────────────────────────────────────────

def outbreak_alert_email(
    user_name: str,
    alerts: list[dict],
    prevention_tips: list[dict],
    unsubscribe_url: str = "",
) -> tuple[str, str, str]:
    """Return (subject, html, plain).
    alerts: list of {disease, count, pct, level, reason}
    prevention_tips: list of {disease, tip}
    """
    if not alerts:
        return "", "", ""

    top_level = max(alerts, key=lambda a: {"high": 2, "medium": 1, "watch": 0}[a["level"]])["level"]
    level_labels  = {"high": "HIGH RISK", "medium": "ELEVATED", "watch": "WATCH"}
    level_colors  = {"high": "#dc2626", "medium": "#ea580c", "watch": "#ca8a04"}
    bg_colors     = {"high": "#fef2f2", "medium": "#fff7ed", "watch": "#fefce8"}
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

    unsubscribe_section = ""
    if unsubscribe_url:
        unsubscribe_section = (
            f'<a href="{unsubscribe_url}" style="color:#0891b2;">Unsubscribe</a>'
        )
    else:
        unsubscribe_section = 'visit your <strong>Profile &rarr; Notification Settings</strong>'

    html = _wrap(f"""
<div style="background:{level_colors[top_level]};color:white;padding:12px 20px;
     border-radius:8px;margin:0 0 24px;text-align:center;">
  <strong style="font-size:14px;">Disease Outbreak Surveillance Alert &mdash; {level_labels[top_level]}</strong>
</div>

<h2 style="color:#0f172a;margin:0 0 8px;">Health Alert &ndash; Bamenda Region</h2>
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
    For emergencies, go immediately &mdash; do not wait.
  </p>
</div>

<p style="color:#94a3b8;font-size:11px;margin:0;line-height:1.7;">
  You received this alert because you opted into health notifications on MediGuard.<br/>
  To unsubscribe, {unsubscribe_section}.
</p>
""")
    plain = (
        f"[MediGuard Alert] {level_labels[top_level]} – Bamenda\n\n"
        f"Hi {user_name},\n\n"
        "Elevated disease activity detected in Bamenda:\n\n" +
        "\n".join(f"  - {a['disease']} [{a['level'].upper()}]: {a['reason']}" for a in alerts[:5]) +
        "\n\nPrevention tips:\n" +
        "\n".join(f"  - {t['disease']}: {t['tip']}" for t in prevention_tips[:5]) +
        "\n\nNearest facilities: Bamenda Regional Hospital, Baptist Hospital (Nkwen), NAHPI Medical Centre.\n\n" +
        (f"Unsubscribe: {unsubscribe_url}\n\n" if unsubscribe_url else "") +
        "– The MediGuard Team"
    )
    return subject, html, plain
