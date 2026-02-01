"""
Scheduler Service for Background Tasks
Runs periodic jobs like sending re-engagement emails to inactive users.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.core.database import get_db
from app.services.email import EmailService


class SchedulerService:
    """Background task scheduler for PharmGPT"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.email_service = EmailService()
        self._is_running = False
    
    def start(self):
        """Start the scheduler"""
        if self._is_running:
            print("⚠️ Scheduler already running")
            return
            
        # Add job: Send re-engagement emails daily at 9 AM UTC
        self.scheduler.add_job(
            self.send_reengagement_emails,
            CronTrigger(hour=9, minute=0),  # 9:00 AM UTC daily
            id="reengagement_emails",
            name="Send re-engagement emails to inactive users",
            replace_existing=True
        )
        
        self.scheduler.start()
        self._is_running = True
        print("✅ Scheduler started - Re-engagement emails scheduled for 9 AM UTC daily")
    
    def stop(self):
        """Stop the scheduler"""
        if self._is_running:
            self.scheduler.shutdown(wait=False)
            self._is_running = False
            print("🛑 Scheduler stopped")
    
    async def send_reengagement_emails(self):
        """
        Find users inactive for 30+ days and send them a re-engagement email.
        Only sends one email per user (tracks via reengagement_email_sent_at).
        """
        print("📧 Running re-engagement email job...")
        
        try:
            db = get_db()
            
            # Calculate the cutoff date (30 days ago)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            cutoff_iso = cutoff_date.isoformat()
            
            # Query for inactive users who haven't received a re-engagement email yet
            # OR haven't received one in the last 90 days (to allow follow-up)
            result = db.table("users").select(
                "id", "email", "first_name", "last_login", "reengagement_email_sent_at"
            ).or_(
                f"last_login.lt.{cutoff_iso},last_login.is.null"
            ).or_(
                "reengagement_email_sent_at.is.null,reengagement_email_sent_at.lt." + (datetime.utcnow() - timedelta(days=90)).isoformat()
            ).eq("is_active", True).execute()
            
            inactive_users = result.data if result.data else []
            
            if not inactive_users:
                print("✅ No inactive users found for re-engagement")
                return
            
            print(f"📋 Found {len(inactive_users)} inactive users")
            
            sent_count = 0
            for user in inactive_users:
                try:
                    email = user.get("email")
                    first_name = user.get("first_name") or "there"
                    user_id = user.get("id")
                    
                    if not email:
                        continue
                    
                    # Send re-engagement email
                    success = self.email_service.send_reengagement_email(
                        to_email=email,
                        first_name=first_name
                    )
                    
                    if success:
                        # Update the user record to mark email as sent
                        db.table("users").update({
                            "reengagement_email_sent_at": datetime.utcnow().isoformat()
                        }).eq("id", user_id).execute()
                        
                        sent_count += 1
                        print(f"  ✅ Sent to: {email}")
                    else:
                        print(f"  ❌ Failed to send to: {email}")
                        
                except Exception as user_error:
                    print(f"  ⚠️ Error processing user {user.get('email')}: {user_error}")
                    continue
            
            print(f"📧 Re-engagement job complete: {sent_count}/{len(inactive_users)} emails sent")
            
        except Exception as e:
            print(f"❌ Re-engagement email job failed: {e}")
            import traceback
            traceback.print_exc()
    
    async def trigger_reengagement_now(self):
        """Manually trigger re-engagement emails (for testing)"""
        await self.send_reengagement_emails()


# Global scheduler instance
scheduler_service = SchedulerService()


def start_scheduler():
    """Start the global scheduler"""
    scheduler_service.start()


def stop_scheduler():
    """Stop the global scheduler"""
    scheduler_service.stop()
