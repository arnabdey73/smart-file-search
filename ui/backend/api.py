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

from fastapi import FastAPI, HTTPException, Request, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import httpx

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from search_agent.simple_search import SimpleFileSearch
from search_agent.network_indexer import NetworkFolderIndexer
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
indexer = NetworkFolderIndexer(config)


# Pydantic models
class SearchResponse(BaseModel):
    items: List[Dict[str, Any]]
    pagination: Dict[str, int]


class SummarizeRequest(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    style: str = Field(default="bullets", pattern="^(bullets|paragraph|table)$")
    max_tokens: Optional[int] = Field(default=500, ge=50, le=1000)


class SummarizeResponse(BaseModel):
    summary: str
    tokens_used: Optional[int] = None


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


# Dependency for API key verification
async def verify_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key if authentication is enabled."""
    if config.get("require_auth", False):
        if not credentials:
            raise HTTPException(status_code=401, detail="API key required")
        
        if not verify_api_key(credentials.credentials):
            raise HTTPException(status_code=403, detail="Invalid API key")
    
    return credentials


# MCP client for backend communication
class MCPClient:
    """Client for communicating with MCP server."""
    
    def __init__(self):
        self.base_url = config.get("mcp_server_url", "http://localhost:9000")
        self.timeout = config.get("mcp_timeout", 30)
    
    async def call_tool(self, tool_name: str, arguments: Dict) -> Any:
        """Call MCP tool via HTTP."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/tools/{tool_name}",
                    json=arguments
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"MCP request failed: {e}")
                raise HTTPException(status_code=502, detail="Backend service unavailable")


mcp_client = MCPClient()


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log requests and responses."""
    start_time = time.time()
    
    # Log request
    log_request(request)
    
    # Process request
    response = await call_next(request)
    
    # Log response time
    process_time = time.time() - start_time
    logger.info(f"Request completed in {process_time:.2f}s")
    
    return response


@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC"),
        version="1.0.0"
    )


@app.get("/api/roots")
async def get_roots(auth: Any = Depends(verify_auth)):
    """Get list of available root directories."""
    try:
        result = await mcp_client.call_tool("listRoots", {})
        return {"roots": result.get("roots", [])}
    except Exception as e:
        logger.error(f"Error getting roots: {e}")
        return format_error_response("Failed to get roots", 500)


@app.get("/api/search", response_model=SearchResponse)
async def search_files(
    query: str = Query(..., description="Search query"),
    k: int = Query(10, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Results offset"),
    exts: Optional[str] = Query(None, description="Comma-separated file extensions"),
    years: Optional[str] = Query(None, description="Comma-separated years"),
    roots: Optional[str] = Query(None, description="Comma-separated root paths"),
    auth: Any = Depends(verify_auth)
):
    """Search indexed files."""
    try:
        # Prepare arguments
        arguments = {
            "query": query,
            "k": k,
            "offset": offset
        }
        
        if exts:
            arguments["exts"] = [ext.strip() for ext in exts.split(",")]
        if years:
            arguments["years"] = [year.strip() for year in years.split(",")]
        if roots:
            arguments["roots"] = [root.strip() for root in roots.split(",")]
        
        # Call MCP tool
        result = await mcp_client.call_tool("searchFiles", arguments)
        
        return SearchResponse(
            items=result.get("items", []),
            pagination=result.get("pagination", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@app.get("/api/file-preview")
async def get_file_preview(
    path: str = Query(..., description="File path"),
    pointer: Optional[str] = Query(None, description="Document pointer"),
    before: int = Query(200, ge=0, le=1000, description="Characters before"),
    after: int = Query(200, ge=0, le=1000, description="Characters after"),
    auth: Any = Depends(verify_auth)
):
    """Get file preview with context."""
    try:
        arguments = {
            "path": path,
            "before": before,
            "after": after
        }
        
        if pointer:
            arguments["pointer"] = pointer
        
        result = await mcp_client.call_tool("openFile", arguments)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File preview error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get file preview")


@app.post("/api/summarize", response_model=SummarizeResponse)
async def summarize_results(
    request: SummarizeRequest,
    auth: Any = Depends(verify_auth)
):
    """Summarize search results using AI."""
    try:
        arguments = {
            "query": request.query,
            "results": request.results,
            "style": request.style,
            "max_tokens": request.max_tokens
        }
        
        result = await mcp_client.call_tool("summarizeResults", arguments)
        
        return SummarizeResponse(
            summary=result.get("summary", ""),
            tokens_used=result.get("tokens_used")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Summarization error: {e}")
        raise HTTPException(status_code=500, detail="Summarization failed")


@app.post("/api/index")
async def trigger_indexing(
    root: str = Query(..., description="Root path to index"),
    full: bool = Query(False, description="Force full reindex"),
    priority: str = Query("normal", pattern="^(low|normal|high)$"),
    auth: Any = Depends(verify_auth)
):
    """Trigger indexing of a folder."""
    try:
        arguments = {
            "root": root,
            "full": full,
            "priority": priority
        }
        
        result = await mcp_client.call_tool("indexFolder", arguments)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Indexing error: {e}")
        raise HTTPException(status_code=500, detail="Indexing failed")


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return format_error_response("Not found", 404)


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    return format_error_response("Internal server error", 500)


if __name__ == "__main__":
    import uvicorn
    
    host = config.get("host", "0.0.0.0")
    port = config.get("port", 8081)
    
    uvicorn.run(app, host=host, port=port)
