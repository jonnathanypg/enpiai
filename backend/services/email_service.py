"""
Email Service - SMTP email sending with branded, localized HTML templates.
Handles all platform notification emails in EN, ES, and PT.
Migration Path: Email sending can be replaced by P2P message routing.
"""
import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from flask import current_app

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Email Translations (EN, ES, PT)
# ──────────────────────────────────────────────

EMAIL_STRINGS = {
    'en': {
        # Base template
        'brand_subtitle': 'Intelligent Business Automation',
        'footer_rights': '© 2026 EnpiAI by WEBLIFETECH. All rights reserved.',

        # Welcome
        'welcome_subject': 'Welcome to EnpiAI! 🎉',
        'welcome_preheader': 'Your EnpiAI account is ready',
        'welcome_title': 'Welcome to EnpiAI! 🎉',
        'welcome_greeting': 'Hi <strong>{name}</strong>,',
        'welcome_body': 'Your account has been successfully created. You\'re now ready to automate your Herbalife business with AI-powered tools.',
        'welcome_business': 'Business',
        'welcome_email': 'Email',
        'welcome_status': 'Status',
        'welcome_status_active': 'Active',
        'welcome_next': 'Here\'s what you can do next:',
        'welcome_step_1': 'Connect your WhatsApp channel',
        'welcome_step_2': 'Upload documents to train your AI agent',
        'welcome_step_3': 'Share your wellness evaluation link',
        'welcome_step_4': 'Activate a subscription plan',
        'welcome_cta': 'Go to Dashboard →',

        # Google welcome
        'google_welcome_body': 'Your account was automatically created via Google Sign-In. You can start using the platform immediately.',
        'google_auth_method': 'Auth Method',
        'google_get_started': 'Get started by connecting your messaging channels and uploading product documents to train your AI agent.',

        # Subscription activated
        'sub_activated_subject': '✅ Subscription Activated — EnpiAI',
        'sub_activated_preheader': 'Your subscription is now active',
        'sub_activated_title': 'Subscription Activated! ✅',
        'sub_activated_body': 'Great news! Your subscription payment has been <strong>confirmed</strong>. All premium features are now fully unlocked.',
        'sub_activated_account': 'Account',
        'sub_activated_subscription': 'Subscription',
        'sub_activated_payment': 'Payment',
        'sub_activated_payment_value': 'Confirmed via dLocal Go',
        'sub_activated_enjoy': 'You now have full access to all automation, CRM, and AI tools. Enjoy! 🚀',

        # Subscription deactivated
        'sub_deactivated_subject': '⚠️ Subscription Update — EnpiAI',
        'sub_deactivated_preheader': 'Your subscription status has changed',
        'sub_deactivated_title': 'Subscription Update ⚠️',
        'sub_deactivated_body': 'We wanted to let you know that your subscription status has changed to <strong>inactive</strong>.',
        'sub_deactivated_reason': 'Reason',
        'sub_deactivated_restore': 'To restore access to all features, please update your payment method or contact the platform administrator.',
        'sub_deactivated_cta': 'Reactivate Subscription →',

        # New lead
        'lead_subject': '🎯 New Lead: {name} — EnpiAI',
        'lead_preheader': 'New lead captured: {name}',
        'lead_title': 'New Lead Captured! 🎯',
        'lead_body': 'A new prospect has been added to your CRM.',
        'lead_name': 'Name',
        'lead_email': 'Email',
        'lead_phone': 'Phone',
        'lead_source': 'Source',
        'lead_followup': 'Check your contacts for more details and follow up promptly for the best conversion results.',
        'lead_cta': 'View Contacts →',

        # Wellness evaluation
        'wellness_subject': '🌿 New Wellness Evaluation — EnpiAI',
        'wellness_preheader': 'New wellness evaluation from {name}',
        'wellness_title': 'New Wellness Evaluation! 🌿',
        'wellness_body': 'A prospect has just completed a wellness evaluation through your personalized link.',
        'wellness_prospect': 'Prospect',
        'wellness_anonymous': 'Anonymous',
        'wellness_bmi': 'BMI',
        'wellness_goal': 'Goal',
        'wellness_not_specified': 'Not specified',
        'wellness_review': 'Review the evaluation and generate a personalized PDF report to share with your prospect.',
        'wellness_cta': 'View Evaluations →',

        # Courtesy account
        'courtesy_subject': '🎁 Your EnpiAI Courtesy Account — EnpiAI',
        'courtesy_preheader': 'Your courtesy account credentials',
        'courtesy_title': 'Your EnpiAI Account is Ready! 🎁',
        'courtesy_body': 'A courtesy account has been created for you on the EnpiAI platform. You have full access to all features — no payment required.',
        'courtesy_email': 'Email',
        'courtesy_password': 'Temp Password',
        'courtesy_status': 'Status',
        'courtesy_status_value': 'Courtesy — Active',
        'courtesy_warning': '⚠️ Please change your password after your first login for security purposes.',
        'courtesy_cta': 'Log In Now →',

        # Wellness report (to prospect)
        'report_title': 'Your Wellness Evaluation 🌿',
        'report_thanks': 'Thank you for completing your wellness evaluation with <strong>{distributor}</strong>.',
        'report_bmi': 'BMI',
        'report_goal': 'Primary Goal',
        'report_followup': 'Your distributor will be in touch soon with personalized recommendations.',
    },

    'es': {
        'brand_subtitle': 'Automatización Empresarial Inteligente',
        'footer_rights': '© 2026 EnpiAI por WEBLIFETECH. Todos los derechos reservados.',

        'welcome_subject': '¡Bienvenido a EnpiAI! 🎉',
        'welcome_preheader': 'Tu cuenta de EnpiAI está lista',
        'welcome_title': '¡Bienvenido a EnpiAI! 🎉',
        'welcome_greeting': 'Hola <strong>{name}</strong>,',
        'welcome_body': 'Tu cuenta ha sido creada exitosamente. Ya estás listo para automatizar tu negocio Herbalife con herramientas potenciadas por IA.',
        'welcome_business': 'Negocio',
        'welcome_email': 'Correo',
        'welcome_status': 'Estado',
        'welcome_status_active': 'Activo',
        'welcome_next': 'Esto es lo que puedes hacer a continuación:',
        'welcome_step_1': 'Conectar tu canal de WhatsApp',
        'welcome_step_2': 'Subir documentos para entrenar a tu agente IA',
        'welcome_step_3': 'Compartir tu enlace de evaluación de bienestar',
        'welcome_step_4': 'Activar un plan de suscripción',
        'welcome_cta': 'Ir al Panel →',

        'google_welcome_body': 'Tu cuenta fue creada automáticamente a través de Google Sign-In. Puedes empezar a usar la plataforma inmediatamente.',
        'google_auth_method': 'Método de autenticación',
        'google_get_started': 'Comienza conectando tus canales de mensajería y subiendo documentos de productos para entrenar a tu agente IA.',

        'sub_activated_subject': '✅ Suscripción Activada — EnpiAI',
        'sub_activated_preheader': 'Tu suscripción está activa',
        'sub_activated_title': '¡Suscripción Activada! ✅',
        'sub_activated_body': '¡Excelentes noticias! Tu pago de suscripción ha sido <strong>confirmado</strong>. Todas las funciones premium están desbloqueadas.',
        'sub_activated_account': 'Cuenta',
        'sub_activated_subscription': 'Suscripción',
        'sub_activated_payment': 'Pago',
        'sub_activated_payment_value': 'Confirmado vía dLocal Go',
        'sub_activated_enjoy': 'Ahora tienes acceso completo a todas las herramientas de automatización, CRM e IA. ¡Disfruta! 🚀',

        'sub_deactivated_subject': '⚠️ Actualización de Suscripción — EnpiAI',
        'sub_deactivated_preheader': 'El estado de tu suscripción cambió',
        'sub_deactivated_title': 'Actualización de Suscripción ⚠️',
        'sub_deactivated_body': 'Queremos informarte que el estado de tu suscripción ha cambiado a <strong>inactivo</strong>.',
        'sub_deactivated_reason': 'Razón',
        'sub_deactivated_restore': 'Para restaurar el acceso a todas las funciones, actualiza tu método de pago o contacta al administrador de la plataforma.',
        'sub_deactivated_cta': 'Reactivar Suscripción →',

        'lead_subject': '🎯 Nuevo Lead: {name} — EnpiAI',
        'lead_preheader': 'Nuevo lead capturado: {name}',
        'lead_title': '¡Nuevo Lead Capturado! 🎯',
        'lead_body': 'Un nuevo prospecto ha sido agregado a tu CRM.',
        'lead_name': 'Nombre',
        'lead_email': 'Correo',
        'lead_phone': 'Teléfono',
        'lead_source': 'Origen',
        'lead_followup': 'Revisa tus contactos para más detalles y haz seguimiento pronto para mejores resultados de conversión.',
        'lead_cta': 'Ver Contactos →',

        'wellness_subject': '🌿 Nueva Evaluación de Bienestar — EnpiAI',
        'wellness_preheader': 'Nueva evaluación de bienestar de {name}',
        'wellness_title': '¡Nueva Evaluación de Bienestar! 🌿',
        'wellness_body': 'Un prospecto acaba de completar una evaluación de bienestar a través de tu enlace personalizado.',
        'wellness_prospect': 'Prospecto',
        'wellness_anonymous': 'Anónimo',
        'wellness_bmi': 'IMC',
        'wellness_goal': 'Objetivo',
        'wellness_not_specified': 'No especificado',
        'wellness_review': 'Revisa la evaluación y genera un informe PDF personalizado para compartir con tu prospecto.',
        'wellness_cta': 'Ver Evaluaciones →',

        'courtesy_subject': '🎁 Tu Cuenta de Cortesía EnpiAI — EnpiAI',
        'courtesy_preheader': 'Tus credenciales de cuenta de cortesía',
        'courtesy_title': '¡Tu Cuenta de EnpiAI está Lista! 🎁',
        'courtesy_body': 'Se ha creado una cuenta de cortesía para ti en la plataforma EnpiAI. Tienes acceso completo a todas las funciones — sin pago requerido.',
        'courtesy_email': 'Correo',
        'courtesy_password': 'Contraseña temporal',
        'courtesy_status': 'Estado',
        'courtesy_status_value': 'Cortesía — Activo',
        'courtesy_warning': '⚠️ Por favor cambia tu contraseña después de tu primer inicio de sesión por seguridad.',
        'courtesy_cta': 'Iniciar Sesión →',

        'report_title': 'Tu Evaluación de Bienestar 🌿',
        'report_thanks': 'Gracias por completar tu evaluación de bienestar con <strong>{distributor}</strong>.',
        'report_bmi': 'IMC',
        'report_goal': 'Objetivo principal',
        'report_followup': 'Tu distribuidor se pondrá en contacto pronto con recomendaciones personalizadas.',
    },

    'pt': {
        'brand_subtitle': 'Automação Empresarial Inteligente',
        'footer_rights': '© 2026 EnpiAI por WEBLIFETECH. Todos os direitos reservados.',

        'welcome_subject': 'Bem-vindo ao EnpiAI! 🎉',
        'welcome_preheader': 'Sua conta EnpiAI está pronta',
        'welcome_title': 'Bem-vindo ao EnpiAI! 🎉',
        'welcome_greeting': 'Olá <strong>{name}</strong>,',
        'welcome_body': 'Sua conta foi criada com sucesso. Você já pode automatizar seu negócio Herbalife com ferramentas de IA.',
        'welcome_business': 'Negócio',
        'welcome_email': 'E-mail',
        'welcome_status': 'Status',
        'welcome_status_active': 'Ativo',
        'welcome_next': 'Veja o que você pode fazer agora:',
        'welcome_step_1': 'Conectar seu canal WhatsApp',
        'welcome_step_2': 'Fazer upload de documentos para treinar seu agente IA',
        'welcome_step_3': 'Compartilhar seu link de avaliação de bem-estar',
        'welcome_step_4': 'Ativar um plano de assinatura',
        'welcome_cta': 'Ir ao Painel →',

        'google_welcome_body': 'Sua conta foi criada automaticamente via Google Sign-In. Você pode começar a usar a plataforma imediatamente.',
        'google_auth_method': 'Método de autenticação',
        'google_get_started': 'Comece conectando seus canais de mensagens e fazendo upload de documentos de produtos para treinar seu agente IA.',

        'sub_activated_subject': '✅ Assinatura Ativada — EnpiAI',
        'sub_activated_preheader': 'Sua assinatura está ativa',
        'sub_activated_title': 'Assinatura Ativada! ✅',
        'sub_activated_body': 'Ótimas notícias! Seu pagamento de assinatura foi <strong>confirmado</strong>. Todos os recursos premium estão desbloqueados.',
        'sub_activated_account': 'Conta',
        'sub_activated_subscription': 'Assinatura',
        'sub_activated_payment': 'Pagamento',
        'sub_activated_payment_value': 'Confirmado via dLocal Go',
        'sub_activated_enjoy': 'Agora você tem acesso total a todas as ferramentas de automação, CRM e IA. Aproveite! 🚀',

        'sub_deactivated_subject': '⚠️ Atualização de Assinatura — EnpiAI',
        'sub_deactivated_preheader': 'O status da sua assinatura mudou',
        'sub_deactivated_title': 'Atualização de Assinatura ⚠️',
        'sub_deactivated_body': 'Gostaríamos de informar que o status da sua assinatura mudou para <strong>inativo</strong>.',
        'sub_deactivated_reason': 'Motivo',
        'sub_deactivated_restore': 'Para restaurar o acesso a todos os recursos, atualize seu método de pagamento ou entre em contato com o administrador da plataforma.',
        'sub_deactivated_cta': 'Reativar Assinatura →',

        'lead_subject': '🎯 Novo Lead: {name} — EnpiAI',
        'lead_preheader': 'Novo lead capturado: {name}',
        'lead_title': 'Novo Lead Capturado! 🎯',
        'lead_body': 'Um novo prospect foi adicionado ao seu CRM.',
        'lead_name': 'Nome',
        'lead_email': 'E-mail',
        'lead_phone': 'Telefone',
        'lead_source': 'Origem',
        'lead_followup': 'Verifique seus contatos para mais detalhes e faça o acompanhamento rapidamente para melhores resultados de conversão.',
        'lead_cta': 'Ver Contatos →',

        'wellness_subject': '🌿 Nova Avaliação de Bem-estar — EnpiAI',
        'wellness_preheader': 'Nova avaliação de bem-estar de {name}',
        'wellness_title': 'Nova Avaliação de Bem-estar! 🌿',
        'wellness_body': 'Um prospect acabou de completar uma avaliação de bem-estar através do seu link personalizado.',
        'wellness_prospect': 'Prospect',
        'wellness_anonymous': 'Anônimo',
        'wellness_bmi': 'IMC',
        'wellness_goal': 'Objetivo',
        'wellness_not_specified': 'Não especificado',
        'wellness_review': 'Revise a avaliação e gere um relatório PDF personalizado para compartilhar com seu prospect.',
        'wellness_cta': 'Ver Avaliações →',

        'courtesy_subject': '🎁 Sua Conta de Cortesia EnpiAI — EnpiAI',
        'courtesy_preheader': 'Suas credenciais de conta de cortesia',
        'courtesy_title': 'Sua Conta EnpiAI está Pronta! 🎁',
        'courtesy_body': 'Uma conta de cortesia foi criada para você na plataforma EnpiAI. Você tem acesso total a todos os recursos — sem pagamento necessário.',
        'courtesy_email': 'E-mail',
        'courtesy_password': 'Senha temporária',
        'courtesy_status': 'Status',
        'courtesy_status_value': 'Cortesia — Ativo',
        'courtesy_warning': '⚠️ Por favor, altere sua senha após o primeiro login por segurança.',
        'courtesy_cta': 'Entrar Agora →',

        'report_title': 'Sua Avaliação de Bem-estar 🌿',
        'report_thanks': 'Obrigado por completar sua avaliação de bem-estar com <strong>{distributor}</strong>.',
        'report_bmi': 'IMC',
        'report_goal': 'Objetivo principal',
        'report_followup': 'Seu distribuidor entrará em contato em breve com recomendações personalizadas.',
    }
}


