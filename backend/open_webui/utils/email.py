"""
Email utility module for sending emails via SMTP
Supports Gmail SMTP and custom SMTP servers
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from pathlib import Path

log = logging.getLogger(__name__)


class EmailService:
    """Email service for sending emails via SMTP"""
    
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        from_email: str,
        from_name: str = "OptimalMD",
        use_tls: bool = True
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.from_name = from_name
        self.use_tls = use_tls
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email using SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (optional, falls back to HTML stripped)
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Attach text content
            if text_content:
                part1 = MIMEText(text_content, 'plain')
                msg.attach(part1)
            
            # Attach HTML content
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)
            
            # Connect to SMTP server and send
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            log.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            log.error(f"Failed to send email to {to_email}: {str(e)}")
            return False


def get_welcome_email_template(user_name: str, user_email: str, password: str) -> str:
    """
    Generate welcome email HTML template with temporary password
    
    Args:
        user_name: Name of the user
        user_email: Email of the user
        password: Temporary password
    
    Returns:
        str: HTML email content
    """
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to OptimalMD</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }}
        .header p {{
            margin: 10px 0 0 0;
            font-size: 16px;
            opacity: 0.9;
        }}
        .content {{
            padding: 40px 30px;
        }}
        .welcome-message {{
            font-size: 18px;
            margin-bottom: 20px;
            color: #1f2937;
        }}
        .info-box {{
            background-color: #f0fdf4;
            border-left: 4px solid #16a34a;
            padding: 20px;
            margin: 25px 0;
            border-radius: 4px;
        }}
        .info-box h3 {{
            margin: 0 0 15px 0;
            color: #15803d;
            font-size: 16px;
            font-weight: 600;
        }}
        .credential {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 10px 0;
            padding: 12px;
            background-color: white;
            border-radius: 4px;
            border: 1px solid #d1fae5;
        }}
        .credential-label {{
            font-weight: 600;
            color: #065f46;
        }}
        .credential-value {{
            font-family: 'Courier New', monospace;
            font-size: 16px;
            color: #1f2937;
            background-color: #f9fafb;
            padding: 6px 12px;
            border-radius: 4px;
            border: 1px solid #e5e7eb;
        }}
        .warning-box {{
            background-color: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin: 25px 0;
            border-radius: 4px;
        }}
        .warning-box p {{
            margin: 0;
            color: #92400e;
            font-size: 14px;
        }}
        .instructions {{
            margin: 25px 0;
        }}
        .instructions h3 {{
            color: #1f2937;
            font-size: 16px;
            margin-bottom: 15px;
        }}
        .instructions ol {{
            padding-left: 20px;
        }}
        .instructions li {{
            margin: 10px 0;
            color: #4b5563;
        }}
        .cta-button {{
            display: inline-block;
            background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
            color: white;
            text-decoration: none;
            padding: 14px 32px;
            border-radius: 6px;
            font-weight: 600;
            margin: 20px 0;
            transition: transform 0.2s;
        }}
        .cta-button:hover {{
            transform: translateY(-2px);
        }}
        .footer {{
            background-color: #f9fafb;
            padding: 30px;
            text-align: center;
            border-top: 1px solid #e5e7eb;
        }}
        .footer p {{
            margin: 5px 0;
            color: #6b7280;
            font-size: 14px;
        }}
        .disclaimer {{
            background-color: #fef2f2;
            border: 1px solid #fecaca;
            padding: 15px;
            margin: 25px 0;
            border-radius: 4px;
            font-size: 12px;
            color: #991b1b;
            line-height: 1.5;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🩺 Welcome to OptimalMD</h1>
            <p>Your AI-Powered Health Companion</p>
        </div>
        
        <div class="content">
            <p class="welcome-message">
                Hello <strong>{user_name}</strong>,
            </p>
            
            <p>
                Thank you for creating an account with OptimalMD - My AI Doctor™. 
                Your account has been successfully created and we're excited to have you join our community!
            </p>
            
            <div class="info-box">
                <h3>📧 Your Login Credentials</h3>
                
                <div class="credential">
                    <span class="credential-label">Email:</span>
                    <span class="credential-value">{user_email}</span>
                </div>
                
                <div class="credential">
                    <span class="credential-label">Temporary Password:</span>
                    <span class="credential-value">{password}</span>
                </div>
            </div>
            
            <div class="warning-box">
                <p>
                    ⚠️ <strong>Important:</strong> This is a temporary password. 
                    For security reasons, please change your password immediately after your first login.
                </p>
            </div>
            
            <div class="instructions">
                <h3>🚀 Getting Started:</h3>
                <ol>
                    <li>Click the button below to access the OptimalMD platform</li>
                    <li>Sign in using your email and the temporary password provided above</li>
                    <li>Navigate to your account settings and change your password</li>
                    <li>Start exploring the powerful AI diagnostic tools</li>
                </ol>
            </div>
            
            <center>
                <a href="https://app.optimalmd.com" class="cta-button">
                    Access OptimalMD Platform →
                </a>
            </center>
            
            <div class="disclaimer">
                <strong>⚕️ Medical Disclaimer:</strong><br>
                By using this platform, you fully acknowledge that this is not medical advice and is not intended 
                to replace the relationship with your physician. OptimalMD accepts no responsibility for actions 
                taken based on the information gained from this AI diagnostic tool. It is for educational and 
                research use only. Always consult with a qualified healthcare provider for medical advice.
            </div>
            
            <p style="margin-top: 30px; color: #6b7280;">
                If you did not create this account or have any questions, please contact our support team immediately.
            </p>
        </div>
        
        <div class="footer">
            <p><strong>OptimalMD - My AI Doctor™</strong></p>
            <p>Your Diagnostic Companion</p>
            <p style="margin-top: 15px;">
                © 2025 OptimalMD. All rights reserved.
            </p>
        </div>
    </div>
</body>
</html>
"""


