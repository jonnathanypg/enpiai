"""
Email Service - SMTP email sending with template support.
Migration Path: Email sending can be replaced by P2P message routing.
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

logger = logging.getLogger(__name__)


class EmailService:
    """SMTP-based email sending service"""

    def send(self, to_email, subject, body_html, body_text=None, from_email=None):
        """
        Send an email via SMTP.

        Args:
            to_email: recipient email
            subject: email subject
            body_html: HTML body
            body_text: plain text fallback (auto-generated if None)
            from_email: sender email (defaults to config)

        Returns:
            bool: True if sent successfully
        """
        smtp_host = current_app.config.get('SMTP_HOST', '')
        smtp_port = current_app.config.get('SMTP_PORT', 587)
        smtp_user = current_app.config.get('SMTP_USER', '')
        smtp_password = current_app.config.get('SMTP_PASSWORD', '')
        smtp_from = from_email or current_app.config.get('SMTP_FROM_EMAIL', smtp_user)
        use_tls = current_app.config.get('SMTP_USE_TLS', True)

        if not smtp_host or not smtp_user:
            logger.warning("SMTP not configured, email not sent")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = smtp_from
            msg['To'] = to_email

            # Plain text fallback
            if body_text:
                msg.attach(MIMEText(body_text, 'plain'))

            # HTML body
            msg.attach(MIMEText(body_html, 'html'))

            # Connect and send
            if use_tls:
                server = smtplib.SMTP(smtp_host, smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port)

            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_from, to_email, msg.as_string())
            server.quit()

            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Email send error to {to_email}: {e}")
            return False

    def send_wellness_report(self, to_email, distributor_name, evaluation_data):
        """Send a wellness evaluation report email"""
        subject = f"Tu Evaluación de Bienestar - {distributor_name}"

        bmi = evaluation_data.get('bmi', 'N/A')
        bmi_cat = evaluation_data.get('bmi_category', '')
        goal = evaluation_data.get('primary_goal', 'bienestar general')

        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #4CAF50;">🌿 Tu Evaluación de Bienestar</h2>
            <p>¡Hola! Gracias por completar tu evaluación de bienestar con <strong>{distributor_name}</strong>.</p>

            <div style="background: #f9f9f9; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h3>📊 Resumen</h3>
                <ul>
                    <li><strong>IMC:</strong> {bmi} ({bmi_cat})</li>
                    <li><strong>Objetivo principal:</strong> {goal}</li>
                </ul>
            </div>

            <p>Tu distribuidor se pondrá en contacto contigo pronto con recomendaciones personalizadas.</p>

            <p style="color: #888; font-size: 12px;">
                Este es un correo automatizado de la plataforma {distributor_name}.
            </p>
        </body>
        </html>
        """

        return self.send(to_email, subject, body_html)


# Singleton instance
email_service = EmailService()
