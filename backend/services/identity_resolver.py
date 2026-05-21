"""
Identity Resolver Service
Resolves user identity from messaging channel identifiers (phone, telegram chat_id).
Inspired by KindiCoreAI architecture, adapted for Herbalife Distributor SaaS.

Migration Path: Identity resolution will use DID-based verification for decentralized auth.
"""
import logging
from extensions import db

logger = logging.getLogger(__name__)


class VirtualUser:
    """
    Acts as a User proxy for Leads who don't have a real User account.
    Allows the agent to have context about who they're talking to.
    """
    def __init__(self, lead):
        self.id = -abs(lead.id)  # Negative ID convention
        self.email = lead.email or f"lead_{lead.id}@enpi.virtual"
        self.name = lead.name or "Prospecto"
        self.phone = lead.phone
        self.is_virtual = True
        self.is_active = True
        self.is_ai_active = getattr(lead, 'is_ai_active', True)
        self.distributor_id = lead.distributor_id
        
        # CRM Context
        self.lead_status = lead.status
        self.lead_source = lead.source
        self.lead_score = lead.score
        self.interests = lead.interests if hasattr(lead, 'interests') else None
        self.notes = lead.notes if hasattr(lead, 'notes') else None

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'role': 'lead',
            'is_virtual': True,
            'is_ai_active': self.is_ai_active,
            'lead_status': self.lead_status,
            'lead_source': self.lead_source,
            'lead_score': self.lead_score,
        }

    def get_context_summary(self) -> str:
        """Generate a human-readable summary for the agent's system prompt."""
        parts = [f"Nombre: {self.name}"]
        if self.lead_status:
            parts.append(f"Estado de Relación: {self.lead_status}")
        if self.lead_source:
            parts.append(f"Origen: {self.lead_source}")
        if self.lead_score:
            parts.append(f"Interés: {self.lead_score}/100")
        if self.interests:
            parts.append(f"Intereses: {self.interests}")
        if self.notes:
            parts.append(f"Notas: {self.notes}")
            
        # Add Wellness Evaluation Context
        try:
            from models.wellness_evaluation import WellnessEvaluation
            latest_eval = WellnessEvaluation.query.filter_by(
                lead_id=abs(self.id)
            ).order_by(WellnessEvaluation.created_at.desc()).first()
            
            if latest_eval:
                parts.append(f"Detalles de Evaluación:\n{latest_eval.get_summary()}")
        except Exception as e:
            logger.debug(f"Could not fetch wellness context for identity: {e}")

        return " | ".join(parts)


