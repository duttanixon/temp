import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.core.config import settings
from typing import List, Optional


def send_email(
    to_addresses: List[str],
    subject: str,
    body: str,
    from_address: Optional[str] = None,
    cc_addresses: Optional[List[str]] = None,
    bcc_addresses: Optional[List[str]] = None,
    is_html: bool = False,
) -> bool:
    """
    Send an email using the SMTP server configured in settings
    """
    if not settings.SMTP_SERVER:
        # Log error or handle the case when SMTP is not configured
        print("SMTP server is not configured.")
        return False
    
    if from_address is None:
        from_address = settings.EMAIL_FROM
    
    msg = MIMEMultipart()
    msg["From"] = from_address
    msg["To"] = ", ".join(to_addresses)
    msg["Subject"] = subject
    
    if cc_addresses:
        msg["Cc"] = ", ".join(cc_addresses)
    
    if bcc_addresses:
        msg["Bcc"] = ", ".join(bcc_addresses)
    
    if is_html:
        msg.attach(MIMEText(body, "html"))
    else:
        msg.attach(MIMEText(body, "plain"))
    
    try:
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        
        all_recipients = to_addresses.copy()
        if cc_addresses:
            all_recipients.extend(cc_addresses)
        if bcc_addresses:
            all_recipients.extend(bcc_addresses)
        
        server.sendmail(from_address, all_recipients, msg.as_string())
        server.quit()
        print(f"Email sent successfully to {', '.join(to_addresses)}")
        return True
    except Exception as e:
        # Log the error or handle it appropriately
        print(f"Error sending email here: {str(e)}")
        return False


def send_welcome_email(email: str, name: str, password: str) -> bool:
    """
    Send a welcome email to a new user
    """
    subject = "Welcome to Edge Device Management System"
    body = f"""
    Hello {name},
    
    Welcome to the Edge Device Management System. Your account has been created.
    
    Your login details:
    Email: {email}
    Password: {password}
    
    Please log in and change your password.
    
    Regards,
    The Edge Device Management Team
    """
    
    return send_email([email], subject, body)


def send_password_reset_email(email: str, reset_token: str) -> bool:
    """
    Send a password reset email
    """
    subject = "Password Reset Request"
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    body = f"""
    Hello,
    
    You have requested to reset your password. Click the link below to set a new password:
    
    {reset_url}
    
    If you did not request this reset, please ignore this email.
    
    Regards,
    The Edge Device Management Team
    """
    
    return send_email([email], subject, body)


def send_password_set_email(email: str, name: str, reset_token: str) -> bool:
    """
    Send password set email for new users
    """
    subject = "Set Your Password - Edge Device Management System"
    reset_url = f"{settings.FRONTEND_URL}/set-password?token={reset_token}"
    body = f"""
    Hello {name},
    
    Welcome to the Edge Device Management System! Your account has been created.
    
    Please click the link below to set your password:
    
    {reset_url}
    
    This link will expire in 2 hours.
    
    If you did not expect this email, please ignore it.
    
    Regards,
    The Edge Device Management Team
    """
    
    return send_email([email], subject, body)