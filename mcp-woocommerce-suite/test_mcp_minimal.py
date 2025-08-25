"""
Minimal MCP server test for debugging Claude Desktop connection
"""

import os
import logging
from mcp.server.fastmcp import FastMCP

# Configure logging to see what's happening
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create minimal FastMCP app
mcp = FastMCP("Test Server")

@mcp.tool()
def test_tool() -> str:
    """A simple test tool"""
    return "Hello from MCP!"

@mcp.tool()
def check_env() -> str:
    """Check environment variables"""
    store_url = os.getenv('STORE_URL', 'Not set')
    key = os.getenv('WOOCOMMERCE_KEY', 'Not set')
    secret = os.getenv('WOOCOMMERCE_SECRET', 'Not set')
    
    return f"STORE_URL: {store_url}\nWOOCOMMERCE_KEY: {key[:20]}...\nWOOCOMMERCE_SECRET: {secret[:20]}..."

if __name__ == "__main__":
    logger.info("Starting minimal MCP server...")
    mcp.run(transport="stdio")