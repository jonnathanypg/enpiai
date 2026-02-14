"""
Herbalife Distributor SaaS Platform - Database Models Package
Copyright © 2026 WEBLIFETECH (Jonnathan Peña). All Rights Reserved.
"""
from .user import User, UserRole
from .distributor import Distributor, AgentGender, SubscriptionTier
from .agent_config import AgentConfig, AgentFeature, AgentTone, AgentObjective, FeatureCategory, DEFAULT_FEATURES
from .lead import Lead, LeadStatus, LeadSource, LeadType
from .customer import Customer
from .wellness_evaluation import WellnessEvaluation
from .product import Product
from .conversation import Conversation, Message, ConversationChannel, ConversationStatus, MessageRole
from .appointment import Appointment, AppointmentStatus, AppointmentType
from .document import Document
from .channel import Channel, ChannelType, ChannelStatus

# Phase 11: Enterprise Scale
from .platform_config import PlatformConfig
from .subscription import Plan, Subscription, PlanInterval, SubscriptionStatus
from .transaction import Transaction, TransactionStatus, TransactionType

# Phase 9: Scheduled Tasks (model lives in services, imported here for migration discovery)
try:
    from services.cron_service import ScheduledTask
except ImportError:
    ScheduledTask = None

__all__ = [
    'User', 'UserRole',
    'Distributor', 'AgentGender', 'SubscriptionTier',
    'AgentConfig', 'AgentFeature', 'AgentTone', 'AgentObjective', 'FeatureCategory', 'DEFAULT_FEATURES',
    'Lead', 'LeadStatus', 'LeadSource', 'LeadType',
    'Customer',
    'WellnessEvaluation',
    'Product',
    'Conversation', 'Message', 'ConversationChannel', 'ConversationStatus', 'MessageRole',
    'Appointment', 'AppointmentStatus', 'AppointmentType',
    'Document',
    'Channel', 'ChannelType', 'ChannelStatus',
    'PlatformConfig',
    'Plan', 'Subscription', 'PlanInterval', 'SubscriptionStatus',
    'Transaction', 'TransactionStatus', 'TransactionType',
]
