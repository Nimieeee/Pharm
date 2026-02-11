import asyncio
import os
import sys

# Add the current directory to python path to make imports work
sys.path.append(os.getcwd())

from app.services.email import EmailService

async def main():
    if len(sys.argv) < 2:
        print("Usage: python send_welcome.py <email>")
        return

    to_email = sys.argv[1]
    print(f"🚀 Preparing to send Welcome/Roadmap email to {to_email}...")
    
    email_service = EmailService()
    
    # Send welcome email using the recently added method
    success = email_service.send_welcome_email(to_email, first_name="Tolu")
    
    if success:
        print("\n✅ Welcome email sent successfully!")
    else:
        print("\n❌ Failed to send welcome email.")

if __name__ == "__main__":
    asyncio.run(main())
