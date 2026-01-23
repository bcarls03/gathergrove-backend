# app/services/sms.py
"""
SMS service for sending event invitations via Twilio.

Design principles:
- SMS is for NON-USERS only (automatic routing in invitation endpoint)
- All SMS sends are logged for debugging and rate limiting
- Graceful fallback if Twilio is not configured
"""

import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SMSService:
    """
    Handles SMS delivery via Twilio.
    
    Environment variables required:
    - TWILIO_ACCOUNT_SID
    - TWILIO_AUTH_TOKEN  
    - TWILIO_PHONE_NUMBER
    """
    
    def __init__(self):
        self.enabled = all([
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN"),
            os.getenv("TWILIO_PHONE_NUMBER")
        ])
        
        if self.enabled:
            try:
                from twilio.rest import Client
                self.client = Client(
                    os.getenv("TWILIO_ACCOUNT_SID"),
                    os.getenv("TWILIO_AUTH_TOKEN")
                )
                self.from_number = os.getenv("TWILIO_PHONE_NUMBER")
                logger.info("SMS service initialized with Twilio")
            except ImportError:
                logger.warning("Twilio SDK not installed. SMS disabled.")
                self.enabled = False
        else:
            logger.warning("Twilio credentials not configured. SMS disabled.")
            self.enabled = False
    
    
    def send_event_invitation(
        self,
        to_number: str,
        event_title: str,
        host_name: str,
        event_datetime: str,
        rsvp_link: str
    ) -> tuple[bool, Optional[str]]:
        """
        Send event invitation via SMS.
        
        Args:
            to_number: E.164 format phone number (e.g., +15551234567)
            event_title: Event title
            host_name: Name of host (e.g., "The Miller Family")
            event_datetime: Formatted datetime (e.g., "Sat, Jan 25 at 3:00 PM")
            rsvp_link: Full RSVP URL
            
        Returns:
            (success: bool, message_sid: str | None)
        """
        if not self.enabled:
            logger.warning(f"SMS disabled - would send to {to_number}: {event_title}")
            return False, None
        
        # Format message
        message = self._format_invitation_message(
            event_title,
            host_name,
            event_datetime,
            rsvp_link
        )
        
        try:
            result = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            logger.info(f"SMS sent to {to_number}: {result.sid}")
            return True, result.sid
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_number}: {str(e)}")
            return False, None
    
    
    def send_event_reminder(
        self,
        to_number: str,
        event_title: str,
        rsvp_link: str
    ) -> tuple[bool, Optional[str]]:
        """
        Send 24h reminder for an event.
        
        Returns:
            (success: bool, message_sid: str | None)
        """
        if not self.enabled:
            logger.warning(f"SMS disabled - would send reminder to {to_number}")
            return False, None
        
        message = f"""Reminder: {event_title}

Happening tomorrow!

View details: {rsvp_link}

Reply STOP to opt out"""
        
        try:
            result = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            logger.info(f"Reminder sent to {to_number}: {result.sid}")
            return True, result.sid
            
        except Exception as e:
            logger.error(f"Failed to send reminder to {to_number}: {str(e)}")
            return False, None
    
    
    def send_event_update(
        self,
        to_number: str,
        event_title: str,
        update_text: str,
        rsvp_link: str
    ) -> tuple[bool, Optional[str]]:
        """
        Notify about event changes (time, location, cancellation).
        
        Returns:
            (success: bool, message_sid: str | None)
        """
        if not self.enabled:
            logger.warning(f"SMS disabled - would send update to {to_number}")
            return False, None
        
        message = f"""Update: {event_title}

{update_text}

View details: {rsvp_link}

Reply STOP to opt out"""
        
        try:
            result = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            logger.info(f"Update sent to {to_number}: {result.sid}")
            return True, result.sid
            
        except Exception as e:
            logger.error(f"Failed to send update to {to_number}: {str(e)}")
            return False, None
    
    
    def _format_invitation_message(
        self,
        event_title: str,
        host_name: str,
        event_datetime: str,
        rsvp_link: str
    ) -> str:
        """Format the invitation SMS message"""
        return f"""{host_name} invited you to: {event_title}

📅 {event_datetime}

View details & RSVP:
{rsvp_link}

Reply STOP to opt out"""


# Global instance
sms_service = SMSService()
