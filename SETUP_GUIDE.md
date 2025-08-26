# WooCommerce Enterprise MCP Suite - Setup Guide

## Complete Installation & Configuration Guide

This guide provides step-by-step instructions for setting up the WooCommerce Enterprise MCP Suite with Claude Desktop.

---

## Prerequisites

Before you begin, ensure you have:

- ✅ **Python 3.9 or higher** (3.11+ recommended)
- ✅ **Claude Desktop** installed and configured
- ✅ **WooCommerce store** with REST API enabled
- ✅ **API credentials** (Consumer Key and Consumer Secret)
- ✅ **Administrator access** to your system
- ✅ **Git** (for cloning the repository)

---

## Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/woocommerce-mcp-suite.git

# Navigate to the project directory
cd MCP
```

---

## Step 2: Create Python Virtual Environment

### Windows
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Verify activation (should show venv path)
where python
```

### macOS/Linux
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify activation
which python
```

---

## Step 3: Install Dependencies

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install required packages
pip install fastmcp woocommerce httpx python-dotenv beautifulsoup4

# Optional: Install additional packages for full functionality
pip install pandas numpy PyQt6 psutil schedule

# Verify installation
python -c "import fastmcp; import woocommerce; print('Core packages installed successfully')"
```

---

## Step 4: Configure WooCommerce Credentials

### Option A: Using Environment File (Recommended)

1. Create `.env` file in the project root:

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

2. Edit `.env` file with your credentials:

```env
# WooCommerce API Credentials
STORE_URL=https://yourstore.com
CONSUMER_KEY=ck_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CONSUMER_SECRET=cs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional Settings
API_VERSION=wc/v3
TIMEOUT=30
MAX_RETRIES=3
RATE_LIMIT=10
LOG_LEVEL=INFO

# Multi-Store Configuration (if applicable)
STORE_2_URL=https://store2.com
STORE_2_KEY=ck_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
STORE_2_SECRET=cs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Option B: Direct Configuration in Claude Desktop

Skip creating `.env` and configure directly in Claude Desktop config (see Step 5).

---

## Step 5: Configure Claude Desktop

### Windows

1. Open Claude Desktop configuration file:
```bash
# Open in notepad
notepad %APPDATA%\Claude\claude_desktop_config.json

# Or navigate to:
# C:\Users\[YourUsername]\AppData\Roaming\Claude\
```

2. Add the MCP server configuration:

```json
{
  "mcpServers": {
    "woocommerce-enterprise": {
      "command": "C:\\Users\\[YourUsername]\\path\\to\\MCP\\venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\[YourUsername]\\path\\to\\MCP\\claude-desktop-mcp\\enhanced\\core.py"],
      "env": {
        "STORE_URL": "https://yourstore.com",
        "CONSUMER_KEY": "ck_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "CONSUMER_SECRET": "cs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "PYTHONPATH": "C:\\Users\\[YourUsername]\\path\\to\\MCP"
      }
    }
  }
}
```

### macOS

1. Open configuration file:
```bash
open ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

2. Add configuration:
```json
{
  "mcpServers": {
    "woocommerce-enterprise": {
      "command": "/Users/[YourUsername]/path/to/MCP/venv/bin/python",
      "args": ["/Users/[YourUsername]/path/to/MCP/claude-desktop-mcp/enhanced/core.py"],
      "env": {
        "STORE_URL": "https://yourstore.com",
        "CONSUMER_KEY": "ck_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "CONSUMER_SECRET": "cs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "PYTHONPATH": "/Users/[YourUsername]/path/to/MCP"
      }
    }
  }
}
```

### Linux

1. Open configuration file:
```bash
nano ~/.config/Claude/claude_desktop_config.json
```

2. Add configuration (similar to macOS).

---

## Step 6: Enable WooCommerce REST API

1. **Login to WordPress Admin**
   - Navigate to `yourstore.com/wp-admin`

2. **Go to WooCommerce Settings**
   - WooCommerce → Settings → Advanced → REST API

3. **Add New API Key**
   - Click "Add key"
   - Description: "Claude MCP Integration"
   - User: Select admin user
   - Permissions: Read/Write
   - Click "Generate API key"

4. **Save Credentials**
   - Copy Consumer Key (starts with `ck_`)
   - Copy Consumer Secret (starts with `cs_`)
   - **Important:** Save these immediately, the secret is only shown once!

---

## Step 7: Test the Setup

### Test 1: Verify Python Environment

```bash
# Activate virtual environment
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Test imports
python -c "
import sys
print(f'Python: {sys.version}')
import fastmcp
print('FastMCP: OK')
import woocommerce
print('WooCommerce: OK')
import httpx
print('HTTPX: OK')
"
```

### Test 2: Verify API Connection

Create `test_connection.py`:

```python
import os
from dotenv import load_dotenv
from woocommerce import API

# Load environment variables
load_dotenv()

# Initialize API
wcapi = API(
    url=os.getenv("STORE_URL"),
    consumer_key=os.getenv("CONSUMER_KEY"),
    consumer_secret=os.getenv("CONSUMER_SECRET"),
    version="wc/v3",
    timeout=30
)

# Test connection
try:
    response = wcapi.get("products?per_page=1")
    if response.status_code == 200:
        print("✅ API connection successful!")
        print(f"Store URL: {os.getenv('STORE_URL')}")
        print(f"Products found: {len(response.json())}")
    else:
        print(f"❌ API error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ Connection failed: {str(e)}")
```

Run the test:
```bash
python test_connection.py
```

### Test 3: Verify MCP Server

