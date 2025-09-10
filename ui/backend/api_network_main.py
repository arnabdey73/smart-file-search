"""
FastAPI backend for the smart file search UI.
Provides REST API endpoints optimized for Windows network folders.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from search_agent.simple_search import SimpleFileSearch
from search_agent.network_indexer import NetworkFolderIndexer
from search_agent.search import SearchEngine
from search_agent.config import SearchConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Smart File Search API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
config = SearchConfig()
search_engine = SimpleFileSearch(config)
enhanced_search_engine = SearchEngine()  # AI-enhanced search engine
indexer = NetworkFolderIndexer(config)

# Pydantic models
class SearchRequest(BaseModel):
    query: str
    max_results: int = 10
    file_extensions: Optional[List[str]] = None
    use_ai: bool = False

class SearchResult(BaseModel):
    file_path: str
    snippet: str
    score: float
    last_modified: Optional[str] = None
    file_size: Optional[int] = None

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_results: int
    query_time_ms: float
    ai_enhancement: Optional[Dict[str, Any]] = None

class NetworkPathRequest(BaseModel):
    path: str

class NetworkPathValidation(BaseModel):
    accessible: bool
    file_count: Optional[int] = None
    error: Optional[str] = None

class IndexRequest(BaseModel):
    network_path: str
    quick_scan: bool = True

class NetworkFolder(BaseModel):
    path: str
    file_count: int
    last_indexed: Optional[str] = None
    total_size_mb: float
    accessible: bool

class SummarizeRequest(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    style: str = "bullets"  # bullets, paragraph, table

class SummarizeResponse(BaseModel):
    summary: str
    related_queries: List[str]
    ai_usage: Optional[Dict[str, Any]] = None  # Token usage and cost information

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

@app.post("/api/validate-path", response_model=NetworkPathValidation)
async def validate_network_path(request: NetworkPathRequest):
    """Validate if a network path is accessible"""
    try:
        path = request.path.strip()
        if not path:
            return NetworkPathValidation(accessible=False, error="Path cannot be empty")
        
        # Check if path exists and is accessible
        path_obj = Path(path)
        if not path_obj.exists():
            return NetworkPathValidation(accessible=False, error="Path does not exist")
        
        if not path_obj.is_dir():
            return NetworkPathValidation(accessible=False, error="Path is not a directory")
        
        # Try to list contents to verify access
        try:
            files = list(path_obj.rglob("*"))
            file_count = len([f for f in files if f.is_file()])
            return NetworkPathValidation(accessible=True, file_count=file_count)
        except PermissionError:
            return NetworkPathValidation(accessible=False, error="Access denied")
        
    except Exception as e:
        logger.error(f"Error validating path {request.path}: {e}")
        return NetworkPathValidation(accessible=False, error=f"Validation error: {str(e)}")

@app.post("/api/index")
async def index_folder(request: IndexRequest):
    """Index a network folder"""
    try:
        path = request.network_path.strip()
        if not path:
            raise HTTPException(status_code=400, detail="Path cannot be empty")
        
        # Validate path first
        path_obj = Path(path)
        if not path_obj.exists() or not path_obj.is_dir():
            raise HTTPException(status_code=400, detail="Invalid path")
        
        # Start indexing (this might take a while for large folders)
        result = indexer.index_network_folder(path, quick_scan=request.quick_scan)
        
        return {
            "success": True,
            "message": f"Indexed {result.get('files_indexed', 0)} files",
            "details": result
        }
        
    except Exception as e:
        logger.error(f"Error indexing folder {request.network_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Indexing error: {str(e)}")

@app.get("/api/network-folders")
async def get_network_folders():
    """Get list of indexed network folders"""
    try:
        folders = []
        
        # Get folders from config
        for folder_path in config.get_allowed_paths():
            try:
                path_obj = Path(folder_path)
                accessible = path_obj.exists() and path_obj.is_dir()
                
                # Get stats from database if available
                stats = search_engine.get_folder_stats(folder_path)
                
                folder_info = NetworkFolder(
                    path=folder_path,
                    file_count=stats.get('file_count', 0),
                    last_indexed=stats.get('last_indexed'),
                    total_size_mb=stats.get('total_size_mb', 0.0),
                    accessible=accessible
                )
                folders.append(folder_info)
                
            except Exception as e:
                logger.warning(f"Error getting stats for folder {folder_path}: {e}")
                # Add folder with error state
                folder_info = NetworkFolder(
                    path=folder_path,
                    file_count=0,
                    total_size_mb=0.0,
                    accessible=False
                )
                folders.append(folder_info)
        
        return {"folders": folders}
        
    except Exception as e:
        logger.error(f"Error getting network folders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search", response_model=SearchResponse)
async def search_files(request: SearchRequest):
    """Search indexed files with optional AI enhancement"""
    try:
        start_time = time.time()
        
        if request.use_ai:
            # Use AI-enhanced search engine
            results_dict = await enhanced_search_engine.search(
                query=request.query,
                k=request.max_results,
                file_extensions=request.file_extensions,
                enable_ai=True
            )
            
            results = results_dict.get('items', [])
            ai_enhancement = results_dict.get('ai_enhancement')
            
            # Convert results to response format
            search_results = []
            for result in results:
                search_result = SearchResult(
                    file_path=result.get('path', ''),
                    snippet=result.get('snippet', ''),
                    score=result.get('score', 0.0),
                    last_modified=result.get('modified'),
                    file_size=None  # Not available in enhanced search
                )
                search_results.append(search_result)
        else:
            # Use simple search engine (legacy)
            results = search_engine.search(
                query=request.query,
                max_results=request.max_results,
                file_extensions=request.file_extensions
            )
            
            # Convert results to response format
            search_results = []
            for result in results:
                search_result = SearchResult(
                    file_path=result.get('file_path', ''),
                    snippet=result.get('snippet', ''),
                    score=result.get('score', 0.0),
                    last_modified=result.get('last_modified'),
                    file_size=result.get('file_size')
                )
                search_results.append(search_result)
            
            ai_enhancement = None
        
        query_time_ms = (time.time() - start_time) * 1000
        
        return SearchResponse(
            results=search_results,
            total_results=len(search_results),
            query_time_ms=query_time_ms,
            ai_enhancement=ai_enhancement
        )
        
    except Exception as e:
        logger.error(f"Error searching: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@app.get("/api/token-usage")
async def get_token_usage():
    """Get current token usage statistics and limits."""
    try:
        ai_enhancer = enhanced_search_engine.ai_enhancer
        
        if not ai_enhancer:
            return {"error": "AI enhancer not available"}
            
        stats = ai_enhancer.get_token_usage_stats()
        return {
            "status": "success",
            "token_usage": stats,
            "limits": {
                "daily_limit": ai_enhancer.daily_token_limit,
                "per_request_limit": ai_enhancer.max_tokens_per_request
            },
            "pricing": {
                "model": "gpt-4o-mini",
                "cost_per_1k_tokens": 0.00015,
                "estimated_queries_remaining": max(0, int(stats.get("remaining_tokens", 0) / 50))  # Assume ~50 tokens per query
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting token usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/enhance-query")
async def enhance_query(request: dict):
    """Enhance a search query using AI with token tracking."""
    try:
        query = request.get("query", "")
        force = request.get("force", False)
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
            
        ai_enhancer = enhanced_search_engine.ai_enhancer
        
        if not ai_enhancer:
            return {
                "enhanced_query": query,
                "tokens_used": 0,
                "ai_used": False,
                "reason": "ai_not_available"
            }
            
        result = ai_enhancer.enhance_query(query, force=force)
        return result
        
    except Exception as e:
        logger.error(f"Error enhancing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/set-limits")
async def set_token_limits(request: dict):
    """Update token usage limits (admin endpoint)."""
    try:
        ai_enhancer = enhanced_search_engine.ai_enhancer
        
        if not ai_enhancer:
            raise HTTPException(status_code=400, detail="AI enhancer not available")
            
        daily_limit = request.get("daily_limit")
        per_request_limit = request.get("per_request_limit")
        
        if daily_limit and daily_limit > 0:
            ai_enhancer.daily_token_limit = daily_limit
            logger.info(f"Daily token limit updated to: {daily_limit}")
            
        if per_request_limit and per_request_limit > 0:
            ai_enhancer.max_tokens_per_request = per_request_limit
            logger.info(f"Per-request token limit updated to: {per_request_limit}")
            
        return {
            "status": "success",
            "new_limits": {
                "daily_limit": ai_enhancer.daily_token_limit,
                "per_request_limit": ai_enhancer.max_tokens_per_request
            }
        }
        
    except Exception as e:
        logger.error(f"Error setting token limits: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/summarize", response_model=SummarizeResponse)
async def summarize_results(request: SummarizeRequest):
    """Generate AI summary and related queries for search results"""
    try:
        ai_enhancer = enhanced_search_engine.ai_enhancer
        
        if not ai_enhancer.is_available():
            raise HTTPException(status_code=503, detail="AI features not available")
        
        # Generate summary with token tracking
        summary_result = ai_enhancer.summarize_results(
            query=request.query,
            results=request.results,
            style=request.style,
            force=request.get("force_ai", False)
        )
        
        # Generate related queries with token tracking
        queries_result = ai_enhancer.suggest_related_queries(
            query=request.query,
            results=request.results,
            force=request.get("force_ai", False)
        )
        
        return SummarizeResponse(
            summary=summary_result.get("summary", ""),
            related_queries=queries_result.get("suggestions", []),
            ai_usage={
                "summary": {
                    "tokens_used": summary_result.get("tokens_used", 0),
                    "ai_used": summary_result.get("ai_used", False),
                    "cost_usd": summary_result.get("cost_usd", 0),
                    "reason": summary_result.get("reason", "")
                },
                "related_queries": {
                    "tokens_used": queries_result.get("tokens_used", 0),
                    "ai_used": queries_result.get("ai_used", False),
                    "cost_usd": queries_result.get("cost_usd", 0),
                    "reason": queries_result.get("reason", "")
                },
                "total_tokens": summary_result.get("tokens_used", 0) + queries_result.get("tokens_used", 0),
                "total_cost_usd": summary_result.get("cost_usd", 0) + queries_result.get("cost_usd", 0)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail=f"Summary error: {str(e)}")

@app.get("/api/ai-status")
async def get_ai_status():
    """Check AI features availability"""
    try:
        ai_enhancer = enhanced_search_engine.ai_enhancer
        return {
            "available": ai_enhancer.is_available(),
            "features": {
                "query_enhancement": config.enable_query_rewrite,
                "summarization": config.enable_summarization,
                "related_queries": ai_enhancer.is_available()
            }
        }
    except Exception as e:
        logger.error(f"Error checking AI status: {e}")
        return {
            "available": False,
            "error": str(e)
        }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Smart File Search API server...")
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
