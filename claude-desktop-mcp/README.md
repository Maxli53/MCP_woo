# Claude Desktop MCP Server

Lightweight MCP server for WooCommerce management through Claude Desktop.

## Overview

This is a standalone MCP (Model Context Protocol) server that enables Claude Desktop to directly manage your WooCommerce store through natural language commands.

## Features

- 🤖 **Direct Claude Integration** - Native Claude Desktop support
- 🛍️ **Single Store Focus** - Optimized for one store
- ⚡ **Lightweight** - Minimal dependencies
- 🔧 **Simple Configuration** - Environment variables only
- 📡 **Stdio Communication** - Direct pipe to Claude

## Available Tools

| Tool | Description |
|------|-------------|
| `list_products` | List products with pagination |
| `get_product` | Get product details |
| `search_products` | Search with filters |
| `update_product` | Update product info |
| `create_product` | Create new product |
| `get_orders` | View recent orders |
| `get_store_stats` | Store statistics |
| `get_categories` | List categories |

## Setup

### 1. Install Dependencies

```batch
pip install mcp woocommerce httpx
```

### 2. Configure Claude Desktop

Add to your Claude Desktop config (`%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "woocommerce": {
      "command": "python",
      "args": ["C:\\path\\to\\claude-desktop-mcp\\mcp_server.py"],
      "env": {
        "STORE_URL": "https://your-store.com",
        "WOOCOMMERCE_KEY": "ck_xxxxxxxxxxxxx",
        "WOOCOMMERCE_SECRET": "cs_xxxxxxxxxxxxx"
      }
    }
  }
}
```

### 3. Get WooCommerce Credentials

1. Login to WooCommerce admin
2. Go to: WooCommerce → Settings → Advanced → REST API
3. Click "Add key"
4. Set Description: "Claude Desktop MCP"
5. Set Permissions: "Read/Write"
6. Generate and copy keys

### 4. Restart Claude Desktop

The MCP server will load automatically.

## Usage Examples

Once configured, ask Claude:

- "What products do I have in my store?"
- "Show me orders from last week"
- "Update product ID 123 to $49.99"
- "Search for products with 'shirt' in the name"
- "What are my store statistics?"
- "Create a new product called 'Test Product'"

## Project Structure

```
claude-desktop-mcp/
├── mcp_server.py       # Main MCP server
├── tools/              # Tool implementations
│   ├── products.py     # Product tools
│   ├── orders.py       # Order tools
│   └── store.py        # Store info tools
├── config.example.json # Example config
└── README.md          # This file
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `STORE_URL` | WooCommerce URL | `https://mystore.com` |
| `WOOCOMMERCE_KEY` | Consumer Key | `ck_1234567890abcdef` |
| `WOOCOMMERCE_SECRET` | Consumer Secret | `cs_abcdef1234567890` |

## Testing

### Test Standalone
```batch
set STORE_URL=https://your-store.com
set WOOCOMMERCE_KEY=ck_xxxxx
set WOOCOMMERCE_SECRET=cs_xxxxx
python mcp_server.py
```

### Check Claude Desktop Logs
```
%APPDATA%\Claude\logs\
```

## Troubleshooting

### MCP Not Loading
1. Check Claude Desktop config syntax
2. Verify Python path is correct
3. Restart Claude Desktop

### Authentication Errors
1. Verify API keys are correct
2. Check store URL (with/without trailing slash)
3. Ensure REST API is enabled

### Connection Issues
1. Check internet connection
2. Verify store is accessible
3. Check firewall settings

## Limitations

- Single store only (by design)
- No persistent storage
- No bulk operations (use web platform)
- Read-heavy operations preferred

## Security

- Credentials stored in Claude Desktop config
- No logging of sensitive data
- Stateless operation
- HTTPS required for store URL

## Development

### Add New Tool
Create in `tools/custom.py`:
```python
@mcp.tool()
def custom_tool(param: str) -> str:
    """Tool description"""
    return f"Result: {param}"
```

## Comparison with Web Platform

| Feature | This MCP | Web Platform |
|---------|----------|--------------|
| Interface | Claude Desktop | Web Browser |
| Stores | Single | Multiple |
| Storage | None | Database |
| Bulk Ops | No | Yes |
| Best For | Quick tasks | Management |

## Support

- Check environment variables
- Verify WooCommerce REST API enabled
- Test with curl first if issues persist