def get_password_reset_email_template(user_name: str, reset_password: str) -> str:
    """
    Generate password reset email HTML template
    
    Args:
        user_name: Name of the user
        reset_password: New temporary password
    
    Returns:
        str: HTML email content
    """
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Password Reset - OptimalMD</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }}
        .content {{
            padding: 40px 30px;
        }}
        .info-box {{
            background-color: #fef2f2;
            border-left: 4px solid #dc2626;
            padding: 20px;
            margin: 25px 0;
            border-radius: 4px;
        }}
        .password-display {{
            font-family: 'Courier New', monospace;
            font-size: 24px;
            color: #1f2937;
            background-color: #f9fafb;
            padding: 15px;
            border-radius: 4px;
            border: 2px solid #dc2626;
            text-align: center;
            margin: 20px 0;
            letter-spacing: 2px;
        }}
        .cta-button {{
            display: inline-block;
            background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
            color: white;
            text-decoration: none;
            padding: 14px 32px;
            border-radius: 6px;
            font-weight: 600;
            margin: 20px 0;
        }}
        .footer {{
            background-color: #f9fafb;
            padding: 30px;
            text-align: center;
            border-top: 1px solid #e5e7eb;
        }}
        .footer p {{
            margin: 5px 0;
            color: #6b7280;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Password Reset</h1>
        </div>
        
        <div class="content">
            <p>Hello <strong>{user_name}</strong>,</p>
            
            <p>
                We received a request to reset your password for your OptimalMD account. 
                Your new temporary password is:
            </p>
            
            <div class="password-display">
                {reset_password}
            </div>
            
            <div class="info-box">
                <p>
                    ⚠️ <strong>Important Security Notice:</strong><br>
                    Please change this temporary password immediately after logging in. 
                    If you did not request this password reset, please contact support immediately.
                </p>
            </div>
            
            <center>
                <a href="https://app.optimalmd.com" class="cta-button">
                    Login to OptimalMD →
                </a>
            </center>
            
            <p style="margin-top: 30px; color: #6b7280;">
                This temporary password will remain active until you change it.
            </p>
        </div>
        
        <div class="footer">
            <p><strong>OptimalMD - My AI Doctor™</strong></p>
            <p>© 2025 OptimalMD. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
