"""AI integration for Smart File Search using OpenAI GPT-4o-mini with token minimization."""
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import openai
from openai import OpenAI

logger = logging.getLogger(__name__)

class AISearchEnhancer:
    """AI-powered search enhancement using OpenAI GPT-4o-mini with token minimization."""
    
    def __init__(self, config):
        self.config = config
        self.client = None
        # Token conservation settings
        self.daily_token_limit = 5000  # Conservative daily limit
        self.max_tokens_per_request = 100  # Reduced from default
        self.usage_file = Path("data/token_usage.json")
        self.usage_file.parent.mkdir(exist_ok=True)
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
        """Check if AI features are available and within token limits."""
        if not (self.client is not None and self.config.enable_query_rewrite):
            return False
        
        # Check daily token limit
        return not self._is_daily_limit_exceeded()
    
    def _is_daily_limit_exceeded(self) -> bool:
        """Check if daily token limit has been exceeded."""
        try:
            if not self.usage_file.exists():
                return False
                
            with open(self.usage_file, 'r') as f:
                usage_data = json.load(f)
                
            today = datetime.now().strftime("%Y-%m-%d")
            today_usage = usage_data.get(today, 0)
            
            if today_usage >= self.daily_token_limit:
                logger.warning(f"Daily token limit ({self.daily_token_limit}) exceeded. Usage: {today_usage}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking token usage: {e}")
            return False
    
    def _log_token_usage(self, tokens: int) -> None:
        """Log token usage for tracking."""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            if self.usage_file.exists():
                with open(self.usage_file, 'r') as f:
                    usage_data = json.load(f)
            else:
                usage_data = {}
                
            usage_data[today] = usage_data.get(today, 0) + tokens
            
            # Clean up old entries (keep last 30 days)
            cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            usage_data = {k: v for k, v in usage_data.items() if k >= cutoff_date}
            
            with open(self.usage_file, 'w') as f:
                json.dump(usage_data, f, indent=2)
                
            logger.info(f"Logged {tokens} tokens. Daily total: {usage_data[today]}")
            
        except Exception as e:
            logger.error(f"Error logging token usage: {e}")
    
    def get_token_usage_stats(self) -> Dict[str, Any]:
        """Get current token usage statistics."""
        try:
            if not self.usage_file.exists():
                return {
                    "today_usage": 0,
                    "daily_limit": self.daily_token_limit,
                    "remaining_tokens": self.daily_token_limit,
                    "usage_percentage": 0,
                    "cost_today_usd": 0
                }
                
            with open(self.usage_file, 'r') as f:
                usage_data = json.load(f)
                
            today = datetime.now().strftime("%Y-%m-%d")
            today_usage = usage_data.get(today, 0)
            
            return {
                "today_usage": today_usage,
                "daily_limit": self.daily_token_limit,
                "remaining_tokens": max(0, self.daily_token_limit - today_usage),
                "usage_percentage": round((today_usage / self.daily_token_limit) * 100, 1),
                "cost_today_usd": round(today_usage * 0.00015 / 1000, 4),  # GPT-4o-mini pricing
                "last_7_days": {
                    date: tokens for date, tokens in usage_data.items()
                    if date >= (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting token usage stats: {e}")
            return {"error": str(e)}
    
    def enhance_query(self, user_query: str, force: bool = False) -> Dict[str, Any]:
        """Enhance user query for better search results with token tracking."""
        result = {
            "enhanced_query": user_query,
            "tokens_used": 0,
            "ai_used": False,
            "reason": "original_query"
        }
        
        if not force and not self.is_available():
            result["reason"] = "ai_unavailable" if not self.client else "token_limit_exceeded"
            return result
        
        # Skip AI for very short queries to save tokens
        if len(user_query.strip()) < 3:
            result["reason"] = "query_too_short"
            return result
            
        try:
            # Ultra-minimal prompt to reduce token usage
            prompt = f"Better search terms for: {user_query[:50]}"
            
            response = self.client.chat.completions.create(
                model=self.config.gpt_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens_per_request,
                temperature=0.2  # Lower temperature for more focused responses
            )
            
            enhanced_query = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens
            
            # Log token usage
            self._log_token_usage(tokens_used)
            
            result.update({
                "enhanced_query": enhanced_query,
                "tokens_used": tokens_used,
                "ai_used": True,
                "reason": "enhanced",
                "cost_usd": round(tokens_used * 0.00015 / 1000, 6)
            })
            
            logger.info(f"Query enhanced: '{user_query}' -> '{enhanced_query}' (Tokens: {tokens_used})")
            return result
            
        except Exception as e:
            logger.error(f"Query enhancement failed: {e}")
            result["reason"] = f"error: {str(e)}"
            return result
    
    def summarize_results(self, query: str, results: List[Dict[str, Any]], 
                         style: str = "bullets", force: bool = False) -> Dict[str, Any]:
        """Summarize search results using AI with token conservation."""
        result = {
            "summary": self._simple_summary(results),
            "tokens_used": 0,
            "ai_used": False,
            "reason": "simple_summary"
        }
        
        # Skip AI if not available or not enough results
        if not force and (not self.is_available() or not self.config.enable_summarization or len(results) < 3):
            result["reason"] = "ai_unavailable" if not self.client else "insufficient_results" if len(results) < 3 else "token_limit_exceeded"
            return result
        
        try:
            # Ultra-minimal summarization to save tokens
            files_text = ", ".join([
                result.get('file_path', '').split('\\')[-1][:30] 
                for result in results[:5]  # Only top 5 results
            ])
            
            # Very short prompt
            prompt = f"Summarize search for '{query[:30]}': {files_text[:200]}"
            
            response = self.client.chat.completions.create(
                model=self.config.gpt_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=min(self.max_tokens_per_request, 150),  # Limit tokens further
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens
            
            # Log token usage
            self._log_token_usage(tokens_used)
            
            result.update({
                "summary": summary,
                "tokens_used": tokens_used,
                "ai_used": True,
                "reason": "ai_summary",
                "cost_usd": round(tokens_used * 0.00015 / 1000, 6)
            })
            
            logger.info(f"Results summarized for query: '{query}' (Tokens: {tokens_used})")
            return result
            
        except Exception as e:
            logger.error(f"Result summarization failed: {e}")
            result["reason"] = f"error: {str(e)}"
            return result
    
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
    
    def suggest_related_queries(self, query: str, results: List[Dict[str, Any]], 
                              force: bool = False) -> Dict[str, Any]:
        """Suggest related search queries based on results with token conservation."""
        result = {
            "suggestions": [],
            "tokens_used": 0,
            "ai_used": False,
            "reason": "no_suggestions"
        }
        
        # Skip AI if not available or insufficient results
        if not force and (not self.is_available() or len(results) < 3):
            result["reason"] = "ai_unavailable" if not self.client else "insufficient_results"
            return result
        
        try:
            # Extract minimal context to save tokens
            file_types = list(set([
                os.path.splitext(result.get('file_path', ''))[1].lower()
                for result in results[:3]  # Only check first 3 results
            ]))[:3]  # Max 3 file types
            
            # Ultra-minimal prompt
            prompt = f"Related queries for '{query[:30]}' finding {', '.join(file_types)} files:"
            
            response = self.client.chat.completions.create(
                model=self.config.gpt_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=80,  # Very conservative limit
                temperature=0.5
            )
            
            suggestions_text = response.choices[0].message.content.strip()
            suggestions = [s.strip() for s in suggestions_text.split('\n') if s.strip()][:3]  # Max 3 suggestions
            tokens_used = response.usage.total_tokens
            
            # Log token usage
            self._log_token_usage(tokens_used)
            
            result.update({
                "suggestions": suggestions,
                "tokens_used": tokens_used,
                "ai_used": True,
                "reason": "generated",
                "cost_usd": round(tokens_used * 0.00015 / 1000, 6)
            })
            
            logger.info(f"Generated {len(suggestions)} related query suggestions (Tokens: {tokens_used})")
            return result
            
        except Exception as e:
            logger.error(f"Related query suggestion failed: {e}")
            result["reason"] = f"error: {str(e)}"
            return result
