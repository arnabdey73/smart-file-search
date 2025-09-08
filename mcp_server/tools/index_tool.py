"""
MCP tool for indexing folders.
Implements the indexFolder functionality.
"""

from mcp import types
from mcp.server import Server
from search_agent.indexer import FileIndexer
import logging

logger = logging.getLogger(__name__)

async def index_folder_handler(arguments: dict) -> str:
    """
    Index files in the specified folder.
    
    Args:
        arguments: Dict containing 'folder_path'
        
    Returns:
        Status message about indexing operation
    """
    try:
        folder_path = arguments.get('folder_path')
        if not folder_path:
            return "Error: folder_path is required"
        
        indexer = FileIndexer()
        result = await indexer.index_folder(folder_path)
        
        logger.info(f"Indexed folder: {folder_path}")
        return f"Successfully indexed {result['files_processed']} files from {folder_path}"
        
    except Exception as e:
        logger.error(f"Error indexing folder: {e}")
        return f"Error indexing folder: {str(e)}"

def register(server: Server):
    """Register the indexFolder tool with the MCP server."""
    
    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="indexFolder",
                description="Index files in a specified folder for searching",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "folder_path": {
                            "type": "string",
                            "description": "Path to the folder to index"
                        }
                    },
                    "required": ["folder_path"]
                }
            )
        ]
    
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        if name == "indexFolder":
            result = await index_folder_handler(arguments)
            return [types.TextContent(type="text", text=result)]
        else:
            raise ValueError(f"Unknown tool: {name}")
