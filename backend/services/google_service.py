"""
Google Service - Google Calendar and Gmail integration.
Uses Google API Python client for authenticated operations.

Migration Path: Calendar and Gmail APIs remain as external integrations.
Scheduling requires explicit user confirmation (GEMINI.md Rule B.1).
"""
import logging
import os
import base64
import json
from datetime import datetime, timedelta
from flask import current_app

logger = logging.getLogger(__name__)


class GoogleService:
    """Google Calendar and Gmail integration service"""

    def _get_credentials(self, distributor=None):
        """
        Get Google API credentials.
        Priority: distributor-specific > app-level config.

        Returns credentials object or None.
        """
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request

            # Check distributor-specific credentials first
            if distributor and distributor.google_credentials:
                # Stored as JSON dict in the user model
                creds_data = distributor.google_credentials if isinstance(
                    distributor.google_credentials, dict
                ) else json.loads(distributor.google_credentials)

                creds = Credentials.from_authorized_user_info(creds_data)

                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())

                return creds

            # App-level: from GOOGLE_CREDENTIALS_JSON env (base64)
            creds_b64 = current_app.config.get('GOOGLE_CREDENTIALS_JSON', '')
            if creds_b64:
                creds_json = json.loads(base64.b64decode(creds_b64))
                return Credentials.from_authorized_user_info(creds_json)

            logger.warning("No Google credentials available")
            return None

        except Exception as e:
            logger.error(f"Google credentials error: {e}")
            return None

    # -------------------------------------------------------------------
    # Calendar
    # -------------------------------------------------------------------
    def check_availability(self, distributor, date_str, timezone='America/Guayaquil'):
        """
        Check calendar availability for a date.

        Args:
            distributor: Distributor model instance
            date_str: date string (YYYY-MM-DD)
            timezone: timezone string

        Returns:
            list of available time slots
        """
        try:
            from googleapiclient.discovery import build

            creds = self._get_credentials(distributor)
            if not creds:
                return {'error': 'Google Calendar not connected'}

            service = build('calendar', 'v3', credentials=creds)

            # Parse date
            target_date = datetime.strptime(date_str, '%Y-%m-%d')
            time_min = target_date.replace(hour=8, minute=0).isoformat() + 'Z'
            time_max = target_date.replace(hour=18, minute=0).isoformat() + 'Z'

            # Get events for the day
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime',
                timeZone=timezone
            ).execute()

            events = events_result.get('items', [])

            # Calculate available slots (30-min intervals)
            busy_times = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                busy_times.append({'start': start, 'end': end})

            # Generate 30-min slots between 8:00 and 18:00
            available_slots = []
            current_time = target_date.replace(hour=8, minute=0)
            end_of_day = target_date.replace(hour=18, minute=0)

            while current_time < end_of_day:
                slot_end = current_time + timedelta(minutes=30)
                slot_str = current_time.strftime('%H:%M')

                # Check if slot is free (simplified check)
                is_free = True
                for busy in busy_times:
                    # Basic overlap check
                    busy_start = datetime.fromisoformat(busy['start'].replace('Z', ''))
                    busy_end = datetime.fromisoformat(busy['end'].replace('Z', ''))
                    if current_time < busy_end and slot_end > busy_start:
                        is_free = False
                        break

                if is_free:
                    available_slots.append(slot_str)

                current_time = slot_end

            return {
                'date': date_str,
                'available_slots': available_slots,
                'busy_count': len(events)
            }

        except Exception as e:
            logger.error(f"Calendar availability check error: {e}")
            return {'error': str(e)}

    def create_event(self, distributor, title, start_datetime, duration_minutes=30,
                     description=None, attendee_email=None, timezone='America/Guayaquil'):
        """
        Create a calendar event.
        NOTE: This must only be called after explicit user confirmation (GEMINI.md Rule).

        Returns:
            dict with event ID and link
        """
        try:
            from googleapiclient.discovery import build

            creds = self._get_credentials(distributor)
            if not creds:
                return {'error': 'Google Calendar not connected'}

            service = build('calendar', 'v3', credentials=creds)

            end_datetime = start_datetime + timedelta(minutes=duration_minutes)

            event = {
                'summary': title,
                'description': description or '',
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': timezone,
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': timezone,
                },
            }

            if attendee_email:
                event['attendees'] = [{'email': attendee_email}]

            created_event = service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all' if attendee_email else 'none'
            ).execute()

            logger.info(f"Calendar event created: {created_event.get('id')}")

            return {
                'event_id': created_event.get('id'),
                'html_link': created_event.get('htmlLink'),
                'status': 'created'
            }

        except Exception as e:
            logger.error(f"Calendar event creation error: {e}")
            return {'error': str(e)}

    # -------------------------------------------------------------------
    # Gmail
    # -------------------------------------------------------------------
    def send_email(self, distributor, to_email, subject, body_html):
        """Send email via Gmail API"""
        try:
            from googleapiclient.discovery import build
            from email.mime.text import MIMEText

            creds = self._get_credentials(distributor)
            if not creds:
                return {'error': 'Gmail not connected'}

            service = build('gmail', 'v1', credentials=creds)

            message = MIMEText(body_html, 'html')
            message['to'] = to_email
            message['subject'] = subject

            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode('utf-8')

            result = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            logger.info(f"Gmail sent to {to_email}, ID: {result.get('id')}")
            return {'message_id': result.get('id'), 'status': 'sent'}

        except Exception as e:
            logger.error(f"Gmail send error: {e}")
            return {'error': str(e)}


# Singleton instance
google_service = GoogleService()
