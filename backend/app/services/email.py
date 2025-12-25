
import os
import resend
from typing import List, Optional

class EmailService:
    def __init__(self):
        api_key = os.getenv("RESEND_API_KEY")
        if not api_key:
            print("⚠️ RESEND_API_KEY not found. Emails will be logged only.")
            self.enabled = False
        else:
            resend.api_key = api_key
            self.enabled = True
        
        self.from_email = os.getenv("EMAIL_FROM", "onboarding@resend.dev")

    def send_verification_email(self, to_email: str, code: str):
        """Send verification code via email"""
        if not self.enabled:
            print(f"📧 [MOCK EMAIL] To: {to_email} | Code: {code}")
            return True

        try:
            params = {
                "from": self.from_email,
                "to": [to_email],
                "subject": "Verify your PharmGPT Account",
                "html": f"""
                <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2>Welcome to PharmGPT!</h2>
                    <p>Please use the following code to verify your email address:</p>
                    <div style="background: #f4f4f5; padding: 20px; text-align: center; border-radius: 12px; margin: 24px 0;">
                        <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #18181b;">{code}</span>
                    </div>
                    <p>If you didn't request this code, you can safely ignore this email.</p>
                </div>
                """
            }
            
            email = resend.Emails.send(params)
            print(f"✅ Email sent to {to_email}: {email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
