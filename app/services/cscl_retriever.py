"""CSCL Retriever service for RAG grounding"""
from typing import List, Dict, Any, Optional
from collections import Counter
import math
from app.db import db
from app.models import CSCLDocumentChunk, CSCLCourseDocument
from app.services.document_service import safe_preview_or_none


class CSCLRetriever:
    """Retriever service for course document chunks"""
    
    def __init__(self, k: int = 5):
        """
        Initialize retriever
        
        Args:
            k: Number of top chunks to return
        """
        self.k = k
    
    def _extract_keywords(self, text: str) -> set:
        """Extract keywords from text (simple tokenization)"""
        # Simple tokenization: split by whitespace and punctuation
        import re
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter out very short words
        return set(w for w in words if len(w) > 2)
    
    def _compute_bm25_score(self, query_terms: set, chunk_text: str, 
                           doc_freqs: Dict[str, int], avg_doc_length: float,
                           total_docs: int) -> float:
        """
        Compute BM25 score (simplified version)
        
        Args:
            query_terms: Set of query terms
            chunk_text: Chunk text to score
            doc_freqs: Document frequency of each term
            avg_doc_length: Average document length
            total_docs: Total number of documents
        """
        k1 = 1.5
        b = 0.75
        
        chunk_words = self._extract_keywords(chunk_text)
        chunk_length = len(chunk_words)
        
        score = 0.0
        for term in query_terms:
            if term not in chunk_words:
                continue
            
            # Term frequency in chunk
            tf = chunk_text.lower().count(term)
            
            # Inverse document frequency
            df = doc_freqs.get(term, 1)
            idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1.0)
            
            # BM25 component
            numerator = idf * tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * (chunk_length / avg_doc_length))
            
            score += numerator / denominator if denominator > 0 else 0
        
        return score
    
    def _compute_keyword_score(self, query_terms: set, chunk_text: str) -> float:
        """Simple keyword matching score"""
        chunk_words = self._extract_keywords(chunk_text)
        
        # Count matches
        matches = len(query_terms & chunk_words)
        total_query_terms = len(query_terms)
        
        if total_query_terms == 0:
            return 0.0
        
        # Coverage score
        coverage = matches / total_query_terms
        
        # Length penalty (prefer medium-length chunks)
        length = len(chunk_text)
        ideal_length = 500
        length_penalty = 1.0 - abs(length - ideal_length) / (ideal_length * 2)
        length_penalty = max(0.1, length_penalty)  # Minimum 0.1
        
        return coverage * length_penalty
    
    def retrieve(self, query: str, course_id: str, 
                binding_type: str = 'planner') -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for a query
        
        Args:
            query: Query text
            course_id: Course ID to filter documents
            binding_type: Type of binding (planner/material/critic/refiner)
        
        Returns:
            List of chunks with:
            - chunk_id
            - doc_id
            - title
            - snippet
            - relevance_score
            - citation_hint
        """
        # Get all chunks for the course
        documents = CSCLCourseDocument.query.filter_by(course_id=course_id).all()
        
        if not documents:
            return []
        
        # Collect all chunks
        all_chunks = []
        for doc in documents:
            chunks = CSCLDocumentChunk.query.filter_by(document_id=doc.id).all()
            all_chunks.extend(chunks)
        
        if not all_chunks:
            return []
        
        # Extract query keywords
        query_terms = self._extract_keywords(query)
        
        if not query_terms:
            return []
        
        # Compute document frequencies (for BM25)
        doc_freqs = {}
        for chunk in all_chunks:
            chunk_words = self._extract_keywords(chunk.chunk_text)
            for word in chunk_words:
                doc_freqs[word] = doc_freqs.get(word, 0) + 1
        
        # Average document length
        avg_doc_length = sum(len(self._extract_keywords(c.chunk_text)) 
                            for c in all_chunks) / len(all_chunks) if all_chunks else 1.0
        
        # Score each chunk
        scored_chunks = []
        for chunk in all_chunks:
            # Use keyword score (simpler and faster)
            score = self._compute_keyword_score(query_terms, chunk.chunk_text)
            
            # Optional: Add BM25 score (weighted combination)
            # bm25_score = self._compute_bm25_score(
            #     query_terms, chunk.chunk_text, doc_freqs, avg_doc_length, len(all_chunks)
            # )
            # score = 0.7 * score + 0.3 * bm25_score
            
            if score > 0:
                # Get document info
                doc = CSCLCourseDocument.query.get(chunk.document_id)
                
                snippet = safe_preview_or_none(chunk.chunk_text or '', 300) if chunk.chunk_text else None
                scored_chunks.append({
                    'chunk_id': chunk.id,
                    'doc_id': chunk.document_id,
                    'title': doc.title if doc else 'Unknown',
                    'snippet': snippet if snippet is not None else '',
                    'relevance_score': score,
                    'citation_hint': f"{doc.title if doc else 'Unknown'} (chunk {chunk.chunk_index + 1})"
                })
        
        # Sort by score and return top k
        scored_chunks.sort(key=lambda x: x['relevance_score'], reverse=True)
        return scored_chunks[:self.k]
    
    def construct_query(self, spec: Dict[str, Any], stage_target: str) -> str:
        """
        Construct query from spec and stage target
        
        Args:
            spec: Pedagogical specification
            stage_target: Stage target (e.g., 'planner', 'material_generator')
        
        Returns:
            Query string
        """
        query_parts = []
        
        # Add course context
        course_context = spec.get('course_context', {})
        if course_context.get('topic'):
            query_parts.append(course_context['topic'])
        if course_context.get('subject'):
            query_parts.append(course_context['subject'])
        
        # Add learning objectives
        learning_objectives = spec.get('learning_objectives', {})
        for obj_list in learning_objectives.values():
            if isinstance(obj_list, list):
                query_parts.extend(obj_list)
        
        # Add task requirements
        task_requirements = spec.get('task_requirements', {})
        if task_requirements.get('task_type'):
            query_parts.append(task_requirements['task_type'])
        if task_requirements.get('expected_output'):
            query_parts.append(str(task_requirements['expected_output']))
        
        # Stage-specific additions
        if stage_target == 'material_generator':
            query_parts.append('materials')
            query_parts.append('resources')
        elif stage_target == 'critic':
            query_parts.append('validation')
            query_parts.append('quality')
        elif stage_target == 'refiner':
            query_parts.append('improvement')
            query_parts.append('refinement')
        
        return ' '.join(query_parts)
