"""AI integration for Smart File Search using OpenAI GPT-4o-mini."""
import os
import logging
from typing import List, Dict, Any, Optional
import openai
from openai import OpenAI

logger = logging.getLogger(__name__)

class AISearchEnhancer:
    """AI-powered search enhancement using OpenAI GPT-4o-mini."""
    
    def __init__(self, config):
        self.config = config
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client with API key."""
        try:
            api_key = self.config.openai_api_key
            if not api_key:
                logger.warning("OpenAI API key not configured. AI features disabled.")
                return
            
            self.client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
    
    def is_available(self) -> bool:
        """Check if AI features are available."""
        return self.client is not None and self.config.enable_query_rewrite
    
    def enhance_query(self, user_query: str) -> str:
        """Enhance user query for better search results."""
        if not self.is_available():
            return user_query
        
        try:
            prompt = f"""
            You are an expert at transforming user search queries into effective file search terms.
            
            Transform this user query into better search keywords for finding files in a Windows network folder:
            "{user_query}"
            
            Guidelines:
            - Focus on key terms that would appear in file names and content
            - Include relevant file types and categories
            - Add synonyms and related terms
            - Keep it concise and focused
            - Return only the enhanced search terms, no explanation
            
            Enhanced search terms:
            """
            
            response = self.client.chat.completions.create(
                model=self.config.gpt_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.3
            )
            
            enhanced_query = response.choices[0].message.content.strip()
            logger.info(f"Query enhanced: '{user_query}' -> '{enhanced_query}'")
            return enhanced_query
            
        except Exception as e:
            logger.error(f"Query enhancement failed: {e}")
            return user_query
    
    def summarize_results(self, query: str, results: List[Dict[str, Any]], style: str = "bullets") -> str:
        """Summarize search results using AI."""
        if not self.is_available() or not self.config.enable_summarization:
            return self._simple_summary(results)
        
        try:
            # Prepare results for summarization
            results_text = ""
            for i, result in enumerate(results[:10], 1):  # Limit to top 10 results
                file_name = result.get('file_path', '').split('\\')[-1]
                snippet = result.get('snippet', '')[:200]  # Limit snippet length
                results_text += f"{i}. {file_name}: {snippet}\n"
            
            style_instructions = {
                "bullets": "Use bullet points with key findings",
                "paragraph": "Write a flowing paragraph summary", 
                "table": "Create a structured table format"
            }
            
            prompt = f"""
            Summarize these search results for the query "{query}".
            
            Search Results:
            {results_text}
            
            Instructions:
            - {style_instructions.get(style, 'Use bullet points')}
            - Focus on the most relevant findings
            - Group similar content together
            - Highlight key themes and patterns
            - Keep it concise but informative
            - Maximum 300 words
            
            Summary:
            """
            
            response = self.client.chat.completions.create(
                model=self.config.gpt_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.config.max_tokens,
                temperature=0.5
            )
            
            summary = response.choices[0].message.content.strip()
            logger.info(f"Results summarized for query: '{query}'")
            return summary
            
        except Exception as e:
            logger.error(f"Result summarization failed: {e}")
            return self._simple_summary(results)
    
    def _simple_summary(self, results: List[Dict[str, Any]]) -> str:
        """Create a simple summary without AI."""
        if not results:
            return "No results found."
        
        file_types = {}
        for result in results:
            file_path = result.get('file_path', '')
            ext = os.path.splitext(file_path)[1].lower()
            file_types[ext] = file_types.get(ext, 0) + 1
        
        summary = f"Found {len(results)} files:\n"
        for ext, count in sorted(file_types.items()):
            if ext:
                summary += f"• {count} {ext.upper()} files\n"
        
        return summary.strip()
    
    def suggest_related_queries(self, query: str, results: List[Dict[str, Any]]) -> List[str]:
        """Suggest related search queries based on results."""
        if not self.is_available() or len(results) < 3:
            return []
        
        try:
            # Extract file types and common terms from results
            file_types = set()
            content_terms = []
            
            for result in results[:5]:
                file_path = result.get('file_path', '')
                ext = os.path.splitext(file_path)[1].lower()
                if ext:
                    file_types.add(ext)
                
                snippet = result.get('snippet', '')
                content_terms.append(snippet[:100])
            
            context = f"File types found: {', '.join(file_types)}\n"
            context += f"Content samples: {' | '.join(content_terms)}"
            
            prompt = f"""
            Based on the search query "{query}" and these results, suggest 3-5 related search queries that might be useful:
            
            {context}
            
            Suggest specific, actionable search queries that would help find related content.
            Return only the queries, one per line, no numbering or explanation.
            """
            
            response = self.client.chat.completions.create(
                model=self.config.gpt_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7
            )
            
            suggestions = response.choices[0].message.content.strip().split('\n')
            suggestions = [s.strip() for s in suggestions if s.strip()][:5]
            
            logger.info(f"Generated {len(suggestions)} related query suggestions")
            return suggestions
            
        except Exception as e:
            logger.error(f"Related query suggestion failed: {e}")
            return []
