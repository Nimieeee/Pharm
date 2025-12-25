
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load .env file directly using absolute path
ENV_PATH = "/opt/pharmgpt-backend/.env"
if os.path.exists(ENV_PATH):
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


class EmailService:
    def __init__(self):
        self.smtp_host = "smtp.gmail.com"
        self.smtp_port = 587
        self.smtp_user = os.getenv("SMTP_USER", "noreply.pharmgpt@gmail.com")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        
        if not self.smtp_password:
            print("⚠️ SMTP_PASSWORD not found. Emails will be logged only.")
            self.enabled = False
        else:
            self.enabled = True
            print(f"✅ Gmail SMTP email service initialized ({self.smtp_user})")

    def send_verification_email(self, to_email: str, code: str) -> bool:
        """Send verification code via email"""
        if not self.enabled:
            print(f"📧 [MOCK EMAIL] To: {to_email} | Code: {code}")
            return True

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Verify your PharmGPT Account"
            msg["From"] = f"PharmGPT <{self.smtp_user}>"
            msg["To"] = to_email

            # HTML content
            html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #18181b; margin: 0;">PharmGPT</h1>
                </div>
                <h2 style="color: #18181b; margin-bottom: 16px;">Verify your email address</h2>
                <p style="color: #71717a; font-size: 16px; line-height: 1.6;">
                    Please use the following code to verify your email address and complete your registration:
                </p>
                <div style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); padding: 24px; text-align: center; border-radius: 16px; margin: 32px 0;">
                    <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: white; font-family: monospace;">{code}</span>
                </div>
                <p style="color: #71717a; font-size: 14px;">
                    This code will expire in 15 minutes. If you didn't request this code, you can safely ignore this email.
                </p>
                <hr style="border: none; border-top: 1px solid #e4e4e7; margin: 32px 0;">
                <p style="color: #a1a1aa; font-size: 12px; text-align: center;">
                    © 2024 PharmGPT. Your AI-powered pharmaceutical assistant.
                </p>
            </div>
            """
            
            # Plain text fallback
            text = f"Your PharmGPT verification code is: {code}\n\nThis code will expire in 15 minutes."
            
            msg.attach(MIMEText(text, "plain"))
            msg.attach(MIMEText(html, "html"))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, to_email, msg.as_string())
            
            print(f"✅ Email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
