import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from logger_config import setup_logger

logger = setup_logger("email_service")

# Email credentials and config
SENDER_EMAIL = "manukbanik30@gmail.com"       # Replace with your sending email
SENDER_PASSWORD = "Sanchait@1"     # Replace with your 16-character App Password
ALERT_RECIPIENT = "manukbanik30@gmail.com"

def send_invalid_query_alert(rejected_query: str):
    """
    Sends an email notification when a user triggers the input guardrail.
    """
    subject = "Alert: Invalid User Query Detected in SQL App"
    body = f"""Hello,

An invalid/out-of-scope query was submitted by a user:

--------------------------------------------------
Query Entered:
{rejected_query}
--------------------------------------------------

Status: Blocked by Input Guardrail.

Best regards,
SQL Query Executor Bot
"""

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = ALERT_RECIPIENT
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, ALERT_RECIPIENT, msg.as_string())
        logger.info(f"Notification email successfully sent to {ALERT_RECIPIENT}")
    except Exception as e:
        logger.error(f"Failed to send alert email: {e}")