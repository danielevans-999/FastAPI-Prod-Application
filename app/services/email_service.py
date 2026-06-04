import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# from app.core.config import settings
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)


def send_smtp_email(to: str, subject: str, body: str, html: str = None):
    """
    Core SMTP email sender
    Pure function — NO Celery decorator
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = settings.MAIL_FROM
    msg["To"]      = to

    msg.attach(MIMEText(body, "plain"))
    if html:
        msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
        server.sendmail(settings.MAIL_FROM, to, msg.as_string())

    logger.info(f"Email sent to {to}")
    return True


def send_welcome_email(email: str, username: str):
    """
    Send welcome email — ALL BUSINESS LOGIC HERE (no duplication)
    """
    subject = f"Welcome to {settings.APP_NAME}!"
    body = f"Hi {username}, welcome aboard!"
    html = f"""
        <h1>Welcome {username}!</h1>
        <p>Your account has been created successfully.</p>
        <p>Thank you for joining {settings.APP_NAME}.</p>
    """
    send_smtp_email(to=email, subject=subject, body=body, html=html)
    logger.info(f"Welcome email sent to {email}")


def send_password_reset_email(email: str, reset_token: str):
    """
    Send password reset email — ALL BUSINESS LOGIC HERE (no duplication)
    """
    reset_url = f"https://yourdomain.com/reset-password?token={reset_token}"
    subject = "Password Reset Request"
    body = f"Click this link to reset your password: {reset_url}"
    html = f"""
        <h2>Password Reset</h2>
        <p>Click the button below to reset your password:</p>
        <a href="{reset_url}"
           style="background:#007bff;color:white;padding:10px 20px;
                  text-decoration:none;border-radius:5px;">
           Reset Password
        </a>
        <p>This link expires in 1 hour.</p>
        <p>If you did not request this, ignore this email.</p>
    """
    send_smtp_email(to=email, subject=subject, body=body, html=html)
    logger.info(f"Password reset email sent to {email}")


def send_notification_email(email: str, title: str, message: str):
    """
    Send notification email — ALL BUSINESS LOGIC HERE (no duplication)
    """
    html = f"<h3>{title}</h3><p>{message}</p>"
    send_smtp_email(to=email, subject=title, body=message, html=html)
    logger.info(f"Notification email sent to {email}")


def send_daily_reports():
    """
    Send daily reports — ALL BUSINESS LOGIC HERE
    """
    logger.info("Sending daily reports...")


send_smtp_email("karanide001@gmail.com", "Test Subject", "Test Body")