class EmailService:
    """SMTP-based email sending service with branded, localized templates"""

    def _t(self, lang, key, **kwargs):
        """Get translated string for a given language and key."""
        strings = EMAIL_STRINGS.get(lang, EMAIL_STRINGS['en'])
        text = strings.get(key, EMAIL_STRINGS['en'].get(key, key))
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, IndexError):
                return text
        return text

    # ──────────────────────────────────────────────
    # Core Send Method
    # ──────────────────────────────────────────────

    def send(self, to_email, subject, body_html, body_text=None, from_email=None, attachments=None):
        """
        Send an email via SMTP.
        attachments: list of file paths to attach.
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
            msg['From'] = f"EnpiAI <{smtp_from}>"
            msg['To'] = to_email

            if body_text:
                msg.attach(MIMEText(body_text, 'plain'))
            msg.attach(MIMEText(body_html, 'html'))
            
            # Attach files
            if attachments:
                for file_path in attachments:
                    try:
                        with open(file_path, "rb") as f:
                            part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
                        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                        msg.attach(part)
                    except Exception as attach_err:
                        logger.warning(f"Failed to attach file {file_path}: {attach_err}")

            # Port 465 = implicit SSL (SMTP_SSL)
            # Port 587 = STARTTLS (SMTP + starttls())
            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port)
                if use_tls:
                    server.starttls()

            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_from, to_email, msg.as_string())
            server.quit()

            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Email send error to {to_email}: {e}")
            return False

    # ──────────────────────────────────────────────
    # Base HTML Template
    # ──────────────────────────────────────────────

    def _base_template(self, content, preheader="", lang="en"):
        """Wrap content in a branded EnpiAI HTML email layout."""
        t = lambda key, **kw: self._t(lang, key, **kw)
        return f"""
