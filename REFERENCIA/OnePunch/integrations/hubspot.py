"""
HubSpot CRM Integration
Contact and deal management
"""
import os
from typing import List, Dict, Optional, Any
from datetime import datetime


class HubSpotIntegration:
    """HubSpot CRM integration for contact and deal management"""
    
    def __init__(self, api_key: Optional[str] = None, access_token: Optional[str] = None):
        """
        Initialize HubSpot integration
        
        Args:
            api_key: HubSpot Private App Token
            access_token: HubSpot OAuth Access Token
        """
        self.api_key = api_key or os.getenv('HUBSPOT_API_KEY')
        self.access_token = access_token
        self._client = None
    
    def _get_client(self):
        """Get or create HubSpot API client"""
        if self._client:
            return self._client
        
        token = self.access_token or self.api_key
        
        if not token:
            raise ValueError("HubSpot not configured (OAuth token or API key required)")
        
        try:
            from hubspot import HubSpot
            self._client = HubSpot(access_token=token)
            return self._client
        except ImportError:
            raise ImportError("hubspot-api-client package not installed. Run: pip install hubspot-api-client")
    
    def search_contacts(
        self,
        query: str,
        properties: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for contacts by email, name, or phone
        
        Args:
            query: Search query (email, name, or phone)
            properties: List of properties to return
        
        Returns:
            List of matching contacts
        """
        client = self._get_client()
        
        if properties is None:
            properties = ['firstname', 'lastname', 'email', 'phone', 'company', 'lifecyclestage', 'hubspot_owner_id', 'hs_buying_role', 'hs_lead_status']
        
        # Build search request
        from hubspot.crm.contacts import PublicObjectSearchRequest
        
        search_request = PublicObjectSearchRequest(
            query=query,
            properties=properties,
            limit=10
        )
        
        try:
            response = client.crm.contacts.search_api.do_search(search_request)
            
            contacts = []
            for result in response.results:
                contact = {
                    'id': result.id,
                    'properties': result.properties,
                    'created_at': result.created_at.isoformat() if result.created_at else None,
                    'updated_at': result.updated_at.isoformat() if result.updated_at else None
                }
                contacts.append(contact)
            
            return contacts
        except Exception as e:
            raise Exception(f"Failed to search contacts: {str(e)}")
    
    def get_contact_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get a contact by email address
        
        Args:
            email: Email address
        
        Returns:
            Contact data or None if not found
        """
        contacts = self.search_contacts(email)
        for contact in contacts:
            if contact['properties'].get('email', '').lower() == email.lower():
                return contact
        return None
    
    def get_contact_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """
        Get a contact by phone number
        
        Args:
            phone: Phone number
        
        Returns:
            Contact data or None if not found
        """
        # Normalize phone number (remove non-digits except +)
        normalized = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        contacts = self.search_contacts(normalized)
        for contact in contacts:
            contact_phone = contact['properties'].get('phone', '')
            contact_phone_normalized = ''.join(c for c in contact_phone if c.isdigit() or c == '+')
            if contact_phone_normalized == normalized:
                return contact
        return None
    
    def create_contact(
        self,
        email: str,
        firstname: Optional[str] = None,
        lastname: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        properties: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new contact
        
        Args:
            email: Email address (required)
            firstname: First name
            lastname: Last name
            phone: Phone number
            company: Company name
            properties: Additional properties
        
        Returns:
            Created contact data
        """
        client = self._get_client()
        
        # Build properties
        contact_properties = {
            'email': email
        }
        
        if firstname:
            contact_properties['firstname'] = firstname
        if lastname:
            contact_properties['lastname'] = lastname
        if phone:
            contact_properties['phone'] = phone
        if company:
            contact_properties['company'] = company
        if properties:
            contact_properties.update(properties)
        
        from hubspot.crm.contacts import SimplePublicObjectInputForCreate
        
        try:
            contact_input = SimplePublicObjectInputForCreate(properties=contact_properties)
            response = client.crm.contacts.basic_api.create(contact_input)
            
            return {
                'success': True,
                'id': response.id,
                'properties': response.properties,
                'created_at': response.created_at.isoformat() if response.created_at else None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_contact(
        self,
        contact_id: str,
        properties: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Update an existing contact
        
        Args:
            contact_id: HubSpot contact ID
            properties: Properties to update
        
        Returns:
            Update result
        """
        client = self._get_client()
        
        from hubspot.crm.contacts import SimplePublicObjectInput
        
        try:
            contact_input = SimplePublicObjectInput(properties=properties)
            response = client.crm.contacts.basic_api.update(contact_id, contact_input)
            
            return {
                'success': True,
                'id': response.id,
                'properties': response.properties,
                'updated_at': response.updated_at.isoformat() if response.updated_at else None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_or_update_contact(
        self,
        email: str,
        firstname: Optional[str] = None,
        lastname: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        properties: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a contact if it doesn't exist, or update if it does
        
        Args:
            email: Email address
            firstname: First name
            lastname: Last name
            phone: Phone number
            company: Company name
            properties: Additional properties
        
        Returns:
            Contact result with action taken
        """
        # Check if contact exists
        existing = self.get_contact_by_email(email)
        
        if existing:
            # Update existing contact
            update_props = {}
            if firstname:
                update_props['firstname'] = firstname
            if lastname:
                update_props['lastname'] = lastname
            if phone:
                update_props['phone'] = phone
            if company:
                update_props['company'] = company
            if properties:
                update_props.update(properties)
            
            result = self.update_contact(existing['id'], update_props)
            result['action'] = 'updated'
            return result
        else:
            # Create new contact
            result = self.create_contact(email, firstname, lastname, phone, company, properties)
            result['action'] = 'created'
            return result
    
    def create_deal(
        self,
        dealname: str,
        amount: Optional[float] = None,
        pipeline: str = 'default',
        dealstage: str = 'appointmentscheduled',
        contact_id: Optional[str] = None,
        properties: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new deal
        
        Args:
            dealname: Deal name
            amount: Deal amount
            pipeline: Pipeline ID (default: 'default')
            dealstage: Deal stage ID
            contact_id: Associated contact ID
            properties: Additional properties
        
        Returns:
            Created deal data
        """
        client = self._get_client()
        
        # Build properties
        deal_properties = {
            'dealname': dealname,
            'pipeline': pipeline,
            'dealstage': dealstage
        }
        
        if amount is not None:
            deal_properties['amount'] = str(amount)
        if properties:
            deal_properties.update(properties)
        
        from hubspot.crm.deals import SimplePublicObjectInputForCreate
        
        try:
            deal_input = SimplePublicObjectInputForCreate(properties=deal_properties)
            response = client.crm.deals.basic_api.create(deal_input)
            
            deal_result = {
                'success': True,
                'id': response.id,
                'properties': response.properties,
                'created_at': response.created_at.isoformat() if response.created_at else None
            }
            
            # Associate with contact if provided
            if contact_id:
                try:
                    from hubspot.crm.deals import AssociationSpec
                    
                    # CONTACT_TO_DEAL association type ID is typically 3
                    client.crm.deals.associations_api.create(
                        deal_id=response.id,
                        to_object_type='contacts',
                        to_object_id=contact_id,
                        association_type_id=3  # Deal to Contact
                    )
                    deal_result['associated_contact'] = contact_id
                except Exception as assoc_error:
                    deal_result['association_warning'] = str(assoc_error)
            
            return deal_result
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def add_note_to_contact(
        self,
        contact_id: str,
        note_body: str
    ) -> Dict[str, Any]:
        """
        Add a note/engagement to a contact
        
        Args:
            contact_id: HubSpot contact ID
            note_body: Note content
        
        Returns:
            Note creation result
        """
        client = self._get_client()
        
        try:
            from hubspot.crm.objects.notes import SimplePublicObjectInputForCreate
            
            note_properties = {
                'hs_note_body': note_body,
                'hs_timestamp': str(int(datetime.now().timestamp() * 1000))
            }
            
            note_input = SimplePublicObjectInputForCreate(properties=note_properties)
            response = client.crm.objects.notes.basic_api.create(note_input)
            
            # Associate note with contact
            try:
                client.crm.objects.notes.associations_api.create(
                    note_id=response.id,
                    to_object_type='contacts',
                    to_object_id=contact_id,
                    association_type_id=202  # Note to Contact
                )
            except Exception:
                pass  # Note created, association may fail silently
            
            return {
                'success': True,
                'note_id': response.id,
                'message': 'Note added to contact'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def sync_conversation(
        self,
        contact_phone: str,
        contact_name: Optional[str] = None,
        conversation_summary: Optional[str] = None,
        lead_score: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Sync a conversation to HubSpot as a contact + note
        
        Args:
            contact_phone: Contact phone number
            contact_name: Contact name (parsed into first/last)
            conversation_summary: Summary to add as note
            lead_score: Optional lead score
            tags: Optional tags
        
        Returns:
            Sync result
        """
        # Parse name
        firstname = None
        lastname = None
        if contact_name:
            parts = contact_name.strip().split(' ', 1)
            firstname = parts[0] if parts else None
            lastname = parts[1] if len(parts) > 1 else None
        
        # First, try to find existing contact by phone
        existing = self.get_contact_by_phone(contact_phone)
        
        if existing:
            contact_id = existing['id']
            action = 'found_existing'
        else:
            # Create new contact (generate email from phone if none)
            generated_email = f"{contact_phone.replace('+', '')}@phone.onepunch.io"
            
            result = self.create_contact(
                email=generated_email,
                firstname=firstname,
                lastname=lastname,
                phone=contact_phone
            )
            
            if not result.get('success'):
                return result
            
            contact_id = result['id']
            action = 'created_new'
        
        # Add conversation summary as note if provided
        note_result = None
        if conversation_summary:
            note_result = self.add_note_to_contact(contact_id, conversation_summary)
        
        return {
            'success': True,
            'contact_id': contact_id,
            'action': action,
            'note_added': note_result.get('success') if note_result else False,
            'message': f"Contact {action.replace('_', ' ')} and synced to HubSpot"
        }

    def update_lifecycle_stage(
        self,
        contact_id: str,
        stage: str
    ) -> Dict[str, Any]:
        """
        Update a contact's lifecycle stage.
        Stages: lead, marketingqualifiedlead, salesqualifiedlead, opportunity, customer, evangelist, other
        """
        return self.update_contact(contact_id, {'lifecyclestage': stage})

    def search_deals(
        self,
        contact_id: Optional[str] = None,
        dealname: Optional[str] = None,
        properties: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for deals associated with a contact or by name.
        """
        client = self._get_client()
        
        if properties is None:
            properties = ['dealname', 'amount', 'dealstage', 'pipeline']

        filters = []
        if dealname:
            filters.append({
                "propertyName": "dealname",
                "operator": "EQ",
                "value": dealname
            })
            
        # Note: Searching by associated contact via search API is complex.
        # Often easier to list associations if we have the contact ID, 
        # or use the association filter if supported by the V3 search API.
        # For simple V3 search, we'll stick to property filters first.
        
        from hubspot.crm.deals import PublicObjectSearchRequest
        
        search_request = PublicObjectSearchRequest(
            filter_groups=[{"filters": filters}] if filters else [],
            properties=properties,
            limit=5
        )
        
        try:
            response = client.crm.deals.search_api.do_search(search_request)
            deals = []
            for result in response.results:
                deals.append({
                    'id': result.id,
                    'properties': result.properties,
                    'created_at': result.created_at.isoformat() if result.created_at else None,
                    'updated_at': result.updated_at.isoformat() if result.updated_at else None
                })
            return deals
        except Exception as e:
            raise Exception(f"Failed to search deals: {str(e)}")

    def update_deal_stage(
        self,
        deal_id: str,
        stage: str
    ) -> Dict[str, Any]:
        """
        Update a deal's stage.
        """
        client = self._get_client()
        from hubspot.crm.deals import SimplePublicObjectInput
        
        try:
            deal_input = SimplePublicObjectInput(properties={'dealstage': stage})
            response = client.crm.deals.basic_api.update(deal_id, deal_input)
            
            return {
                'success': True,
                'id': response.id,
                'properties': response.properties
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
