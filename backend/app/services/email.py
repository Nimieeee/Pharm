
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

class EmailService:
    def __init__(self):
        self.smtp_host = "smtp.gmail.com"
        self.smtp_port = 587
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        
        # Clean the password in case it has quotes from a manual .env loader
        if self.smtp_password:
            self.smtp_password = self.smtp_password.strip("'\"")
        
        if not self.smtp_password:
            print("⚠️ SMTP_PASSWORD not found. Emails will be logged only.")
            self.enabled = False
        else:
            self.enabled = True
            print(f"✅ Gmail SMTP email service initialized ({self.smtp_user})")
            
        # Path to the logo for embedding
        self.logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "frontend/public/Benchside.png")
        if not os.path.exists(self.logo_path):
            # Fallback check - maybe we are in backend root
            self.logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend/public/Benchside.png")
            
        if not os.path.exists(self.logo_path):
            # Fallback for VPS structure if different
            self.logo_path = "/var/www/pharmgpt-backend/frontend/public/Benchside.png"

    async def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """Send a generic email with HTML content and optional inline logo"""
        if not self.enabled:
            print(f"📧 [MOCK EMAIL] To: {to_email} | Subject: {subject}")
            return True

        try:
            # Use 'related' for inline images
            msg = MIMEMultipart("related")
            msg["Subject"] = subject
            msg["From"] = f"Benchside <{self.smtp_user}>"
            msg["To"] = to_email

            # Alternative part for text/html
            msg_alternative = MIMEMultipart("alternative")
            msg.attach(msg_alternative)

            if not text_content:
                text_content = html_content.replace("<br>", "\n").replace("</p>", "\n\n")

            msg_alternative.attach(MIMEText(text_content, "plain"))
            
            # Replace placeholder URL with CID if present in html_content
            cid_logo = "logo_image"
            if "https://benchside.vercel.app/Benchside.png" in html_content:
                html_content = html_content.replace("https://benchside.vercel.app/Benchside.png", f"cid:{cid_logo}")
            elif "Benchside.png" in html_content and "cid:" not in html_content:
                # Catch other variations
                import re
                html_content = re.sub(r'src="[^"]*Benchside\.png"', f'src="cid:{cid_logo}"', html_content)

            msg_alternative.attach(MIMEText(html_content, "html"))

            # Attach the logo if it exists
            if os.path.exists(self.logo_path):
                from email.mime.image import MIMEImage
                with open(self.logo_path, "rb") as f:
                    img = MIMEImage(f.read())
                    img.add_header("Content-ID", f"<{cid_logo}>")
                    img.add_header("Content-Disposition", "inline", filename="Benchside.png")
                    msg.attach(img)
            else:
                 print(f"⚠️ Logo not found at {self.logo_path}, skipping inline attachment")

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, to_email, msg.as_string())
            
            print(f"✅ Email sent to {to_email} (CID Embedded Logo)")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False

    async def send_verification_email(self, to_email: str, code: str) -> bool:
        """Send verification code via email"""
        subject = "Verify your Benchside Account"
        
        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <img src="https://benchside.vercel.app/Benchside.png" alt="Benchside Logo" width="80" height="80" style="display: block; margin: 0 auto; width: 80px; height: 80px; outline: none; border: none; text-decoration: none;">
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
                © 2026 Benchside. Your AI-powered pharmaceutical assistant.
            </p>
        </div>
        """
        
        text = f"Your Benchside verification code is: {code}\n\nThis code will expire in 15 minutes."
        
        return await self.send_email(to_email, subject, html, text)

    async def send_reengagement_email(self, to_email: str, first_name: str = "there") -> bool:
        """Send re-engagement email to inactive users"""
        subject = "We miss you at Benchside! 💊"
        
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <img src="https://benchside.vercel.app/Benchside.png" alt="Benchside Logo" width="80" height="80" style="display: block; margin: 0 auto; width: 80px; height: 80px; outline: none; border: none; text-decoration: none;">
                    </div>
                    <p>Hi there,</p>
                    <p>It's been a while since you last visited Benchside. We've been busy adding new features and improvements to help with your pharmacology research!</p>
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
                <a href="https://benchside.vercel.app/chat" style="display: inline-block; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; padding: 16px 32px; border-radius: 12px; text-decoration: none; font-weight: bold; font-size: 16px;">
                    Continue Your Research →
                </a>
            </div>
            <p style="color: #a1a1aa; font-size: 14px;">
                If you'd prefer not to receive these emails, simply reply with "unsubscribe".
            </p>
            <hr style="border: none; border-top: 1px solid #e4e4e7; margin: 32px 0;">
            <p style="color: #a1a1aa; font-size: 12px; text-align: center;">
                © 2026 Benchside. Your AI-powered pharmaceutical assistant.
            </p>
        </div>
        """
        
        text = f"Hey {first_name}, we miss you at Benchside! Visit https://benchside.app/chat to continue your research."
        
        return await self.send_email(to_email, subject, html, text)

    async def send_password_reset_email(self, to_email: str, reset_link: str) -> bool:
        """Send password reset link via email"""
        subject = "Reset your Benchside Password"
        
        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <img src="https://benchside.vercel.app/Benchside.png" alt="Benchside Logo" width="80" height="80" style="display: block; margin: 0 auto; width: 80px; height: 80px; outline: none; border: none; text-decoration: none;">
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
        
        text = f"Reset your Benchside password by visiting this link:\n{reset_link}\n\nThis link expires in 30 minutes."
        
        return await self.send_email(to_email, subject, html, text)

    async def send_welcome_email(self, to_email: str, first_name: str = "there") -> bool:
        """Send welcome email with roadmap after verification"""
        subject = "You’re in. Here is your roadmap. 🗺️"
        
        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px; color: #18181b;">
            <div style="text-align: center; margin-bottom: 30px;">
                <img src="https://benchside.vercel.app/Benchside.png" alt="Benchside Logo" width="80" height="80" style="display: block; margin: 0 auto; width: 80px; height: 80px; outline: none; border: none; text-decoration: none;">
            </div>
            <h2 style="font-size: 24px; font-weight: 700; color: #18181b; margin-bottom: 24px;">You’re in. Here is your roadmap. 🗺️</h2>
            
            <p style="font-size: 16px; line-height: 1.6; color: #3f3f46;">Hi {first_name},</p>
            
            <p style="font-size: 16px; line-height: 1.6; color: #3f3f46;">
                Welcome to Benchside. You now have access to the most powerful AI workspace for pharmacology.
            </p>
            
            <p style="font-size: 16px; line-height: 1.6; color: #3f3f46;">
                But a powerful tool is useless if you don't know where to start. Here is your 3-step plan to save 5 hours this week:
            </p>
            
            <div style="margin: 32px 0;">
                <div style="margin-bottom: 24px;">
                    <h3 style="font-size: 18px; font-weight: 600; color: #18181b; margin-bottom: 8px;">Step 1: The Literature Review</h3>
                    <p style="font-size: 15px; color: #52525b; margin: 0; line-height: 1.5;">
                        Go to <strong>Deep Research Mode</strong> and type a complex query like: <em>"What are the current BACE1 inhibitors in Phase 3 trials?"</em> Watch it build a report with citations.
                    </p>
                </div>
                
                <div style="margin-bottom: 24px;">
                    <h3 style="font-size: 18px; font-weight: 600; color: #18181b; margin-bottom: 8px;">Step 2: The Data Extraction</h3>
                    <p style="font-size: 15px; color: #52525b; margin: 0; line-height: 1.5;">
                        Upload that 20-page protocol PDF you’ve been dreading reading. Ask Benchside: <em>"Extract the inclusion criteria and dosing schedule into a table."</em>
                    </p>
                </div>
                
                <div>
                    <h3 style="font-size: 18px; font-weight: 600; color: #18181b; margin-bottom: 8px;">Step 3: The Report</h3>
                    <p style="font-size: 15px; color: #52525b; margin: 0; line-height: 1.5;">
                        Take your findings and hit <strong>Generate Report</strong>. Benchside will format it for you instantly.
                    </p>
                </div>
            </div>
            
            <p style="font-size: 16px; line-height: 1.6; color: #3f3f46; font-weight: 500;">
                Don't let the tools sit there. Put them to work.
            </p>
            
            <div style="text-align: center; margin: 40px 0;">
                <a href="https://benchside.vercel.app/" style="display: inline-block; background: #18181b; color: #ffffff; padding: 14px 32px; border-radius: 12px; text-decoration: none; font-weight: 600; font-size: 16px;">Log in and Try Step 1 &rarr;</a>
            </div>
            
            <p style="margin-top: 30px; font-size: 16px; color: #3f3f46;">
                The Benchside Team
            </p>
            
            <div style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #e4e4e7; text-align: center;">
                <p style="font-size: 12px; color: #a1a1aa;">
                    © 2026 Benchside. AI-Powered Pharmacological Research Assistant.
                </p>
            </div>
        </div>
        """
        
        text = f"""You’re in. Here is your roadmap.

Hi {first_name},

Welcome to Benchside. You now have access to the most powerful AI workspace for pharmacology.

Here is your 3-step plan to save 5 hours this week:

Step 1: The Literature Review
Go to Deep Research Mode and type a complex query like: "What are the current BACE1 inhibitors in Phase 3 trials?"

Step 2: The Data Extraction
Upload that 20-page protocol PDF. Ask Benchside: "Extract the inclusion criteria and dosing schedule into a table."

Step 3: The Report
Take your findings and hit Generate Report.

Don't let the tools sit there. Put them to work.

Log in and Try Step 1: https://benchside.vercel.app/

The Benchside Team
        """
        
        return await self.send_email(to_email, subject, html, text)
