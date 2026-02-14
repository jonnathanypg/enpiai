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
            'lead_status': self.lead_status,
            'lead_source': self.lead_source,
            'lead_score': self.lead_score,
        }

    def get_context_summary(self) -> str:
        """Generate a human-readable summary for the agent's system prompt."""
        parts = [f"Name: {self.name}"]
        if self.lead_status:
            parts.append(f"Status: {self.lead_status}")
        if self.lead_source:
            parts.append(f"Source: {self.lead_source}")
        if self.lead_score:
            parts.append(f"Score: {self.lead_score}/100")
        if self.interests:
            parts.append(f"Interests: {self.interests}")
        if self.notes:
            parts.append(f"Notes: {self.notes}")
        return " | ".join(parts)


class IdentityResolver:
    """
    Resolves user identity from messaging channel identifiers.
    """

    @staticmethod
    def resolve_from_phone(phone: str, distributor_id: int) -> dict:
        """
        Resolve user identity from WhatsApp phone number.
        
        Search order:
        1. Check if it's a registered Customer
        2. Check if it's a known Lead
        3. Return not-found (the agent or webhook will auto-create a Lead)
        """
        db.session.rollback()
        
        # Normalize phone
        phone = phone.replace(" ", "").replace("-", "")
        phone_clean = phone.replace("+", "")
        
        logger.info(f"[IdentityResolver] Resolving phone: {phone} for distributor: {distributor_id}")

        # 1. Check Customers
        try:
            from models.customer import Customer
            customer = Customer.query.filter(
                Customer.phone.like(f"%{phone_clean}%"),
                Customer.distributor_id == distributor_id
            ).first()
            if customer:
                logger.info(f"[IdentityResolver] Found Customer: {customer.name} (ID: {customer.id})")
                return {
                    'found': True, 'type': 'customer', 'id': customer.id,
                    'name': customer.name, 'email': customer.email,
                    'context': f"Returning customer: {customer.name}",
                }
        except Exception as e:
            logger.warning(f"[IdentityResolver] Customer lookup error: {e}")

        # 2. Check Leads
        try:
            from models.lead import Lead
            lead = Lead.query.filter(
                Lead.phone.like(f"%{phone_clean}%"),
                Lead.distributor_id == distributor_id
            ).first()
            if lead:
                virtual = VirtualUser(lead)
                logger.info(f"[IdentityResolver] Found Lead: {lead.name} (ID: {lead.id})")
                return {
                    'found': True, 'type': 'lead', 'id': lead.id,
                    'name': lead.name, 'email': lead.email,
                    'virtual_user': virtual,
                    'context': virtual.get_context_summary(),
                }
        except Exception as e:
            logger.warning(f"[IdentityResolver] Lead lookup error: {e}")

        # 3. Not found
        logger.info(f"[IdentityResolver] No identity found for phone: {phone}")
        return {'found': False, 'type': 'unknown', 'context': 'New prospect (no prior history)'}

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
                    }
            except Exception as e:
                logger.warning(f"[IdentityResolver] Conversation customer lookup error: {e}")

        return {'found': False, 'type': 'unknown', 'context': 'API user with active conversation'}
