
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load .env file directly using absolute path
ENV_PATH = "/var/www/pharmgpt-backend/.env"
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

    async def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """Send a generic email with HTML content"""
        if not self.enabled:
            print(f"📧 [MOCK EMAIL] To: {to_email} | Subject: {subject}")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"PharmGPT <{self.smtp_user}>"
            msg["To"] = to_email

            if not text_content:
                # Basic HTML to text conversion fallback
                text_content = html_content.replace("<br>", "\n").replace("</p>", "\n\n")

            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            # Use synchronous SMTP in async wrapper if needed, but for now simple blocking is fine for scripts
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, to_email, msg.as_string())
            
            print(f"✅ Email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False

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

    def send_reengagement_email(self, to_email: str, first_name: str = "there") -> bool:
        """Send re-engagement email to inactive users"""
        if not self.enabled:
            print(f"📧 [MOCK EMAIL] Re-engagement to: {to_email}")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "We miss you at PharmGPT! 💊"
            msg["From"] = f"PharmGPT <{self.smtp_user}>"
            msg["To"] = to_email

            html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #18181b; margin: 0;">PharmGPT</h1>
                </div>
                <h2 style="color: #18181b; margin-bottom: 16px;">Hey {first_name}, we miss you! 👋</h2>
                <p style="color: #71717a; font-size: 16px; line-height: 1.6;">
                    It's been a while since you last visited PharmGPT. We've been busy adding new features and improvements to help with your pharmacology research!
                </p>
                <p style="color: #71717a; font-size: 16px; line-height: 1.6;">
                    Here's what's new:
                </p>
                <ul style="color: #71717a; font-size: 16px; line-height: 1.8;">
                    <li>🔬 <strong>Deep Research Mode</strong> – PubMed-powered literature reviews</li>
                    <li>📄 <strong>Document Analysis</strong> – Upload PDFs for instant insights</li>
                    <li>⚡ <strong>Faster Responses</strong> – Improved AI performance</li>
                </ul>
                <div style="text-align: center; margin: 32px 0;">
                    <a href="https://pharmgpt.vercel.app/chat" style="display: inline-block; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; padding: 16px 32px; border-radius: 12px; text-decoration: none; font-weight: bold; font-size: 16px;">
                        Continue Your Research →
                    </a>
                </div>
                <p style="color: #a1a1aa; font-size: 14px;">
                    If you'd prefer not to receive these emails, simply reply with "unsubscribe".
                </p>
                <hr style="border: none; border-top: 1px solid #e4e4e7; margin: 32px 0;">
                <p style="color: #a1a1aa; font-size: 12px; text-align: center;">
                    © 2024 PharmGPT. Your AI-powered pharmaceutical assistant.
                </p>
            </div>
            """
            
            text = f"Hey {first_name}, we miss you at PharmGPT! Visit https://pharmgpt.vercel.app/chat to continue your research."
            
            msg.attach(MIMEText(text, "plain"))
            msg.attach(MIMEText(html, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, to_email, msg.as_string())
            
            print(f"✅ Re-engagement email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send re-engagement email: {e}")
            return False

    def send_password_reset_email(self, to_email: str, reset_link: str) -> bool:
        """Send password reset link via email"""
        if not self.enabled:
            print(f"📧 [MOCK EMAIL] Password Reset to: {to_email} | Link: {reset_link}")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Reset your PharmGPT Password"
            msg["From"] = f"PharmGPT <{self.smtp_user}>"
            msg["To"] = to_email

            html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #18181b; margin: 0;">PharmGPT</h1>
                </div>
                <h2 style="color: #18181b; margin-bottom: 16px;">Reset your password</h2>
                <p style="color: #71717a; font-size: 16px; line-height: 1.6;">
                    We received a request to reset your password. Click the button below to choose a new password:
                </p>
                <div style="text-align: center; margin: 32px 0;">
                    <a href="{reset_link}" style="background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%); color: white; padding: 14px 32px; border-radius: 12px; text-decoration: none; font-weight: 600; display: inline-block;">Reset Password</a>
                </div>
                <p style="color: #71717a; font-size: 14px;">
                    This link will expire in 30 minutes. If you didn't request a password reset, you can safely ignore this email.
                </p>
                <p style="color: #a1a1aa; font-size: 12px; text-align: center; margin-top: 32px;">
                    If the button doesn't work, copy and paste this link into your browser:<br>
                    <a href="{reset_link}" style="color: #6366f1;">{reset_link}</a>
                </p>
            </div>
            """
            
            text = f"Reset your PharmGPT password by visiting this link:\n{reset_link}\n\nThis link expires in 30 minutes."
            
            msg.attach(MIMEText(text, "plain"))
            msg.attach(MIMEText(html, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, to_email, msg.as_string())
            
            print(f"✅ Password reset email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send password reset email: {e}")
            return False
