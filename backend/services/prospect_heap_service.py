"""
Prospect Heap Service - High Performance Max-Heap Engine
Implements Max-Heap (heapq) algorithms for O(1) priority access
to High-Intent or High-Risk Prospects for Herbalife Independent Distributors.

Zero-Downtime & Non-Destructive: Operates seamlessly on existing Prospect models.
"""
import heapq
import time
from typing import List, Dict, Optional, Any

class ProspectHeapItem:
    """Wrapper to enable Max-Heap comparison in heapq (invert lead_score / imc_risk for min-heap behavior)"""
    def __init__(self, prospect: Any):
        self.prospect = prospect
        # lead_score is 0 to 100. Invert so highest score comes first in min-heap.
        score = getattr(prospect, 'lead_score', 0) or 0
        self.priority = -score
        created_at = getattr(prospect, 'created_at', None)
        self.timestamp = created_at.timestamp() if hasattr(created_at, 'timestamp') else time.time()

    def __lt__(self, other):
        if self.priority == other.priority:
            return self.timestamp < other.timestamp  # Earliest prospect breaks ties
        return self.priority < other.priority


class ProspectPriorityHeapService:
    """
    In-Memory Max-Heap Service for Lead Scoring & Nutritional Triage (O(1) Top Access)
    """
    _heaps: Dict[int, List[ProspectHeapItem]] = {}  # tenant_id -> Heap List

    @classmethod
    def rebuild_heap_for_tenant(cls, tenant_id: int):
        """Build or refresh the Max-Heap for a distributor's tenant_id from database"""
        try:
            from models.lead import Lead
            from models.customer import Customer
            leads = Lead.query.filter_by(distributor_id=tenant_id).all()
            customers = Customer.query.filter_by(distributor_id=tenant_id).all()
            prospects = list(leads) + list(customers)
        except Exception:
            prospects = []

        heap_list = [ProspectHeapItem(p) for p in prospects]
        heapq.heapify(heap_list)
        cls._heaps[tenant_id] = heap_list
        return len(heap_list)

    @classmethod
    def get_top_prospect(cls, tenant_id: int) -> Optional[Any]:
        """Get highest priority prospect lead in O(1) time"""
        if tenant_id not in cls._heaps or not cls._heaps[tenant_id]:
            cls.rebuild_heap_for_tenant(tenant_id)

        heap = cls._heaps.get(tenant_id, [])
        if heap:
            return heap[0].prospect  # O(1) root inspection
        return None

    @classmethod
    def pop_top_prospect(cls, tenant_id: int) -> Optional[Any]:
        """Extract highest priority prospect in O(log N) time"""
        if tenant_id not in cls._heaps or not cls._heaps[tenant_id]:
            cls.rebuild_heap_for_tenant(tenant_id)

        heap = cls._heaps.get(tenant_id, [])
        if heap:
            item = heapq.heappop(heap)
            return item.prospect
        return None

    @classmethod
    def add_or_update_prospect(cls, prospect: Any):
        """Insert or refresh a prospect in the distributor's heap in O(log N) time"""
        tenant_id = getattr(prospect, 'distributor_id', None) or getattr(prospect, 'tenant_id', None)
        if not tenant_id:
            return
            
        if tenant_id not in cls._heaps:
            cls.rebuild_heap_for_tenant(tenant_id)
        
        item = ProspectHeapItem(prospect)
        heapq.heappush(cls._heaps[tenant_id], item)
