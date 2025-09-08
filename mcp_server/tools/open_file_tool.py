"""
MCP tool for opening and reading files.
Implements the openFile functionality.
"""

from mcp import types
from mcp.server import Server
import os
import logging

logger = logging.getLogger(__name__)

async def open_file_handler(arguments: dict) -> str:
    """
    Open and read file content.
    
    Args:
        arguments: Dict containing 'file_path'
        
    Returns:
        File content as string
    """
    try:
        file_path = arguments.get('file_path')
        if not file_path:
            return "Error: file_path is required"
        
        if not os.path.exists(file_path):
            return f"Error: File not found: {file_path}"
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        logger.info(f"Opened file: {file_path}")
        return content
        
    except Exception as e:
        logger.error(f"Error opening file: {e}")
        return f"Error opening file: {str(e)}"

def register(server: Server):
    """Register the openFile tool with the MCP server."""
    
    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="openFile",
                description="Open and read the content of a file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to open"
                        }
                    },
                    "required": ["file_path"]
                }
            )
        ]
    
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        if name == "openFile":
            result = await open_file_handler(arguments)
            return [types.TextContent(type="text", text=result)]
        else:
            raise ValueError(f"Unknown tool: {name}")
