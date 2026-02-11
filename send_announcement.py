import asyncio
import os
import sys

# Add the current directory to python path to make imports work
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from dotenv import load_dotenv
load_dotenv('pharmgpt-backend.env')

from app.services.email import EmailService

# Email Content
SUBJECT = "Goodbye PharmGPT. Hello Benchside. 👋"

HTML_CONTENT = """
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px; color: #18181b;">
    
    <!-- Logo -->
    <div style="text-align: center; margin-bottom: 30px;">
        <img src="https://benchside.vercel.app/Benchside.png" alt="Benchside Logo" width="80" height="80" style="display: block; margin: 0 auto; width: 80px; height: 80px; outline: none; border: none; text-decoration: none;">
    </div>

    <!-- Header -->
    <div style="text-align: center; margin-bottom: 40px;">
        <h1 style="font-size: 24px; font-weight: 700; margin: 0; color: #18181b;">We realized something important:<br>You didn't just need a chatbot.</h1>
    </div>

    <!-- Body -->
    <div style="font-size: 16px; line-height: 1.6; color: #3f3f46;">
        <p>Hi there,</p>
        
        <p>When we started PharmGPT, the goal was simple: answer pharmacology queries fast. But as many of you started using it, we saw that your needs were bigger than just "Q&A."</p>
        
        <p>You needed to review literature, analyze complex lab images, and write reports. You didn't need a chatbot; you needed a research partner.</p>
        
        <p style="font-weight: 500; color: #18181b; font-size: 18px; margin: 25px 0;">So, we evolved. PharmGPT is officially becoming Benchside.</p>
        
        <p>We changed the name because we changed the mission. We are building a complete digital workspace that lives right where you work—at your benchside.</p>
        
        <h3 style="font-size: 18px; font-weight: 600; margin-top: 30px; margin-bottom: 15px; color: #18181b;">Here is how your new workspace helps you win the day:</h3>
        
        <ul style="list-style-type: none; padding: 0; margin-top: 20px;">
            <li style="margin-bottom: 12px; padding-left: 24px; position: relative;">
                <span style="position: absolute; left: 0;">🔬</span>
                <strong>Stop drowning in tabs:</strong> Use <strong>Deep Research Mode</strong> to review PubMed, clinical trials, and journals in one click.
            </li>
            <li style="margin-bottom: 12px; padding-left: 24px; position: relative;">
                <span style="position: absolute; left: 0;">📄</span>
                <strong>Chat with your data:</strong> Upload PDFs and protocols. Our <strong>Document Intelligence</strong> doesn't just read them; it extracts the insights you need instantly.
            </li>
            <li style="margin-bottom: 12px; padding-left: 24px; position: relative;">
                <span style="position: absolute; left: 0;">👁️</span>
                <strong>Eyes on the science:</strong> Upload molecular structures or lab charts. Our <strong>Visual Analysis</strong> engine (powered by Pixtral) interprets them in seconds.
            </li>
            <li style="margin-bottom: 12px; padding-left: 24px; position: relative;">
                <span style="position: absolute; left: 0;">⚡</span>
                <strong>Automate the boring stuff:</strong> Turn raw data into formatted <strong>Lab Reports</strong> automatically.
            </li>
        </ul>

        <p style="margin-top: 25px;">Your account and history are waiting for you. The only difference is that now, you have a much more powerful engine under the hood.</p>

        <div style="text-align: center; margin: 40px 0;">
            <a href="https://benchside.vercel.app/" style="display: inline-block; background: #18181b; color: #ffffff; padding: 14px 32px; border-radius: 12px; text-decoration: none; font-weight: 600; font-size: 16px;">Explore the New Benchside &rarr;</a>
        </div>
        
        <p style="margin-top: 30px;">
            Here’s to finding cures faster,<br>
            <strong>The Benchside Team</strong>
        </p>
    </div>
    
    <!-- Footer -->
    <div style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #e4e4e7; text-align: center;">
        <p style="font-size: 12px; color: #a1a1aa;">
            © 2026 Benchside. AI-Powered Pharmacological Research Assistant.<br>
            <a href="https://benchside.vercel.app/" style="color: #a1a1aa; text-decoration: none;">benchside.vercel.app</a>
        </p>
    </div>
</div>
"""

TEXT_CONTENT = """
Goodbye PharmGPT. Hello Benchside.

We realized something important: You didn't just need a chatbot.

Hi there,

When we started PharmGPT, the goal was simple: answer pharmacology queries fast. But as many of you started using it, we saw that your needs were bigger than just "Q&A."

You needed to review literature, analyze complex lab images, and write reports. You didn't need a chatbot; you needed a research partner.

So, we evolved. PharmGPT is officially becoming Benchside.

We changed the name because we changed the mission. We are building a complete digital workspace that lives right where you work—at your benchside.

Here is how your new workspace helps you win the day:

- Stop drowning in tabs: Use Deep Research Mode to review PubMed, clinical trials, and journals in one click.
- Chat with your data: Upload PDFs and protocols. Our Document Intelligence doesn't just read them; it extracts the insights you need instantly.
- Eyes on the science: Upload molecular structures or lab charts. Our Visual Analysis engine (powered by Pixtral) interprets them in seconds.
- Automate the boring stuff: Turn raw data into formatted Lab Reports automatically.

Your account and history are waiting for you. The only difference is that now, you have a much more powerful engine under the hood.

Explore the New Benchside: https://benchside.vercel.app/

Here’s to finding cures faster,

The Benchside Team
"""

async def main():
    if len(sys.argv) < 2:
        print("Usage: python send_announcement.py <email>")
        return

    to_email = sys.argv[1]
    print(f"🚀 Preparing to send announcement to {to_email}...")
    
    email_service = EmailService()
    
    success = await email_service.send_email(
        to_email=to_email,
        subject=SUBJECT,
        html_content=HTML_CONTENT,
        text_content=TEXT_CONTENT
    )
    
    if success:
        print("\n✅ Announcement sent successfully!")
    else:
        print("\n❌ Failed to send announcement.")

if __name__ == "__main__":
    asyncio.run(main())
