import asyncio
import os
import sys

# Add the parent directory to sys.path to allow importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.services.email import EmailService
from app.core.database import db

async def main():
    print("🚀 Starting PharmGPT 2.0 Announcement Email Campaign")
    
    # Initialize DB (needed for potentially fetching users in real run)
    await db.test_connection()
    
    email_service = EmailService()
    
    # Test Recipient
    test_email = "odunewutolu2@gmail.com"
    first_name = "Toluwanimi"
    
    print(f"📧 Sending test email to: {test_email}")
    
    # Email HTML Content
    subject = "🚀 Introducing PharmGPT 2.0: Higher Precision Pharmacological AI"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&display=swap');
            
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; 
                line-height: 1.6; 
                color: #18181B; 
                background-color: #FDFCF8;
                margin: 0;
                padding: 0;
            }}
            .container {{ 
                max-width: 600px; 
                margin: 40px auto; 
                background: #ffffff; 
                border: 1px solid #E4E4E7; 
                border-radius: 20px;
                overflow: hidden;
            }}
            .header {{ 
                padding: 60px 40px 40px; 
                text-align: center; 
                border-bottom: 1px solid #F4F4F5;
            }}
            .header h1 {{ 
                font-family: 'Fraunces', serif;
                font-size: 32px;
                font-weight: 500;
                margin: 0;
                color: #18181B;
                letter-spacing: -0.02em;
            }}
            .header p {{
                color: #71717A;
                margin: 10px 0 0 0;
                font-size: 16px;
            }}
            .content {{ 
                padding: 40px; 
            }}
            .section-title {{
                font-family: 'Fraunces', serif;
                font-size: 20px;
                font-weight: 500;
                margin-bottom: 20px;
                color: #18181B;
            }}
            .feature-list {{ 
                margin: 25px 0;
                padding: 0;
                list-style: none;
            }}
            .feature-item {{ 
                margin-bottom: 20px;
                padding: 20px;
                background: #FDFCF8;
                border: 1px solid #E4E4E7;
                border-radius: 12px;
                transition: border-color 0.2s;
            }}
            .feature-item strong {{
                display: block;
                color: #6366f1;
                margin-bottom: 4px;
                font-size: 15px;
            }}
            .feature-item span {{
                color: #71717A;
                font-size: 14px;
                line-height: 1.5;
            }}
            .btn-wrapper {{
                text-align: center;
                margin-top: 40px;
            }}
            .btn {{ 
                display: inline-block; 
                background: #6366f1; 
                color: #ffffff !important; 
                padding: 14px 32px; 
                text-decoration: none; 
                border-radius: 100px; 
                font-weight: 500;
                font-size: 16px;
                transition: opacity 0.2s;
            }}
            .footer {{ 
                text-align: center; 
                padding: 40px; 
                background: #FDFCF8;
                border-top: 1px solid #F4F4F5;
                font-size: 12px; 
                color: #A1A1AA; 
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>PharmGPT 2.0 is Here</h1>
                <p>Voice, Vision, and Deep Research.</p>
            </div>
            <div class="content">
                <p>Hi {first_name},</p>
                <p>We've completely reimagined <strong>PharmGPT</strong> to be faster, smarter, and way more powerful. The new 2.0 update brings cutting-edge AI features directly to your fingertips.</p>
                
                <h3 class="section-title">✨ What's New?</h3>
                
                <div class="feature-list">
                    <div class="feature-item">
                        <strong>🎙️ Voice Mode</strong>
                        <span>Speak directly to the AI with real-time transcription.</span>
                    </div>
                    <div class="feature-item">
                        <strong>🧠 Deep Research</strong>
                        <span>Autonomous web research for complex clinical queries.</span>
                    </div>
                    <div class="feature-item">
                        <strong>👁️ Enhanced Vision</strong>
                        <span>Upload lab reports & images for instant analysis.</span>
                    </div>
                    <div class="feature-item">
                        <strong>🌐 Multi-language</strong>
                        <span>Now fluent in Spanish, French, German, and more.</span>
                    </div>
                    <div class="feature-item">
                        <strong>🎨 New UI</strong>
                        <span>A stunning, modern interface with dark mode.</span>
                    </div>
                    <div class="feature-item">
                        <strong>👤 User Profiles</strong>
                        <span>Customize your experience and settings.</span>
                    </div>
                </div>
                
                <p style="text-align: center; color: #71717A; font-size: 14px; margin-top: 40px;">
                    Experience the future of pharmacological AI today.
                </p>
                
                <div class="btn-wrapper">
                    <a href="https://pharmgpt.vercel.app/login?ref=email_v2&confetti=true" class="btn">Try PharmGPT 2.0 Now →</a>
                </div>
            </div>
            <div class="footer">
                <p>© 2026 PharmGPT. All rights reserved.<br>
                You received this because you are a registered user.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    success = await email_service.send_email(
        to_email=test_email,
        subject=subject,
        html_content=html_content
    )
    
    if success:
        print("✅ Announcement email sent successfully!")
    else:
        print("❌ Failed to send announcement email.")

if __name__ == "__main__":
    asyncio.run(main())
