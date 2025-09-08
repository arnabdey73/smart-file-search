"""
MCP tool for searching files.
Implements the searchFiles functionality.
"""

from mcp import types
from mcp.server import Server
from search_agent.search import SearchEngine
import logging

logger = logging.getLogger(__name__)

async def search_files_handler(arguments: dict) -> str:
    """
    Search indexed files based on query and filters.
    
    Args:
        arguments: Dict containing 'query' and optional 'filters'
        
    Returns:
        JSON string with search results
    """
    try:
        query = arguments.get('query')
        if not query:
            return "Error: query is required"
        
        filters = arguments.get('filters', {})
        
        search_engine = SearchEngine()
        results = await search_engine.search(query, filters)
        
        logger.info(f"Search completed for query: {query}")
        return str(results)
        
    except Exception as e:
        logger.error(f"Error searching files: {e}")
        return f"Error searching files: {str(e)}"

def register(server: Server):
    """Register the searchFiles tool with the MCP server."""
    
    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="searchFiles",
                description="Search indexed files using query and optional filters",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query text"
                        },
                        "filters": {
                            "type": "object",
                            "description": "Optional filters for file type, date, etc.",
                            "properties": {
                                "file_type": {"type": "string"},
                                "date_from": {"type": "string"},
                                "date_to": {"type": "string"}
                            }
                        }
                    },
                    "required": ["query"]
                }
            )
        ]
    
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        if name == "searchFiles":
            result = await search_files_handler(arguments)
            return [types.TextContent(type="text", text=result)]
        else:
            raise ValueError(f"Unknown tool: {name}")