class IdentityResolver:
    """
    Resolves user identity from messaging channel identifiers.
    """

    @staticmethod
    def resolve_from_phone(phone: str, distributor_id: int) -> dict:
        """
        Resolve user identity from WhatsApp phone number.
        """
        db.session.rollback()
        from models.lead import Lead
        from models.customer import Customer
        from models.distributor import Distributor
        
        # 1. Normalize and Hash
        phone_hash = Lead.generate_phone_hash(phone)
        if not phone_hash:
            return {'found': False, 'type': 'unknown', 'context': 'Invalid phone'}
            
        logger.info(f"[IdentityResolver] Resolving phone: {phone} (hash: {phone_hash}) for distributor: {distributor_id}")

        # 0. Check if it's the Distributor themselves
        # Note: Distributors might not have hashes for their own numbers in the same way,
        # so we keep the suffix/exact matching for the distributor object which is usually NOT encrypted.
        phone_raw = str(phone).replace(" ", "").replace("-", "").replace("+", "")
        phone_suffix = phone_raw[-9:] if len(phone_raw) >= 9 else phone_raw

        try:
            distributor = Distributor.query.filter(
                Distributor.id == distributor_id,
                db.or_(
                    Distributor.whatsapp_phone.like(f"%{phone_suffix}%"),
                    Distributor.phone.like(f"%{phone_suffix}%"),
                    Distributor.whatsapp_phone == phone_raw,
                    Distributor.phone == phone_raw
                )
            ).first()
            
            if distributor:
                logger.info(f"[IdentityResolver] Found Distributor: {distributor.name}")
                return {
                    'found': True, 'type': 'distributor', 'id': distributor.id,
                    'name': distributor.name, 'email': distributor.email,
                    'context': (
                        f"IDENTIDAD CONFIRMADA: Estás hablando con el propietario de la cuenta ({distributor.name}). "
                        "MODO MAESTRO ACTIVADO. Responde como su Asistente Ejecutivo de Negocios."
                    ),
                }
        except Exception as e:
            logger.warning(f"[IdentityResolver] Distributor lookup error: {e}")

        # 1. Check Customers via Hash
        try:
            customer = Customer.query.filter_by(distributor_id=distributor_id, phone_hash=phone_hash).first()
            if customer:
                logger.info(f"[IdentityResolver] Found Customer: {customer.name}")
                return {
                    'found': True, 'type': 'customer', 'id': customer.id,
                    'name': customer.name, 'email': customer.email,
                    'context': f"Cliente existente: {customer.name}. Trátalo con prioridad.",
                    'is_ai_active': getattr(customer, 'is_ai_active', True)
                }
        except Exception as e:
            logger.warning(f"[IdentityResolver] Customer lookup error: {e}")

        # 2. Check Leads via Hash
        try:
            lead = Lead.query.filter_by(distributor_id=distributor_id, phone_hash=phone_hash).first()
            if lead:
                virtual = VirtualUser(lead)
                logger.info(f"[IdentityResolver] Found Lead: {lead.name}")
                return {
                    'found': True, 'type': 'lead', 'id': lead.id,
                    'name': lead.name, 'email': lead.email,
                    'virtual_user': virtual,
                    'context': virtual.get_context_summary(),
                    'is_ai_active': getattr(lead, 'is_ai_active', True)
                }
        except Exception as e:
            logger.warning(f"[IdentityResolver] Lead lookup error: {e}")

        # 3. Not found
        logger.info(f"[IdentityResolver] No identity found for phone: {phone}")
        return {'found': False, 'type': 'unknown', 'context': 'Nuevo contacto (sin historial previo)'}

    @staticmethod
    def resolve_from_telegram(chat_id: str, distributor_id: int) -> dict:
        """Resolve from Telegram Chat ID via Lead.telegram_chat_id."""
        db.session.rollback()
        try:
            from models.lead import Lead
            lead = Lead.query.filter(
                Lead.telegram_chat_id == str(chat_id),
                Lead.distributor_id == distributor_id
            ).first()
            if lead:
                virtual = VirtualUser(lead)
                return {
                    'found': True, 'type': 'lead', 'id': lead.id,
                    'name': lead.name, 'virtual_user': virtual,
                    'context': virtual.get_context_summary(),
                    'is_ai_active': getattr(lead, 'is_ai_active', True)
                }
        except Exception as e:
            logger.warning(f"[IdentityResolver] Telegram lookup error: {e}")
        return {'found': False, 'type': 'unknown', 'context': 'New Telegram contact'}

    @staticmethod
    def resolve_from_conversation(conversation) -> dict:
        """
        Resolve identity from a Conversation object (used by the OpenAI-compat endpoint).
        Falls back to whatever metadata the conversation has.
        """
        if not conversation:
            return {'found': False, 'type': 'unknown', 'context': 'Anonymous API user'}
        
        # If conversation has a lead_id
        if hasattr(conversation, 'lead_id') and conversation.lead_id:
            try:
                from models.lead import Lead
                lead = Lead.query.get(conversation.lead_id)
                if lead:
                    virtual = VirtualUser(lead)
                    return {
                        'found': True, 'type': 'lead', 'id': lead.id,
                        'name': lead.name, 'virtual_user': virtual,
                        'context': virtual.get_context_summary(),
                        'is_ai_active': getattr(lead, 'is_ai_active', True)
                    }
            except Exception as e:
                logger.warning(f"[IdentityResolver] Conversation lead lookup error: {e}")

        # If conversation has a customer_id
        if hasattr(conversation, 'customer_id') and conversation.customer_id:
            try:
                from models.customer import Customer
                customer = Customer.query.get(conversation.customer_id)
                if customer:
                    return {
                        'found': True, 'type': 'customer', 'id': customer.id,
                        'name': customer.name, 'email': customer.email,
                        'context': f"Returning customer: {customer.name}",
                        'is_ai_active': getattr(customer, 'is_ai_active', True)
                    }
            except Exception as e:
                logger.warning(f"[IdentityResolver] Conversation customer lookup error: {e}")

        return {'found': False, 'type': 'unknown', 'context': 'API user with active conversation'}
