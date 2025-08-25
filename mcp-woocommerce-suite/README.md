# MCP WooCommerce Suite

A professional web-based WooCommerce store management system built with Python, FastAPI, and the Model Context Protocol (MCP).

## Features

- 🛒 **Multi-Store Management** - Connect and manage multiple WooCommerce stores
- 📦 **Product Management** - Import, export, and bulk manage products
- 📊 **Data Processing** - Full pandas/numpy support for Excel and CSV operations
- 🔄 **Bulk Operations** - Mass updates for prices, categories, and inventory
- 🌐 **REST API** - Complete API for automation and integrations
- 💻 **Web Interface** - Modern, responsive browser-based UI
- 🤖 **Claude Desktop Integration** - Direct store management through MCP protocol

## Requirements

- Windows 10/11
- Python 3.11 (required for pandas/numpy compatibility)
- 2GB RAM minimum
- Modern web browser

## Quick Start

### 1. Setup
```batch
setup.bat
```
This will:
- Create a Python 3.11 virtual environment
- Install all required packages
- Configure the system

### 2. Run
```batch
start.bat
```
This will:
- Start the web server on http://localhost:8000
- Open your browser automatically
- Display the management interface

## Project Structure

```
mcp-woocommerce-suite/
├── main.py                 # Main application entry point
├── web_server.py           # FastAPI web server
├── setup.bat              # One-click setup script
├── start.bat              # Application launcher
├── requirements.txt       # Python dependencies
├── src/
│   ├── config/           # Configuration modules
│   ├── mcp_server/       # MCP server implementation
│   │   ├── claude_desktop_mcp.py  # Claude Desktop MCP server
│   │   └── woocommerce_mcp.py     # Web MCP server
│   ├── gui/              # Desktop GUI components
│   ├── utils/            # Utility modules
│   └── web/              # Web interface components
├── data/                 # Application data (created on first run)
│   ├── stores/          # Store configurations
│   ├── logs/            # Application logs
│   └── backups/         # Data backups
├── resources/           # UI resources
│   ├── icons/          # Application icons
│   └── templates/      # HTML templates
└── venv/               # Python virtual environment
```

## API Endpoints

The application provides a REST API accessible at http://localhost:8000

### Core Endpoints
- `GET /` - Web interface
- `GET /api/status` - System status
- `GET /api/stores` - List all stores
- `POST /api/stores` - Add a new store
- `GET /api/products` - List products
- `GET /docs` - Interactive API documentation

### Example: Add a Store
```bash
curl -X POST http://localhost:8000/api/stores \
  -H "Content-Type: application/json" \
  -d '{"name":"My Store","url":"https://mystore.com","id":"store1"}'
```

## WooCommerce Integration

### Getting WooCommerce API Credentials

1. Log into your WooCommerce admin panel
2. Go to WooCommerce → Settings → Advanced → REST API
3. Click "Add key"
4. Set permissions to "Read/Write"
5. Copy the Consumer Key and Consumer Secret

### Adding a Store

1. Open the web interface at http://localhost:8000
2. Click "Add Store"
3. Enter your store details and API credentials
4. Click "Save"

## Data Processing

The suite includes powerful data processing capabilities:

- **Import**: CSV and Excel files
- **Export**: CSV, Excel with formatting
- **Bulk Updates**: Modify multiple products at once
- **Data Validation**: Automatic validation before operations

## Configuration

Create a `.env` file from the template:
```batch
copy .env.example .env
```

Edit `.env` to configure:
- API settings
- Database preferences
- Security options
- Notification settings

## Troubleshooting

### Port 8000 Already in Use
The start script automatically clears port 8000. If issues persist:
```batch
netstat -an | findstr :8000
taskkill /F /PID [process_id]
```

### Python Version Issues
This project requires Python 3.11 for full compatibility:
```batch
py -3.11 --version
```
If not installed, download from: https://www.python.org/downloads/release/python-3119/

### Package Installation Issues
If packages fail to install:
```batch
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Claude Desktop Integration

The suite includes a dedicated MCP (Model Context Protocol) server for Claude Desktop integration, allowing you to manage your WooCommerce store directly through Claude Desktop.

### Setup Claude Desktop MCP

1. **Configure Claude Desktop** with your store credentials in `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "woocommerce-store-manager": {
      "command": "C:\\path\\to\\your\\venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\your\\src\\mcp_server\\claude_desktop_mcp.py"],
      "env": {
        "STORE_URL": "https://your-store.com/",
        "WOOCOMMERCE_KEY": "your_consumer_key",
        "WOOCOMMERCE_SECRET": "your_consumer_secret"
      }
    }
  }
}
```

2. **Restart Claude Desktop** to load the MCP server

3. **Available MCP Tools**:
   - `list_products` - List store products with pagination/search
   - `get_product` - Get detailed product information
   - `search_products` - Advanced product search with filters
   - `get_store_stats` - Store overview and statistics
   - `get_orders` - List recent orders
   - `update_product` - Update product information
   - `create_product` - Create new products
   - `get_categories` - List product categories

### Usage Examples

After setup, you can interact with your store through Claude Desktop:
- "What products do I have in my store?"
- "Show me my recent orders"
- "Update product ID 123 price to $99.99"
- "Search for products containing 'snowmobile'"

## Development

### Extending the API
Edit `web_server.py` to add new endpoints:
```python
@app.get('/api/custom')
async def custom_endpoint():
    return {"message": "Custom endpoint"}
```

### Adding WooCommerce Features
The `src/mcp_server/woocommerce_mcp.py` contains the MCP implementation for advanced features.

## Security

- API credentials are encrypted when stored
- .env file should never be committed to version control
- Use HTTPS in production environments
- Regular backups are recommended

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the API documentation at `/docs`
3. Check the logs in `data/logs/`

## License

MIT License - See LICENSE file for details

## Acknowledgments

- FastAPI for the excellent web framework
- WooCommerce for the e-commerce platform
- MCP protocol for standardized tool interfaces

---

**Version**: 1.0.0  
**Python**: 3.11  
**Status**: Production Ready