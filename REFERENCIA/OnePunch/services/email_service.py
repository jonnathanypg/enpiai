import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# from sendgrid import SendGridAPIClient # Removed to avoid dependency error
# from sendgrid.helpers.mail import Mail
from models.channel import Channel, ChannelType, ChannelStatus

logger = logging.getLogger(__name__)

from email.mime.application import MIMEApplication
import base64

class EmailService:
    def send_email(self, company_id, to_email, subject, body, attachments=None):
        """
        Send an email using the company's configured email channel.
        attachments: List of dicts {'name': str, 'content': bytes, 'type': str}
        """
        # Preventive rollback for stale connections
        try:
            from extensions import db
            db.session.rollback()
        except Exception:
            pass

        # Find connection
        channel = Channel.query.filter_by(
            company_id=company_id,
            type=ChannelType.EMAIL,
            status=ChannelStatus.CONNECTED
        ).first()
        
        if not channel:
            logger.warning(f"No connected email channel found for company {company_id}")
            return {'success': False, 'message': 'No email channel connected'}
            
        credentials = channel.credentials or {}
        provider = credentials.get('provider')
        
        try:
            if provider == 'sendgrid':
                return self._send_via_sendgrid(credentials, channel.email_address, to_email, subject, body, attachments)
            elif provider == 'smtp':
                return self._send_via_smtp(credentials, channel.email_address, to_email, subject, body, attachments)
            else:
                 return {'success': False, 'message': f'Unknown email provider: {provider}'}
                 
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return {'success': False, 'message': str(e)}

    def _send_via_sendgrid(self, credentials, from_email, to_email, subject, body, attachments=None):
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
        except ImportError:
            return {'success': False, 'message': 'SendGrid package not installed. Please install it or use SMTP.'}

        api_key = credentials.get('api_key')
        if not api_key:
             return {'success': False, 'message': 'SendGrid API Key missing'}
             
        message = Mail(
            from_email=from_email or credentials.get('from_email'),
            to_emails=to_email,
            subject=subject,
            html_content=body
        )
        
        if attachments:
            for att in attachments:
                encoded_file = base64.b64encode(att['content']).decode()
                attachedFile = Attachment(
                    FileContent(encoded_file),
                    FileName(att['name']),
                    FileType(att.get('type', 'application/pdf')),
                    Disposition('attachment')
                )
                message.add_attachment(attachedFile)
        
        try:
            sg = SendGridAPIClient(api_key)
            response = sg.send(message)
            if response.status_code in [200, 201, 202]:
                return {'success': True, 'message': f'Email sent to {to_email}'}
            else:
                return {'success': False, 'message': f'SendGrid error: {response.status_code}'}
        except Exception as e:
            raise e

    def _send_via_smtp(self, credentials, from_email, to_email, subject, body, attachments=None):
        smtp_host = credentials.get('smtp_host')
        smtp_port = int(credentials.get('smtp_port', 465))
        encryption = credentials.get('smtp_encryption', 'ssl')
        username = credentials.get('email_user')
        password = credentials.get('email_pass')
        sender_email = from_email or credentials.get('from_email') or username
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        if attachments:
            for att in attachments:
                part = MIMEApplication(att['content'], Name=att['name'])
                part['Content-Disposition'] = f'attachment; filename="{att["name"]}"'
                msg.attach(part)
        
        context = ssl.create_default_context()
        
        try:
            if encryption == 'ssl':
                with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
                    server.login(username, password)
                    server.sendmail(sender_email, to_email, msg.as_string())
            elif encryption == 'tls':
                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    server.starttls(context=context)
                    server.login(username, password)
                    server.sendmail(sender_email, to_email, msg.as_string())
            else:
                 with smtplib.SMTP(smtp_host, smtp_port) as server:
                    server.login(username, password)
                    server.sendmail(sender_email, to_email, msg.as_string())
            
            return {'success': True, 'message': f'Email sent to {to_email}'}
            
        except Exception as e:
            raise e
