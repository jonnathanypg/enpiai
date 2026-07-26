"""
Prospect Trie Service - Prefix Tree Data Structure
Implements Trie data structure for O(L) instant autocomplete search
over Prospect Names, Emails, and Phone Numbers per Tenant ID in EnpiAI.

Zero-Downtime & Non-Destructive: Reads Prospect models without DB mutations.
"""
from typing import List, Dict, Any, Optional

class ProspectTrieNode:
    def __init__(self):
        self.children: Dict[str, 'ProspectTrieNode'] = {}
        self.is_end_of_word: bool = False
        self.items: List[Dict[str, Any]] = []


class ProspectSearchTrieService:
    """
    Trie Index per Tenant ID for O(L) Autocomplete Searches in Distributor CRM
    """
    _tries: Dict[int, ProspectTrieNode] = {}  # tenant_id -> Root ProspectTrieNode

    @classmethod
    def rebuild_trie_for_tenant(cls, tenant_id: int):
        """Build Trie index for a distributor tenant from active prospects in database"""
        root = ProspectTrieNode()
        try:
            from models.prospect import Prospect
            prospects = Prospect.query.filter_by(distributor_id=tenant_id).all()
        except Exception:
            prospects = []

        for prospect in prospects:
            prospect_info = prospect.to_dict() if hasattr(prospect, 'to_dict') else {
                'id': getattr(prospect, 'id', None),
                'name': getattr(prospect, 'name', ''),
                'email': getattr(prospect, 'email', ''),
                'phone': getattr(prospect, 'phone', ''),
                'lead_score': getattr(prospect, 'lead_score', 0)
            }

            # Index terms
            search_terms = []
            name = getattr(prospect, 'name', '')
            if name:
                search_terms.append(name.lower())
                for part in name.lower().split():
                    search_terms.append(part)
            
            email = getattr(prospect, 'email', '')
            if email:
                search_terms.append(email.lower())
                
            phone = getattr(prospect, 'phone', '')
            if phone:
                search_terms.append(phone.replace("+", "").replace(" ", ""))

            for term in search_terms:
                if term:
                    cls._insert_term(root, term, prospect_info)

        cls._tries[tenant_id] = root
        return len(prospects)

    @classmethod
    def _insert_term(cls, root: ProspectTrieNode, term: str, prospect_info: Dict[str, Any]):
        curr = root
        for char in term:
            if char not in curr.children:
                curr.children[char] = ProspectTrieNode()
            curr = curr.children[char]
            # Keep up to 10 matching prospects at intermediate nodes for fast prefix matches
            if not any(p['id'] == prospect_info['id'] for p in curr.items):
                if len(curr.items) < 10:
                    curr.items.append(prospect_info)
        curr.is_end_of_word = True

    @classmethod
    def search_prefix(cls, tenant_id: int, prefix: str) -> List[Dict[str, Any]]:
        """Search prefix in O(L) time where L is length of prefix"""
        if tenant_id not in cls._tries:
            cls.rebuild_trie_for_tenant(tenant_id)

        root = cls._tries.get(tenant_id)
        if not root:
            return []

        curr = root
        for char in prefix.lower():
            if char not in curr.children:
                return []
            curr = curr.children[char]

        return curr.items
