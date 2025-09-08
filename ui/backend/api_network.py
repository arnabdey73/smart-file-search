"""FastAPI backend optimized for Windows network folder search."""
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import os
import sys
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import our search components
from search_agent.simple_search import SimpleFileSearch
from search_agent.network_indexer import NetworkFolderIndexer
from search_agent.config import config

# Initialize FastAPI app
app = FastAPI(
    title="Smart File Search API",
    description="Fast search for Windows network folders",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
searcher = SimpleFileSearch()
indexer = NetworkFolderIndexer()

logger = logging.getLogger(__name__)

# Pydantic models
class IndexRequest(BaseModel):
    network_path: str
    quick_scan: bool = True

class SearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 50
    file_types: Optional[List[str]] = None
    network_paths: Optional[List[str]] = None
    modified_after: Optional[str] = None

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Smart File Search API",
        "database": "connected" if os.path.exists(searcher.db_path) else "not_found"
    }

@app.get("/api/network-folders")
async def get_network_folders():
    """Get list of available network folders."""
    try:
        folders = indexer.get_network_folders()
        
        # Add accessibility check
        for folder in folders:
            folder['accessible'] = os.path.exists(folder['path'])
            
        return {
            "folders": folders,
            "configured_paths": config.allowed_network_paths
        }
    except Exception as e:
        logger.error(f"Error getting network folders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/validate-path")
async def validate_network_path(path: str):
    """Validate if a network path is accessible."""
    try:
        # Normalize the path
        normalized_path = os.path.normpath(path)
        
        # Check if path exists and is accessible
        accessible = os.path.exists(normalized_path)
        
        # Get basic info if accessible
        info = {
            "path": normalized_path,
            "accessible": accessible,
            "is_network_path": normalized_path.startswith("\\\\"),
            "error": None
        }
        
        if accessible:
            try:
                # Try to list directory contents
                files = os.listdir(normalized_path)
                info["file_count"] = len(files)
                info["sample_files"] = files[:5]  # First 5 files as samples
            except PermissionError:
                info["error"] = "Permission denied"
                info["accessible"] = False
            except Exception as e:
                info["error"] = str(e)
                info["accessible"] = False
        else:
            info["error"] = "Path not found or not accessible"
            
        return info
        
    except Exception as e:
        logger.error(f"Error validating path: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/index")
async def index_folder(request: IndexRequest):
    """Index a Windows network folder."""
    try:
        # Validate path first
        if not os.path.exists(request.network_path):
            raise HTTPException(
                status_code=404,
                detail=f"Network path not accessible: {request.network_path}"
            )
            
        # Start indexing
        stats = indexer.index_network_folder(request.network_path, request.quick_scan)
        
        return {
            "status": "success",
            "network_path": request.network_path,
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error indexing folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search")
async def search_files(request: SearchRequest):
    """Search files in indexed network folders."""
    try:
        # Perform search
        results = searcher.search(
            query=request.query,
            max_results=request.max_results,
            file_types=request.file_types,
            network_paths=request.network_paths,
            modified_after=request.modified_after
        )
        
        return {
            "query": request.query,
            "results": results,
            "total_found": len(results),
            "search_time_ms": 0  # Add timing if needed
        }
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search")
async def search_files_get(
    query: str = Query(..., min_length=2, description="Search query"),
    max_results: Optional[int] = Query(50, ge=1, le=200),
    file_types: Optional[str] = Query(None, description="Comma-separated file extensions"),
    network_paths: Optional[str] = Query(None, description="Comma-separated network paths"),
    modified_after: Optional[str] = Query(None, description="ISO date string (YYYY-MM-DD)")
):
    """Search files in indexed network folders (GET method for easy testing)."""
    try:
        # Parse filters
        file_types_list = []
        if file_types:
            file_types_list = [ext.strip() for ext in file_types.split(',')]
            
        network_paths_list = []
        if network_paths:
            network_paths_list = [path.strip() for path in network_paths.split(',')]
            
        # Perform search
        results = searcher.search(
            query=query,
            max_results=max_results,
            file_types=file_types_list,
            network_paths=network_paths_list,
            modified_after=modified_after
        )
        
        return {
            "query": query,
            "results": results,
            "total_found": len(results),
            "search_time_ms": 0  # Add timing if needed
        }
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/file-preview")
async def get_file_preview(
    file_path: str = Query(..., description="Full file path"),
    max_chars: int = Query(2000, ge=100, le=10000)
):
    """Get preview of a file from network folder."""
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
            
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(max_chars)
                
            return {
                "file_path": file_path,
                "content": content,
                "truncated": len(content) >= max_chars
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File preview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_search_stats():
    """Get search index statistics."""
    try:
        stats = searcher.get_search_stats()
        return stats
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=20)
):
    """Get search suggestions."""
    try:
        suggestions = searcher.get_search_suggestions(query, limit)
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error(f"Suggestions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Serve static files (frontend)
try:
    frontend_path = Path(__file__).parent.parent / "frontend" / "dist"
    if frontend_path.exists():
        app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="static")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
