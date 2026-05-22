from ..celery_app import celery_app
from ..config import settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)


def send_smtp_email(to: str, subject: str, body: str, html: str = None):
    """Core SMTP email sender"""
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


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email(self, email: str, username: str):
    """Send welcome email after registration"""
    try:
        send_smtp_email(
            to      = email,
            subject = f"Welcome to {settings.APP_NAME}!",
            body    = f"Hi {username}, welcome aboard!",
            html    = f"""
                <h1>Welcome {username}!</h1>
                <p>Your account has been created successfully.</p>
                <p>Thank you for joining {settings.APP_NAME}.</p>
            """
        )
        logger.info(f"Welcome email sent to {email}")
    except Exception as exc:
        logger.error(f"Failed to send welcome email to {email}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_email(self, email: str, reset_token: str):
    """Send password reset email"""
    reset_url = f"https://yourdomain.com/reset-password?token={reset_token}"
    try:
        send_smtp_email(
            to      = email,
            subject = "Password Reset Request",
            body    = f"Click this link to reset your password: {reset_url}",
            html    = f"""
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
        )
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task
def send_daily_reports():
    """Scheduled task — send daily reports to admins"""
    logger.info("Sending daily reports...")
    # Add report generation logic here


@celery_app.task(bind=True, max_retries=3)
def send_notification_email(self, email: str, title: str, message: str):
    """Send notification email"""
    try:
        send_smtp_email(
            to      = email,
            subject = title,
            body    = message,
            html    = f"<h3>{title}</h3><p>{message}</p>"
        )
    except Exception as exc:
        raise self.retry(exc=exc)
