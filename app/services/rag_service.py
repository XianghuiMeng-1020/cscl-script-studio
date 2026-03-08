"""RAG (Retrieval-Augmented Generation) service for CSCL scripts"""
import os
import json
from typing import List, Dict, Any, Optional
from app.config import Config


class RAGService:
    """RAG service for retrieving course materials"""
    
    def __init__(self):
        self.course_docs_dir = os.path.join(Config.DATA_DIR, 'course_docs')
        os.makedirs(self.course_docs_dir, exist_ok=True)
    
    def retrieve_chunks(self, topic: str, learning_objectives: List[str], 
                        course_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks from course materials
        
        Args:
            topic: Script topic
            learning_objectives: List of learning objectives
            course_id: Optional course ID to filter materials
        
        Returns:
            List of chunks with 'text', 'ref', 'score' fields
        """
        chunks = []
        
        # Try to load course materials
        course_file = os.path.join(self.course_docs_dir, f'{course_id}.json' if course_id else 'default.json')
        
        if os.path.exists(course_file):
            try:
                with open(course_file, 'r', encoding='utf-8') as f:
                    materials = json.load(f)
                
                # Simple keyword-based retrieval (BM25 simplified)
                topic_keywords = set(topic.lower().split())
                objective_keywords = set()
                for obj in learning_objectives:
                    objective_keywords.update(obj.lower().split())
                
                all_keywords = topic_keywords | objective_keywords
                
                # Score each material chunk
                if isinstance(materials, list):
                    for i, material in enumerate(materials):
                        if isinstance(material, dict):
                            text = material.get('text', material.get('content', ''))
                        else:
                            text = str(material)
                        
                        # Simple keyword matching score
                        text_lower = text.lower()
                        score = sum(1 for kw in all_keywords if kw in text_lower)
                        
                        if score > 0:
                            chunks.append({
                                'text': text[:500],  # Limit length
                                'ref': material.get('ref', f'{course_file}#{i}'),
                                'score': score
                            })
                
                # Sort by score and return top 5
                chunks.sort(key=lambda x: x['score'], reverse=True)
                chunks = chunks[:5]
                
            except Exception as e:
                # If file read fails, return empty chunks
                pass
        
        # If no chunks found, return empty list (fallback)
        return chunks
    
    def add_course_materials(self, course_id: str, materials: List[Dict[str, Any]]):
        """Add course materials for retrieval (helper method)"""
        course_file = os.path.join(self.course_docs_dir, f'{course_id}.json')
        with open(course_file, 'w', encoding='utf-8') as f:
            json.dump(materials, f, ensure_ascii=False, indent=2)
