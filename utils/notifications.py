"""Notification sender."""

import requests
from typing import Optional


def send_telegram(token: str, chat_id: str, message: str) -> bool:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})
    return resp.status_code == 200


def send_slack(webhook_url: str, message: str, channel: Optional[str] = None) -> bool:
    payload = {"text": message}
    if channel:
        payload["channel"] = channel
    resp = requests.post(webhook_url, json=payload)
    return resp.status_code == 200


def send_email(smtp_host: str, smtp_port: int, sender: str, password: str, to: str, subject: str, body: str) -> bool:
    import smtplib
    from email.mime.text import MIMEText

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
        return True
    except Exception:
        return False
