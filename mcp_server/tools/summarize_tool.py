"""
MCP tool for summarizing search results.
Implements the summarizeResults functionality.
"""

from mcp import types
from mcp.server import Server
from llm.client import GPTClient
import logging
import json

logger = logging.getLogger(__name__)

async def summarize_results_handler(arguments: dict) -> str:
    """
    Summarize search results using LLM.
    
    Args:
        arguments: Dict containing 'results'
        
    Returns:
        Summarized results as string
    """
    try:
        results = arguments.get('results')
        if not results:
            return "Error: results are required"
        
        # Parse results if it's a string
        if isinstance(results, str):
            try:
                results = json.loads(results)
            except json.JSONDecodeError:
                pass
        
        gpt_client = GPTClient()
        summary = await gpt_client.summarize_search_results(results)
        
        logger.info("Search results summarized successfully")
        return summary
        
    except Exception as e:
        logger.error(f"Error summarizing results: {e}")
        return f"Error summarizing results: {str(e)}"

def register(server: Server):
    """Register the summarizeResults tool with the MCP server."""
    
    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="summarizeResults",
                description="Summarize search results using AI",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "results": {
                            "type": ["string", "array", "object"],
                            "description": "Search results to summarize"
                        }
                    },
                    "required": ["results"]
                }
            )
        ]
    
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        if name == "summarizeResults":
            result = await summarize_results_handler(arguments)
            return [types.TextContent(type="text", text=result)]
        else:
            raise ValueError(f"Unknown tool: {name}")
