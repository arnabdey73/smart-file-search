"""
GPT-4.1 mini API client.
Handles OpenAI API calls with retry logic and safety measures.
"""

import os
import asyncio
import json
import time
from typing import Dict, List, Any, Optional
import logging
import re

# Optional OpenAI import
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from .utils import load_prompt_template, sanitize_content
from pathlib import Path

logger = logging.getLogger(__name__)


class GPTClient:
    """OpenAI GPT-4.1 mini client with safety and retry logic."""
    
    def __init__(self):
        """Initialize the GPT client."""
        if not HAS_OPENAI:
            raise ImportError("openai package not installed")
        
        # Get API key
        self.api_key = os.getenv("GPT_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("GPT_API_KEY or OPENAI_API_KEY environment variable required")
        
        # Initialize OpenAI client
        openai.api_key = self.api_key
        
        # Configuration
        self.model = "gpt-4.1-mini"  # Use the specified model
        self.max_tokens = 1000
        self.temperature = 0.3
        self.timeout = 30
        self.max_retries = 3
        self.retry_delay = 1
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
        logger.info("GPT client initialized")
    
    async def rewrite_query(self, query: str) -> Dict[str, Any]:
        """
        Rewrite user query for better FTS search and extract filters.
        
        Args:
            query: Original user query
            
        Returns:
            Dictionary with rewritten query and extracted filters
        """
        try:
            # Load prompt template
            template = load_prompt_template("query_rewrite.txt")
            
            # Format prompt
            prompt = template.format(query=query)
            
            # Make API call
            response = await self._make_request(
                prompt=prompt,
                max_tokens=200,
                temperature=0.1
            )
            
            # Parse response
            result = self._parse_query_rewrite_response(response, query)
            
            logger.info(f"Query rewritten: '{query}' -> '{result['fts']}'")
            return result
            
        except Exception as e:
            logger.error(f"Query rewrite failed: {e}")
            # Return original query as fallback
            return {
                "fts": query,
                "filters": {"exts": [], "years": []},
                "notes": f"Rewrite failed: {str(e)}"
            }
    
    async def summarize_search_results(self, query: str, results: List[Dict], 
                                     style: str = "bullets", 
                                     max_tokens: int = 500) -> str:
        """
        Summarize search results using AI.
        
        Args:
            query: Original search query
            results: List of search results with path and snippet
            style: Summary style (bullets, paragraph, table)
            max_tokens: Maximum tokens for summary
            
        Returns:
            Generated summary text
        """
        try:
            if not results:
                return "No results found for the given query."
            
            # Load prompt template
            template = load_prompt_template("summarization.txt")
            
            # Prepare results for prompt (sanitize content)
            sanitized_results = []
            for result in results[:10]:  # Limit to top 10 results
                sanitized_result = {
                    "path": result.get("path", ""),
                    "snippet": sanitize_content(result.get("snippet", ""))
                }
                sanitized_results.append(sanitized_result)
            
            # Format prompt
            results_text = self._format_results_for_prompt(sanitized_results)
            prompt = template.format(
                query=query,
                style=style,
                results=results_text
            )
            
            # Make API call
            response = await self._make_request(
                prompt=prompt,
                max_tokens=min(max_tokens, 800),
                temperature=0.3
            )
            
            summary = response.strip()
            
            logger.info(f"Summarized {len(results)} results ({len(summary)} chars)")
            return summary
            
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return f"Error generating summary: {str(e)}"
    
    async def _make_request(self, prompt: str, max_tokens: int = None, 
                           temperature: float = None) -> str:
        """
        Make a request to OpenAI API with retry logic.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text response
        """
        # Rate limiting
        await self._rate_limit()
        
        # Use instance defaults if not specified
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature
        
        for attempt in range(self.max_retries):
            try:
                # Make API call
                response = await asyncio.wait_for(
                    self._api_call(prompt, max_tokens, temperature),
                    timeout=self.timeout
                )
                
                return response
                
            except asyncio.TimeoutError:
                logger.warning(f"API request timeout (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                raise
                
            except Exception as e:
                logger.warning(f"API request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                raise
        
        raise Exception("Max retries exceeded")
    
    async def _api_call(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Make the actual OpenAI API call."""
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=self.timeout
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def _rate_limit(self):
        """Implement basic rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    def _parse_query_rewrite_response(self, response: str, original_query: str) -> Dict[str, Any]:
        """Parse the query rewrite response into structured format."""
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                return json.loads(response)
            
            # Parse structured text response
            result = {
                "fts": original_query,
                "filters": {"exts": [], "years": []},
                "notes": ""
            }
            
            lines = response.strip().split('\n')
            for line in lines:
                line = line.strip()
                
                if line.startswith('FTS:'):
                    result["fts"] = line[4:].strip()
                elif line.startswith('Extensions:'):
                    exts_text = line[11:].strip()
                    result["filters"]["exts"] = [ext.strip() for ext in exts_text.split(',') if ext.strip()]
                elif line.startswith('Years:'):
                    years_text = line[6:].strip()
                    result["filters"]["years"] = [year.strip() for year in years_text.split(',') if year.strip()]
                elif line.startswith('Notes:'):
                    result["notes"] = line[6:].strip()
            
            return result
            
        except Exception as e:
            logger.warning(f"Could not parse query rewrite response: {e}")
            return {
                "fts": original_query,
                "filters": {"exts": [], "years": []},
                "notes": "Parse error"
            }
    
    def _format_results_for_prompt(self, results: List[Dict]) -> str:
        """Format search results for inclusion in prompt."""
        formatted_results = []
        
        for i, result in enumerate(results, 1):
            path = result.get("path", "Unknown")
            snippet = result.get("snippet", "")
            
            # Truncate long snippets
            if len(snippet) > 200:
                snippet = snippet[:200] + "..."
            
            formatted_results.append(f"{i}. {path}\n   {snippet}")
        
        return "\n\n".join(formatted_results)


# Singleton instance
_gpt_client = None

def get_gpt_client() -> GPTClient:
    """Get singleton GPT client instance."""
    global _gpt_client
    if _gpt_client is None:
        _gpt_client = GPTClient()
    return _gpt_client
