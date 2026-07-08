"""
outreach_sender.py — sends an email via SendGrid (default) or Gmail SMTP,
depending on config.SEND_PROVIDER.
"""

import smtplib
from email.mime.text import MIMEText

import requests

import config


def send_via_sendgrid(to_email, subject, body):
    if not config.SENDGRID_API_KEY:
        raise RuntimeError("SENDGRID_API_KEY not set")

    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": config.FROM_EMAIL, "name": config.FROM_NAME},
        "reply_to": {"email": config.REPLY_TO},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
    }
    resp = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {config.SENDGRID_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=15,
    )
    if resp.status_code not in (200, 202):
        raise RuntimeError(f"SendGrid error {resp.status_code}: {resp.text}")


def send_via_smtp(to_email, subject, body):
    if not (config.SMTP_USER and config.SMTP_PASSWORD):
        raise RuntimeError("SMTP_USER / SMTP_PASSWORD not set")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = f"{config.FROM_NAME} <{config.SMTP_USER}>"
    msg["To"] = to_email
    msg["Reply-To"] = config.REPLY_TO

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        server.sendmail(config.SMTP_USER, [to_email], msg.as_string())


def send_email(to_email, subject, body):
    if config.SEND_PROVIDER == "smtp":
        send_via_smtp(to_email, subject, body)
    else:
        send_via_sendgrid(to_email, subject, body)
