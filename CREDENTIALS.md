# Store Credentials Configuration

## RideBase.fi Store

The RideBase.fi WooCommerce store credentials are configured in multiple places for different use cases:

### 1. Claude Desktop MCP Integration

**Option A: Use the ready config file**
```bash
# Copy the provided config to Claude Desktop
copy claude-desktop-mcp\config.ridebase.json %APPDATA%\Claude\claude_desktop_config.json
```

**Option B: Manual configuration**
Add to `%APPDATA%\Claude\claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "ridebase-woocommerce": {
      "command": "C:\\Users\\maxli\\PycharmProjects\\PythonProject\\MCP\\venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\maxli\\PycharmProjects\\PythonProject\\MCP\\claude-desktop-mcp\\mcp_server.py"],
      "env": {
        "STORE_URL": "https://ridebase.fi/",
        "WOOCOMMERCE_KEY": "ck_f6ad7b402ad502bcccd39616c94717f282954278",
        "WOOCOMMERCE_SECRET": "cs_9732d3b1cfe2db9fffd47316e99884efecac4b9c"
      }
    }
  }
}
```

**Testing:**
```bash
cd claude-desktop-mcp
test_ridebase.bat
```

### 2. Web Platform

Credentials are stored in `web-platform/.env`:
```env
STORE_URL=https://ridebase.fi/
WOOCOMMERCE_KEY=ck_f6ad7b402ad502bcccd39616c94717f282954278
WOOCOMMERCE_SECRET=cs_9732d3b1cfe2db9fffd47316e99884efecac4b9c
```

**Add store to database:**
```bash
cd web-platform
python add_ridebase_store.py
```

**Start web platform:**
```bash
cd web-platform
start_webapp.bat
```

### 3. Environment Variables (For Testing)

Set environment variables in Windows:
```batch
set STORE_URL=https://ridebase.fi/
set WOOCOMMERCE_KEY=ck_f6ad7b402ad502bcccd39616c94717f282954278
set WOOCOMMERCE_SECRET=cs_9732d3b1cfe2db9fffd47316e99884efecac4b9c
```

Or use PowerShell:
```powershell
$env:STORE_URL = "https://ridebase.fi/"
$env:WOOCOMMERCE_KEY = "ck_f6ad7b402ad502bcccd39616c94717f282954278"
$env:WOOCOMMERCE_SECRET = "cs_9732d3b1cfe2db9fffd47316e99884efecac4b9c"
```

## Security Notes

⚠️ **Important Security Considerations:**

1. **Never commit credentials** - The `.env` files are gitignored
2. **Use environment variables** - For production deployments
3. **Rotate keys regularly** - Generate new API keys periodically
4. **Limit permissions** - Use read-only keys where possible
5. **Secure storage** - In production, use secure credential stores

## Credential Files Overview

| File | Purpose | Location |
|------|---------|----------|
| `.env` | Root environment file | `/MCP/.env` |
| `web-platform/.env` | Web platform config | `/MCP/web-platform/.env` |
| `config.ridebase.json` | Claude Desktop config | `/MCP/claude-desktop-mcp/` |
| `claude_desktop_config.json` | Claude Desktop settings | `%APPDATA%\Claude\` |

## Quick Test Commands

### Test Claude Desktop MCP:
```bash
cd claude-desktop-mcp
test_ridebase.bat
```

### Test Web Platform:
```bash
cd web-platform
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(f'Store: {os.getenv(\"STORE_URL\")}')"
```

## Troubleshooting

If credentials don't work:
1. Check trailing slash on STORE_URL (should be `https://ridebase.fi/`)
2. Verify no extra spaces in keys
3. Ensure WooCommerce REST API is enabled in store
4. Check API key permissions (Read/Write needed)