```bash
# Run MCP server directly
python claude-desktop-mcp/enhanced/core.py

# Should output:
# Starting WooCommerce Enterprise MCP Server...
# MCP server running on stdio
```

---

## Step 8: Restart Claude Desktop

1. **Close Claude Desktop completely**
   - Windows: Right-click system tray icon → Exit
   - macOS: Cmd+Q or Claude → Quit Claude
   - Linux: Close application

2. **Restart Claude Desktop**

3. **Verify MCP Integration**
   - Open Claude Desktop
   - Type: "Can you list my WooCommerce products?"
   - Claude should now have access to your store

---

## Step 9: Configure Multi-Store (Optional)

For multiple stores, create `stores_config.json`:

```json
{
  "stores": {
    "main": {
      "id": "main",
      "name": "Main Store",
      "url": "https://main.store.com",
      "consumer_key": "ck_main_xxxxx",
      "consumer_secret": "cs_main_xxxxx",
      "language": "en",
      "currency": "USD",
      "timezone": "America/New_York"
    },
    "eu": {
      "id": "eu",
      "name": "EU Store",
      "url": "https://eu.store.com",
      "consumer_key": "ck_eu_xxxxx",
      "consumer_secret": "cs_eu_xxxxx",
      "language": "de",
      "currency": "EUR",
      "timezone": "Europe/Berlin"
    }
  },
  "default_store": "main",
  "sync_settings": {
    "auto_sync": false,
    "sync_interval_hours": 6
  }
}
```

Update Claude Desktop config to include the config file:

```json
{
  "mcpServers": {
    "woocommerce-enterprise": {
      "command": "python",
      "args": ["claude-desktop-mcp/enhanced/core.py"],
      "env": {
        "STORES_CONFIG": "C:\\path\\to\\stores_config.json"
      }
    }
  }
}
```

---

## Step 10: Setup Automated Features (Optional)

### Enable Monitoring

Create `monitoring_config.json`:

```json
{
  "monitoring": {
    "enabled": true,
    "interval_minutes": 15,
    "health_check_interval": 5,
    "alerts": {
      "email": "admin@yourstore.com",
      "thresholds": {
        "api_response_time": 3.0,
        "error_rate": 5.0,
        "low_stock": 10
      }
    }
  },
  "backups": {
    "enabled": true,
    "interval_hours": 24,
    "retention_days": 30,
    "backup_dir": "./backups"
  }
}
```

### Enable Scheduled Tasks

```python
# In Claude Desktop, ask:
"Setup monitoring schedule with 15-minute checks and daily backups"

# Claude will configure:
setup_monitoring_schedule({
    "monitoring_interval_minutes": 15,
    "backup_interval_hours": 24,
    "health_check_interval_minutes": 5
})
```

---

## Troubleshooting

### Issue: "Module not found" error

**Solution:**
```bash
# Ensure virtual environment is activated
.\venv\Scripts\activate  # Windows

# Reinstall packages
pip install --upgrade fastmcp woocommerce httpx python-dotenv
```

### Issue: API authentication failed

**Solution:**
1. Verify credentials are correct (no extra spaces)
2. Check API permissions (should be Read/Write)
3. Ensure HTTPS is used (not HTTP)
4. Test with curl:
```bash
curl https://yourstore.com/wp-json/wc/v3/products \
  -u ck_xxxxx:cs_xxxxx
```

### Issue: Claude Desktop doesn't recognize MCP

**Solution:**
1. Check config file syntax (valid JSON)
2. Verify paths are absolute, not relative
3. Use forward slashes or escaped backslashes in paths
4. Check Claude Desktop logs:
   - Windows: `%APPDATA%\Claude\logs\`
   - macOS: `~/Library/Logs/Claude/`

### Issue: SSL Certificate Error

**Solution:**
```python
# Disable SSL verification (development only!)
wcapi = API(
    url=store_url,
    consumer_key=key,
    consumer_secret=secret,
    verify_ssl=False  # Only for development!
)
```

### Issue: Rate Limiting

**Solution:**
Configure rate limits in `.env`:
```env
RATE_LIMIT=5  # Requests per second
MAX_RETRIES=3
RETRY_DELAY=2
```

---

## Verification Checklist

After setup, verify everything works:

- [ ] Python virtual environment activates correctly
- [ ] All required packages are installed
- [ ] `.env` file contains valid credentials
- [ ] WooCommerce REST API is enabled
- [ ] API test script connects successfully
- [ ] Claude Desktop config file is valid JSON
- [ ] Claude Desktop has been restarted
- [ ] Claude can access WooCommerce tools
- [ ] Basic operations work (list products, orders)
- [ ] Multi-store configuration loads (if applicable)

---

## Next Steps

1. **Test Basic Operations**
   ```
   Ask Claude: "List my WooCommerce products"
   Ask Claude: "Show me recent orders"
   Ask Claude: "Check store health"
   ```

2. **Configure Safety Settings**
   - Enable dry-run mode for testing
   - Setup automated backups
   - Configure monitoring alerts

3. **Explore Advanced Features**
   - Multi-store synchronization
   - Bulk operations
   - Store cloning
   - Multi-language support

4. **Read Documentation**
   - [README.md](README.md) - Overview and features
   - [TOOL_REFERENCE.md](TOOL_REFERENCE.md) - Complete tool documentation
   - [ARCHITECTURE.md](ARCHITECTURE.md) - System design

---

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review Claude Desktop logs
3. Verify WooCommerce API access
4. Test with minimal configuration first
5. Report issues on GitHub

---

*Setup Guide Version: 2.0.0*
*Last Updated: January 26, 2025*