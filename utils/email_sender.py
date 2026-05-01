import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import os
from typing import Optional, List


def send_report_email(
    sender_email: str,
    sender_password: str,
    recipient_emails: List[str],
    subject: str,
    report_text: str,
    html_body: Optional[str] = None,
    attachment_path: Optional[str] = None
) -> dict:
    """Send report email via Gmail SMTP."""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = ", ".join(recipient_emails)

        # Plain text fallback
        plain_body = f"""SmartReport Agent — Automated Business Intelligence Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{report_text}

---
Sent by SmartReport Agent | Powered by Sash.AI-style Intelligence
"""
        msg.attach(MIMEText(plain_body, 'plain'))

        # HTML version
        if html_body:
            msg.attach(MIMEText(html_body, 'html'))
        else:
            html = _build_html_email(report_text, subject)
            msg.attach(MIMEText(html, 'html'))

        # Attachment
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(attachment_path)}"')
            msg.attach(part)

        # Send
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_emails, msg.as_string())

        return {"success": True, "message": f"Report sent to {', '.join(recipient_emails)}"}

    except smtplib.SMTPAuthenticationError:
        return {"success": False, "message": "Authentication failed. Check your Gmail App Password."}
    except Exception as e:
        return {"success": False, "message": f"Email error: {str(e)}"}


def _build_html_email(report_text: str, subject: str) -> str:
    """Build a styled HTML email."""
    lines = report_text.split('\n')
    html_lines = []
    for line in lines:
        if line.startswith('## '):
            html_lines.append(f'<h2 style="color:#1a1a2e;border-bottom:2px solid #e74c3c;padding-bottom:6px">{line[3:]}</h2>')
        elif line.startswith('### '):
            html_lines.append(f'<h3 style="color:#16213e">{line[4:]}</h3>')
        elif line.startswith('- '):
            html_lines.append(f'<li style="margin:4px 0">{line[2:]}</li>')
        elif line.startswith('**') and line.endswith('**'):
            html_lines.append(f'<strong>{line[2:-2]}</strong><br>')
        elif line.strip() == '':
            html_lines.append('<br>')
        else:
            html_lines.append(f'<p style="margin:4px 0">{line}</p>')

    body = '\n'.join(html_lines)
    return f"""
    <html><body style="font-family:Georgia,serif;max-width:700px;margin:auto;color:#333;padding:20px">
    <div style="background:#1a1a2e;color:white;padding:20px;border-radius:8px;margin-bottom:20px">
        <h1 style="margin:0;font-size:22px">📊 SmartReport Agent</h1>
        <p style="margin:4px 0;opacity:0.8;font-size:13px">{subject}</p>
        <p style="margin:4px 0;opacity:0.6;font-size:12px">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
    <div style="padding:10px">{body}</div>
    <div style="background:#f8f9fa;padding:12px;border-radius:6px;margin-top:20px;font-size:11px;color:#888;text-align:center">
        SmartReport Agent · Powered by AI · Enterprise Intelligence Platform
    </div>
    </body></html>"""
