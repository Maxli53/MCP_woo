# WooCommerce Management Suite

Two independent systems for managing WooCommerce stores, each optimized for different use cases.

## 🎯 Which System Should You Use?

### Use the Web Platform if you need:
- Multiple store management
- Web-based interface
- Bulk operations (import/export)
- Persistent data storage
- REST API for automation
- Team collaboration

**→ [Go to Web Platform](./web-platform/)**

### Use Claude Desktop MCP if you need:
- Quick single-store operations
- Natural language interface through Claude
- Minimal setup
- Lightweight solution
- No web server required

**→ [Go to Claude Desktop MCP](./claude-desktop-mcp/)**

## 📁 Project Structure

```
MCP/
├── ARCHITECTURE.md           # Detailed architecture documentation
├── README.md                # This file
│
├── web-platform/            # System 1: Web Management Platform
│   ├── README.md           # Web platform documentation
│   ├── main.py            # Application entry
│   ├── web_server.py      # FastAPI server
│   └── src/               # Application code
│
├── claude-desktop-mcp/     # System 2: Claude Desktop Integration
│   ├── README.md          # MCP documentation
│   ├── mcp_server.py      # FastMCP server
│   └── tools/             # MCP tools
│
├── shared/                 # Shared components
│   ├── woocommerce_api/   # API wrapper
│   └── models/            # Data models
│
└── mcp-woocommerce-suite/ # Legacy combined version (deprecated)
```

## 🚀 Quick Start

### Option 1: Web Platform
```batch
cd web-platform
setup_webapp.bat
start_webapp.bat
```
→ Opens browser at http://localhost:8000

### Option 2: Claude Desktop MCP
```batch
cd claude-desktop-mcp
# Configure environment variables in Claude Desktop
# Restart Claude Desktop
```
→ Use Claude Desktop to manage your store

## 📊 Comparison

| Feature | Web Platform | Claude Desktop MCP |
|---------|--------------|-------------------|
| **Interface** | Web browser | Claude Desktop |
| **Stores** | Multiple | Single |
| **Setup** | Medium | Simple |
| **Storage** | Database | None |
| **Bulk Operations** | ✅ Yes | ❌ No |
| **API Access** | ✅ REST API | ❌ No |
| **Dependencies** | Heavy | Light |
| **Best For** | Full management | Quick operations |

## 📋 Requirements

- **Python**: 3.11+ (required for pandas/numpy)
- **OS**: Windows 10/11
- **RAM**: 2GB minimum
- **WooCommerce**: REST API enabled

## 🔧 Installation

### Full Setup (Both Systems)
```batch
# Clone repository
git clone [repository-url]
cd MCP

# Setup both systems
setup.bat
```

### Individual Setup
See README in each system's folder:
- [Web Platform Setup](./web-platform/README.md)
- [Claude Desktop MCP Setup](./claude-desktop-mcp/README.md)

## 📚 Documentation

- **Architecture**: [ARCHITECTURE.md](./ARCHITECTURE.md) - System design details
- **Web Platform**: [web-platform/README.md](./web-platform/README.md)
- **Claude MCP**: [claude-desktop-mcp/README.md](./claude-desktop-mcp/README.md)

## 🎯 Use Cases

### Web Platform Use Cases
- Managing inventory across multiple stores
- Bulk price updates from Excel
- Regular CSV exports for accounting
- Team-based store management
- API integration with other systems

### Claude Desktop MCP Use Cases
- Quick price checks
- Simple product updates
- Order status queries
- Store statistics overview
- Natural language store management

## 🔄 Migration from Legacy

If you're using the combined `mcp-woocommerce-suite/` version:

1. **Backup your data**: `data/` folder contains stores config
2. **Choose your system**: Web Platform or Claude MCP
3. **Follow setup**: In the chosen system's README
4. **Migrate config**: Copy store credentials to new system

## 🛠️ Development

Each system can be developed independently:

### Web Platform Development
```batch
cd web-platform
python main.py --debug
```

### Claude MCP Development
```batch
cd claude-desktop-mcp
python mcp_server.py
```

## 📝 License

MIT License - See LICENSE file

## 🤝 Support

- Check system-specific README files
- Review logs in `data/logs/` (Web Platform)
- Verify WooCommerce REST API is enabled
- Ensure correct Python version (3.11+)

---

**Choose your path:**
- 🌐 [Web Platform](./web-platform/) - Full management suite
- 🤖 [Claude Desktop MCP](./claude-desktop-mcp/) - Quick Claude integration