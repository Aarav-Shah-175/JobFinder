import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any

def send_email_notification(top_jobs: List[Dict[str, Any]], report_filepath: str) -> bool:
    """
    Sends daily email notification if SMTP env variables are set.
    """
    smtp_server = os.getenv("EMAIL_SMTP_SERVER")
    smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    recipient = os.getenv("EMAIL_RECIPIENT") or sender

    if not smtp_server or not sender or not password:
        return False

    try:
        with open(report_filepath, "r", encoding="utf-8") as f:
            report_content = f.read()
    except Exception:
        report_content = "Daily Job Report Attached."

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = f"🎯 Aarav's Personal Daily Job Report — Top Matches ({len(top_jobs)})"

    msg.attach(MIMEText(report_content, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email notification failed: {e}")
        return False