<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>EnpiAI</title>
  <style>
    body {{ margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f4f4f7; color: #333; }}
    .preheader {{ display: none !important; visibility: hidden; mso-hide: all; font-size: 1px; color: #f4f4f7; line-height: 1px; max-height: 0; max-width: 0; opacity: 0; overflow: hidden; }}
    .wrapper {{ width: 100%; background-color: #f4f4f7; padding: 40px 0; }}
    .container {{ max-width: 580px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.06); }}
    .header {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 32px 40px; text-align: center; }}
    .header h1 {{ margin: 0; color: #ffffff; font-size: 24px; font-weight: 700; letter-spacing: -0.5px; }}
    .header .subtitle {{ color: #94a3b8; font-size: 13px; margin-top: 4px; }}
    .body {{ padding: 40px; }}
    .body h2 {{ margin: 0 0 16px; font-size: 22px; color: #0f172a; }}
    .body p {{ margin: 0 0 16px; font-size: 15px; line-height: 1.6; color: #475569; }}
    .info-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin: 24px 0; }}
    .info-card table {{ width: 100%; border-collapse: collapse; }}
    .info-card td {{ padding: 6px 0; font-size: 14px; vertical-align: top; }}
    .info-card td:first-child {{ color: #64748b; width: 140px; font-weight: 500; }}
    .info-card td:last-child {{ color: #0f172a; font-weight: 600; }}
    .cta {{ display: inline-block; background: linear-gradient(135deg, #3b82f6, #2563eb); color: #ffffff !important; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px; margin: 8px 0; }}
    .badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }}
    .badge-green {{ background: #dcfce7; color: #166534; }}
    .badge-red {{ background: #fee2e2; color: #991b1b; }}
    .badge-blue {{ background: #dbeafe; color: #1e40af; }}
    .divider {{ border: none; border-top: 1px solid #e2e8f0; margin: 24px 0; }}
    .footer {{ padding: 24px 40px; text-align: center; background: #f8fafc; }}
    .footer p {{ margin: 0; font-size: 12px; color: #94a3b8; }}
    .footer a {{ color: #3b82f6; text-decoration: none; }}
  </style>
</head>
<body>
  <span class="preheader">{preheader}</span>
  <div class="wrapper">
    <div class="container">
      <div class="header">
        <h1>🤖 EnpiAI</h1>
        <div class="subtitle">{t('brand_subtitle')}</div>
      </div>
      <div class="body">
        {content}
      </div>
      <div class="footer">
        <p>{t('footer_rights')}</p>
        <p style="margin-top: 8px;"><a href="https://enpi.click">enpi.click</a></p>
      </div>
    </div>
  </div>
</body>
</html>
"""

    # ──────────────────────────────────────────────
    # 1. Welcome Email (Manual Registration)
    # ──────────────────────────────────────────────

    def send_welcome_email(self, to_email, user_name, distributor_name, lang='en'):
        """Send welcome email after manual registration."""
        t = lambda key, **kw: self._t(lang, key, **kw)
        content = f"""
        <h2>{t('welcome_title')}</h2>
        <p>{t('welcome_greeting', name=user_name)}</p>
        <p>{t('welcome_body')}</p>

        <div class="info-card">
          <table>
            <tr><td>{t('welcome_business')}</td><td>{distributor_name}</td></tr>
            <tr><td>{t('welcome_email')}</td><td>{to_email}</td></tr>
            <tr><td>{t('welcome_status')}</td><td><span class="badge badge-green">{t('welcome_status_active')}</span></td></tr>
          </table>
        </div>

        <p>{t('welcome_next')}</p>
        <p>
          ✅ {t('welcome_step_1')}<br>
          ✅ {t('welcome_step_2')}<br>
          ✅ {t('welcome_step_3')}<br>
          ✅ {t('welcome_step_4')}
        </p>

        <p style="text-align: center; margin-top: 24px;">
          <a href="https://enpi.click/dashboard" class="cta">{t('welcome_cta')}</a>
        </p>
        """
        return self.send(to_email, t('welcome_subject'), self._base_template(content, t('welcome_preheader'), lang))

    # ──────────────────────────────────────────────
    # 2. Welcome Email (Google Auto-Registration)
    # ──────────────────────────────────────────────

    def send_google_welcome_email(self, to_email, user_name, lang='en'):
        """Send welcome email after Google auto-registration."""
        t = lambda key, **kw: self._t(lang, key, **kw)
        content = f"""
        <h2>{t('welcome_title')}</h2>
        <p>{t('welcome_greeting', name=user_name)}</p>
        <p>{t('google_welcome_body')}</p>

        <div class="info-card">
          <table>
            <tr><td>{t('welcome_email')}</td><td>{to_email}</td></tr>
            <tr><td>{t('google_auth_method')}</td><td>Google</td></tr>
            <tr><td>{t('welcome_status')}</td><td><span class="badge badge-green">{t('welcome_status_active')}</span></td></tr>
          </table>
        </div>

        <p>{t('google_get_started')}</p>

        <p style="text-align: center; margin-top: 24px;">
          <a href="https://enpi.click/dashboard" class="cta">{t('welcome_cta')}</a>
        </p>
        """
        return self.send(to_email, t('welcome_subject'), self._base_template(content, t('welcome_preheader'), lang))

    # ──────────────────────────────────────────────
    # 3. Subscription Activated
    # ──────────────────────────────────────────────

    def send_subscription_activated(self, to_email, distributor_name, lang='en'):
        """Send notification when dLocal confirms a subscription payment."""
        t = lambda key, **kw: self._t(lang, key, **kw)
        content = f"""
        <h2>{t('sub_activated_title')}</h2>
        <p>{t('welcome_greeting', name=distributor_name)}</p>
        <p>{t('sub_activated_body')}</p>

        <div class="info-card">
          <table>
            <tr><td>{t('sub_activated_account')}</td><td>{distributor_name}</td></tr>
            <tr><td>{t('sub_activated_subscription')}</td><td><span class="badge badge-green">{t('welcome_status_active')}</span></td></tr>
            <tr><td>{t('sub_activated_payment')}</td><td>{t('sub_activated_payment_value')}</td></tr>
          </table>
        </div>

        <p>{t('sub_activated_enjoy')}</p>

        <p style="text-align: center; margin-top: 24px;">
          <a href="https://enpi.click/dashboard" class="cta">{t('welcome_cta')}</a>
        </p>
        """
        return self.send(to_email, t('sub_activated_subject'), self._base_template(content, t('sub_activated_preheader'), lang))

    # ──────────────────────────────────────────────
    # 4. Subscription Deactivated
    # ──────────────────────────────────────────────

    def send_subscription_deactivated(self, to_email, distributor_name, reason="", lang='en'):
        """Send notification when a subscription is cancelled or payment fails."""
        t = lambda key, **kw: self._t(lang, key, **kw)
        reason_text = f"<p>{t('sub_deactivated_reason')}: <em>{reason}</em></p>" if reason else ""
        content = f"""
        <h2>{t('sub_deactivated_title')}</h2>
        <p>{t('welcome_greeting', name=distributor_name)}</p>
        <p>{t('sub_deactivated_body')}</p>
        {reason_text}

        <div class="info-card">
          <table>
            <tr><td>{t('sub_activated_account')}</td><td>{distributor_name}</td></tr>
            <tr><td>{t('sub_activated_subscription')}</td><td><span class="badge badge-red">{t('sub_deactivated_title').split(' ')[0]}</span></td></tr>
          </table>
        </div>

        <p>{t('sub_deactivated_restore')}</p>

        <p style="text-align: center; margin-top: 24px;">
          <a href="https://enpi.click/subscribe" class="cta">{t('sub_deactivated_cta')}</a>
        </p>
        """
        return self.send(to_email, t('sub_deactivated_subject'), self._base_template(content, t('sub_deactivated_preheader'), lang))

    # ──────────────────────────────────────────────
    # 5. New Lead Notification
    # ──────────────────────────────────────────────

    def send_new_lead_notification(self, to_email, distributor_name, lead_name, lead_email="", lead_phone="", source="", lang='en'):
        """Notify distributor when a new lead is captured."""
        t = lambda key, **kw: self._t(lang, key, **kw)
        details_rows = f"<tr><td>{t('lead_name')}</td><td>{lead_name}</td></tr>"
        if lead_email:
            details_rows += f"<tr><td>{t('lead_email')}</td><td>{lead_email}</td></tr>"
        if lead_phone:
            details_rows += f"<tr><td>{t('lead_phone')}</td><td>{lead_phone}</td></tr>"
        if source:
            details_rows += f"<tr><td>{t('lead_source')}</td><td><span class='badge badge-blue'>{source}</span></td></tr>"

        content = f"""
        <h2>{t('lead_title')}</h2>
        <p>{t('welcome_greeting', name=distributor_name)}</p>
        <p>{t('lead_body')}</p>

        <div class="info-card">
          <table>
            {details_rows}
          </table>
        </div>

        <p>{t('lead_followup')}</p>

        <p style="text-align: center; margin-top: 24px;">
          <a href="https://enpi.click/contacts" class="cta">{t('lead_cta')}</a>
        </p>
        """
        return self.send(to_email, t('lead_subject', name=lead_name), self._base_template(content, t('lead_preheader', name=lead_name), lang))

    # ──────────────────────────────────────────────
    # 6. Wellness Evaluation Submitted
    # ──────────────────────────────────────────────

    def send_wellness_evaluation_notification(self, to_email, distributor_name, lead_name="", bmi="N/A", goal="", lang='en'):
        """Notify distributor when a wellness evaluation is submitted."""
        t = lambda key, **kw: self._t(lang, key, **kw)
        content = f"""
        <h2>{t('wellness_title')}</h2>
        <p>{t('welcome_greeting', name=distributor_name)}</p>
        <p>{t('wellness_body')}</p>

        <div class="info-card">
          <table>
            <tr><td>{t('wellness_prospect')}</td><td>{lead_name or t('wellness_anonymous')}</td></tr>
            <tr><td>{t('wellness_bmi')}</td><td>{bmi}</td></tr>
            <tr><td>{t('wellness_goal')}</td><td>{goal or t('wellness_not_specified')}</td></tr>
          </table>
        </div>

        <p>{t('wellness_review')}</p>

        <p style="text-align: center; margin-top: 24px;">
          <a href="https://enpi.click/wellness" class="cta">{t('wellness_cta')}</a>
        </p>
        """
        return self.send(to_email, t('wellness_subject'), self._base_template(content, t('wellness_preheader', name=lead_name or t('wellness_anonymous')), lang))

    # ──────────────────────────────────────────────
    # 7. Courtesy Account Created
    # ──────────────────────────────────────────────

    def send_courtesy_account_created(self, to_email, name, temp_password, lang='en'):
        """Send credentials to a newly created courtesy account."""
        t = lambda key, **kw: self._t(lang, key, **kw)
        content = f"""
        <h2>{t('courtesy_title')}</h2>
        <p>{t('welcome_greeting', name=name)}</p>
        <p>{t('courtesy_body')}</p>

        <div class="info-card">
          <table>
            <tr><td>{t('courtesy_email')}</td><td>{to_email}</td></tr>
            <tr><td>{t('courtesy_password')}</td><td><code style="background:#f1f5f9; padding:2px 8px; border-radius:4px; font-size:14px;">{temp_password}</code></td></tr>
            <tr><td>{t('courtesy_status')}</td><td><span class="badge badge-green">{t('courtesy_status_value')}</span></td></tr>
          </table>
        </div>

        <p>{t('courtesy_warning')}</p>

        <p style="text-align: center; margin-top: 24px;">
          <a href="https://enpi.click/login" class="cta">{t('courtesy_cta')}</a>
        </p>
        """
        return self.send(to_email, t('courtesy_subject'), self._base_template(content, t('courtesy_preheader'), lang))

    # ──────────────────────────────────────────────
    # Legacy: Wellness Report to Prospect
    # ──────────────────────────────────────────────

    def send_wellness_report(self, to_email, distributor_name, evaluation_data, lang='en'):
        """Send a wellness evaluation report email to the prospect."""
        t = lambda key, **kw: self._t(lang, key, **kw)
        bmi = evaluation_data.get('bmi', 'N/A')
        bmi_cat = evaluation_data.get('bmi_category', '')
        goal = evaluation_data.get('primary_goal', 'general wellness')

        content = f"""
        <h2>{t('report_title')}</h2>
        <p>{t('report_thanks', distributor=distributor_name)}</p>

        <div class="info-card">
          <table>
            <tr><td>{t('report_bmi')}</td><td>{bmi} ({bmi_cat})</td></tr>
            <tr><td>{t('report_goal')}</td><td>{goal}</td></tr>
          </table>
        </div>

        <p>{t('report_followup')}</p>
        """
        return self.send(to_email, f"🌿 {t('report_title')} — {distributor_name}", self._base_template(content, t('report_title'), lang))

    def send_wellness_report_to_lead(self, to_email, distributor_name, evaluation_data, pdf_path=None, lang='en'):
        """ Branded email for the lead with the PDF report attached. """
        t = lambda key, **kw: self._t(lang, key, **kw)
        
        content = f"""
        <h2>{t('report_title')}</h2>
        <p>{t('report_thanks', distributor=distributor_name)}</p>
        
        <div class="info-card">
          <table>
            <tr><td>{t('report_bmi')}</td><td>{evaluation_data.get('bmi', 'N/A')}</td></tr>
            <tr><td>{t('report_goal')}</td><td>{evaluation_data.get('primary_goal', t('wellness_not_specified'))}</td></tr>
          </table>
        </div>
        
        <p>{t('wellness_review')}</p>
        <p>{t('report_followup')}</p>
        """
        attachments = [pdf_path] if pdf_path and os.path.exists(pdf_path) else None
        return self.send(
            to_email, 
            f"🌿 {t('report_title')} — {distributor_name}", 
            self._base_template(content, t('report_title'), lang),
            attachments=attachments
        )


# Singleton instance
email_service = EmailService()
