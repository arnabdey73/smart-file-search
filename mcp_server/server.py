"""
Main MCP server startup module.
Initializes and runs the Model Context Protocol server.
"""

import asyncio
import json
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
import uvicorn
import logging

from .config import get_config
from search_agent.indexer import FileIndexer
from search_agent.search import SearchEngine
from llm.client import GPTClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Smart File Search MCP Server")

# Global instances
indexer = None
search_engine = None
gpt_client = None

class ToolRequest(BaseModel):
    tool: str
    arguments: Dict[str, Any]

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global indexer, search_engine, gpt_client
    
    config = get_config()
    indexer = FileIndexer(config['database_path'])
    search_engine = SearchEngine(config['database_path'])
    
    try:
        gpt_client = GPTClient()
        logger.info("GPT client initialized")
    except Exception as e:
        logger.warning(f"GPT client not available: {e}")
        gpt_client = None
    
    logger.info("MCP Server started successfully")

@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "mcp-server"}

@app.get("/tools/listRoots")
async def list_roots():
    """List available root directories."""
    config = get_config()
    return {"roots": config.get('allowed_roots', [])}

@app.post("/tools/indexFolder") 
async def index_folder(request: Dict[str, Any]):
    """Index a folder."""
    try:
        root = request.get('root')
        full = request.get('full', False)
        priority = request.get('priority', 'normal')
        
        if not root:
            raise HTTPException(status_code=400, detail="root parameter required")
        
        result = await indexer.index_folder(root, full, priority)
        return result
        
    except Exception as e:
        logger.error(f"Indexing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/searchFiles")
async def search_files(request: Dict[str, Any]):
    """Search indexed files."""
    try:
        query = request.get('query')
        k = request.get('k', 10)
        offset = request.get('offset', 0)
        exts = request.get('exts', [])
        years = request.get('years', [])
        roots = request.get('roots', [])
        
        if not query:
            raise HTTPException(status_code=400, detail="query parameter required")
        
        result = await search_engine.search(
            query=query,
            k=k,
            offset=offset,
            file_extensions=exts,
            years=years,
            roots=roots
        )
        return result
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/openFile")
async def open_file(request: Dict[str, Any]):
    """Open and preview file content."""
    try:
        path = request.get('path')
        pointer = request.get('pointer')
        before = request.get('before', 200)
        after = request.get('after', 200)
        
        if not path:
            raise HTTPException(status_code=400, detail="path parameter required")
        
        result = await search_engine.get_file_preview(path, pointer, before, after)
        return result
        
    except Exception as e:
        logger.error(f"File preview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/summarizeResults")
async def summarize_results(request: Dict[str, Any]):
    """Summarize search results using AI."""
    try:
        if not gpt_client:
            raise HTTPException(status_code=503, detail="AI service not available")
        
        query = request.get('query')
        results = request.get('results', [])
        style = request.get('style', 'bullets')
        max_tokens = request.get('max_tokens', 500)
        
        if not query or not results:
            raise HTTPException(status_code=400, detail="query and results required")
        
        summary = await gpt_client.summarize_search_results(query, results, style, max_tokens)
        return {"summary": summary}
        
    except Exception as e:
        logger.error(f"Summarization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes"""
    try:
        # Check if we can access the database
        import sqlite3
        config = get_config()
        db_path = config["database_path"]
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Test database connection
        conn = sqlite3.connect(db_path)
        conn.execute("SELECT 1")
        conn.close()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "service": "smart-file-search"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Smart File Search",
        "version": "1.0.0",
        "description": "Intelligent file search system with semantic capabilities",
        "endpoints": {
            "health": "/health",
            "tools": {
                "indexFolder": "/tools/indexFolder",
                "searchFiles": "/tools/searchFiles", 
                "openFile": "/tools/openFile",
                "summarizeResults": "/tools/summarizeResults"
            }
        }
    }

def main():
    """Main server entry point."""
    config = get_config()
    host = config.get('host', '0.0.0.0')
    port = config.get('port', 9000)
    
    logger.info(f"Starting MCP server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()
