"""Web Retrieval Service - integrates web search for enriching lesson materials"""
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import requests

from app.config import Config

logger = logging.getLogger(__name__)


class WebRetrievalService:
    """Service for retrieving external web content to enrich lesson materials"""
    
    def __init__(self):
        self.enabled = getattr(Config, 'WEB_RETRIEVAL_ENABLED', False)
        self.provider = getattr(Config, 'WEB_RETRIEVAL_PROVIDER', 'tavily')
        self.api_key = getattr(Config, 'TAVILY_API_KEY', '')
        self.max_results = getattr(Config, 'TAVILY_MAX_RESULTS', 5)
        self.timeout = getattr(Config, 'WEB_RETRIEVAL_TIMEOUT', 30)
        self.max_content_length = getattr(Config, 'WEB_RETRIEVAL_MAX_CONTENT_LENGTH', 10000)
    
    def is_enabled(self) -> bool:
        """Check if web retrieval is enabled and configured"""
        return self.enabled and bool(self.api_key)
    
    def search_and_retrieve(
        self,
        query: str,
        search_depth: str = "basic",
        include_answer: bool = True,
        include_images: bool = False,
        max_results: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search the web and retrieve relevant content
        
        Args:
            query: Search query string
            search_depth: Search depth (basic or advanced)
            include_answer: Whether to include AI-generated answer
            include_images: Whether to include images
            max_results: Max number of results (defaults to config)
        
        Returns:
            Dict with search results and metadata
        """
        if not self.is_enabled():
            return {
                'success': False,
                'error': 'Web retrieval is not enabled or not configured',
                'results': []
            }
        
        try:
            if self.provider == 'tavily':
                return self._search_tavily(
                    query=query,
                    search_depth=search_depth,
                    include_answer=include_answer,
                    include_images=include_images,
                    max_results=max_results or self.max_results
                )
            else:
                return {
                    'success': False,
                    'error': f'Unsupported web retrieval provider: {self.provider}',
                    'results': []
                }
                
        except Exception as e:
            logger.error(f"Web retrieval error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'results': []
            }
    
    def _search_tavily(
        self,
        query: str,
        search_depth: str,
        include_answer: bool,
        include_images: bool,
        max_results: int
    ) -> Dict[str, Any]:
        """Perform search using Tavily API"""
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = {
            'api_key': self.api_key,
            'query': query,
            'search_depth': search_depth,
            'include_answer': include_answer,
            'include_images': include_images,
            'max_results': max_results
        }
        
        response = requests.post(
            'https://api.tavily.com/search',
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        
        if not response.ok:
            error_msg = f'Tavily API error: {response.status_code}'
            try:
                error_data = response.json()
                error_msg = error_data.get('error', error_msg)
            except:
                pass
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'results': []
            }
        
        data = response.json()
        
        # Process and clean results
        processed_results = []
        for result in data.get('results', []):
            processed_results.append({
                'title': result.get('title', 'Untitled'),
                'url': result.get('url', ''),
                'content': self._truncate_content(result.get('content', '')),
                'score': result.get('score', 0),
                'source': self._extract_domain(result.get('url', ''))
            })
        
        return {
            'success': True,
            'query': query,
            'answer': data.get('answer', ''),
            'results': processed_results,
            'metadata': {
                'total_results': len(processed_results),
                'search_depth': search_depth,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
    
    def retrieve_lesson_materials(
        self,
        spec: Dict[str, Any],
        retrieval_type: str = "examples"
    ) -> Dict[str, Any]:
        """
        Retrieve lesson-relevant external materials based on activity specification
        
        Args:
            spec: Activity specification containing topic, learning_objectives, etc.
            retrieval_type: Type of materials to retrieve (examples, cases, datasets, charts)
        
        Returns:
            Dict with retrieved materials organized by type
        """
        if not self.is_enabled():
            return {
                'success': False,
                'error': 'Web retrieval not enabled',
                'materials': {}
            }
        
        topic = spec.get('topic', '')
        task_type = spec.get('task_type', '')
        learning_objectives = spec.get('learning_objectives', [])
        
        # Build targeted search queries
        search_queries = self._build_search_queries(topic, task_type, learning_objectives, retrieval_type)
        
        all_results = {
            'success': True,
            'materials': {},
            'metadata': {
                'topic': topic,
                'retrieval_type': retrieval_type,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        for query_info in search_queries:
            try:
                result = self.search_and_retrieve(
                    query=query_info['query'],
                    search_depth=query_info.get('depth', 'basic'),
                    max_results=query_info.get('max_results', 3)
                )
                
                if result['success']:
                    category = query_info['category']
                    if category not in all_results['materials']:
                        all_results['materials'][category] = []
                    
                    # Add source attribution
                    for item in result['results']:
                        item['retrieval_category'] = category
                        item['search_query'] = query_info['query']
                    
                    all_results['materials'][category].extend(result['results'])
                    
            except Exception as e:
                logger.error(f"Failed to retrieve {query_info['category']}: {str(e)}")
                continue
        
        return all_results
    
    def _build_search_queries(
        self,
        topic: str,
        task_type: str,
        learning_objectives: List[str],
        retrieval_type: str
    ) -> List[Dict[str, str]]:
        """Build targeted search queries based on activity needs"""
        
        queries = []
        
        if retrieval_type == "examples" or retrieval_type == "all":
            # Real-world examples
            queries.append({
                'query': f'{topic} real world examples case studies classroom teaching',
                'category': 'examples',
                'depth': 'advanced',
                'max_results': 3
            })
            
            # Current events/cases
            queries.append({
                'query': f'{topic} recent news 2024 2025 educational case',
                'category': 'current_cases',
                'depth': 'basic',
                'max_results': 3
            })
        
        if retrieval_type == "datasets" or retrieval_type == "all":
            # Public datasets
            queries.append({
                'query': f'{topic} open data public dataset csv download education',
                'category': 'datasets',
                'depth': 'advanced',
                'max_results': 3
            })
            
            # Data sources
            queries.append({
                'query': f'{topic} statistics data source chart graph public domain',
                'category': 'data_sources',
                'depth': 'basic',
                'max_results': 2
            })
        
        if retrieval_type == "charts" or retrieval_type == "all":
            # Public charts and visualizations
            queries.append({
                'query': f'{topic} infographic chart visualization public domain educational',
                'category': 'visualizations',
                'depth': 'basic',
                'max_results': 3
            })
        
        if retrieval_type == "research" or retrieval_type == "all":
            # Educational research
            queries.append({
                'query': f'{topic} educational research findings pedagogy teaching methods',
                'category': 'research',
                'depth': 'advanced',
                'max_results': 2
            })
        
        # Task-specific queries
        if task_type == 'chart_critique':
            queries.append({
                'query': f'{topic} misleading data visualization examples common errors',
                'category': 'critique_examples',
                'depth': 'basic',
                'max_results': 3
            })
        
        if task_type == 'structured_debate':
            queries.append({
                'query': f'{topic} debate topics arguments pro con different perspectives',
                'category': 'debate_topics',
                'depth': 'advanced',
                'max_results': 3
            })
        
        return queries
    
    def _truncate_content(self, content: str) -> str:
        """Truncate content to max length"""
        if len(content) > self.max_content_length:
            return content[:self.max_content_length] + '...'
        return content
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL for source attribution"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return 'unknown'
    
    def format_for_prompt(self, retrieval_result: Dict[str, Any]) -> str:
        """Format retrieved materials for inclusion in LLM prompts"""
        if not retrieval_result.get('success') or not retrieval_result.get('materials'):
            return ""
        
        formatted_parts = ["\n\n=== External Resources Retrieved ===\n"]
        
        for category, items in retrieval_result['materials'].items():
            if not items:
                continue
            
            category_label = category.replace('_', ' ').title()
            formatted_parts.append(f"\n--- {category_label} ---\n")
            
            for i, item in enumerate(items[:3], 1):  # Limit to top 3 per category
                formatted_parts.append(
                    f"[{i}] {item.get('title', 'Untitled')}\n"
                    f"Source: {item.get('source', 'Unknown')}\n"
                    f"URL: {item.get('url', 'N/A')}\n"
                    f"Content: {item.get('content', '')[:500]}...\n"
                )
        
        formatted_parts.append("\n=== End External Resources ===\n")
        
        return "\n".join(formatted_parts)


# Singleton instance
_web_retrieval_service = None

def get_web_retrieval_service() -> WebRetrievalService:
    """Get or create the web retrieval service singleton"""
    global _web_retrieval_service
    if _web_retrieval_service is None:
        _web_retrieval_service = WebRetrievalService()
    return _web_retrieval_service