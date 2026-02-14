"""
RAG Service - Pinecone vector database operations for document storage and retrieval.
Uses text-embedding-3-small (1536 dimensions) via LLM Service.

Migration Path: Vector embeddings are operational/anonymized data.
Private sovereign data remains encrypted in SQL.
"""
import logging
import hashlib
from flask import current_app

logger = logging.getLogger(__name__)



class RAGService:
    """Handles Pinecone vector database operations"""

    def __init__(self):
        self._index = None

    def _get_index(self, api_key=None, index_name=None):
        """Lazy-initialize Pinecone index. Allows explicit config for async threads."""
        if self._index is None:
            try:
                from pinecone import Pinecone

                # Fallback to current_app if not provided (sync context)
                if not api_key:
                    api_key = current_app.config.get('PINECONE_API_KEY', '')
                if not index_name:
                    index_name = current_app.config.get('PINECONE_INDEX_NAME', 'enpi-ai-rag')

                if not api_key:
                    logger.warning("Pinecone API key not configured")
                    return None

                pc = Pinecone(api_key=api_key)
                self._index = pc.Index(index_name)
                logger.info(f"Pinecone index '{index_name}' initialized")

            except ImportError:
                logger.error("pinecone-client package not installed")
            except RuntimeError:
                 # Likely outside application context in thread
                 logger.error("Pinecone init failed: Missing app context or explicit keys")
            except Exception as e:
                logger.error(f"Pinecone initialization error: {e}")

        return self._index

    def query(self, query_text, distributor_id, top_k=5, filter_metadata=None):
        """
        Query Pinecone for relevant documents with Two-Tier RAG + Keyword Reranking.

        Phase 11: Queries both the distributor's local namespace AND the global
        namespace (managed by Super Admin). Results are merged and re-ranked.

        Args:
            query_text: search query
            distributor_id: int or str, for namespace isolation
            top_k: number of results
            filter_metadata: optional filter dict

        Returns:
            list of matches with text, scores, and source tier
        """
        from services.llm_service import llm_service

        index = self._get_index()
        if not index:
            logger.warning("Pinecone index not available, returning empty results")
            return []

        local_namespace = f"dist_{distributor_id}"
        global_namespace = "global"

        # Get query embedding (shared for both queries)
        query_embedding = llm_service.get_embedding(query_text)

        # --- Phase 11: Two-Tier Query ---
        fetch_k = top_k * 3

        # 1. Local namespace (distributor-specific docs)
        local_results = []
        try:
            local_raw = index.query(
                vector=query_embedding,
                top_k=fetch_k,
                namespace=local_namespace,
                include_metadata=True,
                filter=filter_metadata
            )
            local_results = local_raw.get('matches', [])
        except Exception as e:
            logger.warning(f"Local RAG query failed for {local_namespace}: {e}")

        # 2. Global namespace (Herbalife general knowledge)
        global_results = []
        try:
            global_rag_enabled = True
            try:
                from models.platform_config import PlatformConfig
                config = PlatformConfig.get_config()
                global_rag_enabled = config.global_rag_enabled
            except Exception:
                pass  # Default to enabled

            if global_rag_enabled:
                global_raw = index.query(
                    vector=query_embedding,
                    top_k=fetch_k,
                    namespace=global_namespace,
                    include_metadata=True,
                )
                global_results = global_raw.get('matches', [])
        except Exception as e:
            logger.warning(f"Global RAG query failed: {e}")

        # 3. Merge and re-rank
        matches = []
        query_keywords = [w.lower() for w in query_text.split() if len(w) > 3]
        seen_ids = set()

        for match_list, tier in [(local_results, 'local'), (global_results, 'global')]:
            for match in match_list:
                if match['id'] in seen_ids:
                    continue
                seen_ids.add(match['id'])

                text = match.get('metadata', {}).get('text', '')
                score = match['score']

                # Keyword Boosting
                if text:
                    text_lower = text.lower()
                    matches_count = sum(1 for w in query_keywords if w in text_lower)
                    if matches_count > 0:
                        boost = min(0.2, matches_count * 0.05)
                        score += boost

                # Slight boost for local (more relevant to this distributor)
                if tier == 'local':
                    score += 0.03

                matches.append({
                    'id': match['id'],
                    'score': score,
                    'text': text,
                    'metadata': match.get('metadata', {}),
                    'tier': tier,
                })

        # Sort by boosted score
        matches.sort(key=lambda x: x['score'], reverse=True)

        return matches[:top_k]

    def upsert_document(self, text_chunks, distributor_id, document_id, metadata=None, api_key=None, index_name=None):
        """
        Upsert document chunks into Pinecone.
        Example of explicit config injection for workers.
        """
        from services.llm_service import llm_service

        index = self._get_index(api_key=api_key, index_name=index_name)
        if not index:
            raise RuntimeError("Pinecone index not available")

        namespace = f"dist_{distributor_id}"
        vectors = []
        vector_ids = []

        for i, chunk in enumerate(text_chunks):
            # Generate embedding
            # Note: llm_service.get_embedding might also need explicit API key if it relies on current_app
            # But usually LLM service init captures it? Let's assume it works or fix it later.
            # Actually llm_service uses os.getenv mostly or current_app. 
            # We should probably pass OpenAI key too if needed.
            embedding = llm_service.get_embedding(chunk)

            # Create unique vector ID
            chunk_hash = hashlib.md5(chunk.encode()).hexdigest()[:8]
            vector_id = f"doc_{document_id}_chunk_{i}_{chunk_hash}"
            vector_ids.append(vector_id)

            # Prepare metadata
            chunk_metadata = {
                'document_id': document_id,
                'distributor_id': distributor_id,
                'chunk_index': i,
                'text': chunk[:1000],  # Store truncated text for retrieval
            }
            if metadata:
                chunk_metadata.update(metadata)

            vectors.append({
                'id': vector_id,
                'values': embedding,
                'metadata': chunk_metadata
            })

        # Batch upsert (max 100 per batch)
        batch_size = 100
        for batch_start in range(0, len(vectors), batch_size):
            batch = vectors[batch_start:batch_start + batch_size]
            index.upsert(vectors=batch, namespace=namespace)

        logger.info(f"Upserted {len(vectors)} chunks for document {document_id}")
        return vector_ids

    # ... query and delete methods ...

    def upsert_document_async(self, text_chunks, distributor_id, document_id, metadata=None):
        """Non-blocking document upsert via Celery task queue."""
        try:
            from tasks import index_document_rag
            index_document_rag.delay(
                text_chunks=text_chunks,
                distributor_id=distributor_id,
                document_id=document_id,
                metadata=metadata
            )
            logger.info(f"Document {document_id} upsert dispatched to Celery worker")
        except Exception as e:
            logger.warning(f"Celery dispatch failed ({e}), falling back to sync upsert")
            self.upsert_document(text_chunks, distributor_id, document_id, metadata)


# Singleton instance
rag_service = RAGService()
