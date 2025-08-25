# Project Architecture - WooCommerce Management Suite

This project contains **TWO INDEPENDENT SYSTEMS** that can be used separately or together:

## System 1: Web-Based Management Platform
Full-featured web application for managing multiple WooCommerce stores

**Location:** `/web-platform/`

**Features:**
- Multi-store management with persistent storage
- Web interface (FastAPI + modern UI)
- REST API endpoints
- Data import/export (CSV/Excel)
- Bulk operations
- User sessions and authentication
- Database persistence

**Components:**
```
web-platform/
├── main.py                    # Main application entry
├── web_server.py              # FastAPI server
├── src/
│   ├── config/               # App configuration
│   ├── gui/                  # Desktop GUI (PyQt6)
│   ├── store_management/     # Store management logic
│   ├── data_processing/      # Bulk operations, import/export
│   ├── utils/                # Shared utilities
│   └── web/                  # Web interfaces
│       ├── dashboard/        # Monitoring dashboard
│       └── inspector/        # MCP inspector
├── data/                     # Persistent data
│   ├── stores/              # Store configurations
│   ├── logs/                # Application logs
│   └── backups/             # Data backups
└── start_webapp.bat         # Start web platform

```

## System 2: Claude Desktop MCP Integration
Lightweight MCP server for Claude Desktop integration

**Location:** `/claude-desktop-mcp/`

**Features:**
- Single-store connection via environment variables
- Direct stdio communication with Claude Desktop
- Stateless tool execution
- No GUI or web interface
- Minimal dependencies

**Components:**
```
claude-desktop-mcp/
├── mcp_server.py             # FastMCP stdio server
├── tools/                    # MCP tool implementations
│   ├── products.py          # Product management tools
│   ├── orders.py            # Order management tools
│   └── store.py             # Store info tools
├── config.example.json      # Claude Desktop config example
├── README.md                # Setup instructions
└── start_mcp.bat           # Start MCP server

```

## Shared Components
Code used by both systems

**Location:** `/shared/`

```
shared/
├── woocommerce_api/         # WooCommerce API wrapper
│   └── client.py           # API client implementation
├── models/                  # Data models
│   ├── product.py
│   ├── order.py
│   └── store.py
└── requirements/
    ├── base.txt            # Shared dependencies
    ├── web.txt             # Web platform deps
    └── mcp.txt             # MCP deps
```

## Root Structure
```
MCP/
├── ARCHITECTURE.md          # This file
├── README.md               # Project overview
├── setup.bat               # Setup both systems
├── web-platform/           # System 1: Web Management
├── claude-desktop-mcp/     # System 2: Claude MCP
├── shared/                 # Shared components
└── venv/                   # Python virtual environment
```

## Usage Scenarios

### Use Web Platform Only
- Managing multiple stores
- Need web interface
- Require persistent data
- Bulk operations
```batch
cd web-platform
start_webapp.bat
```

### Use Claude Desktop MCP Only
- Single store management
- Through Claude Desktop
- Quick operations
```batch
cd claude-desktop-mcp
# Configure environment variables
start_mcp.bat
```

### Use Both Systems
- Web platform for management
- Claude Desktop for quick queries
```batch
setup.bat  # Initial setup
# Then run each system as needed
```

## Key Differences

| Feature | Web Platform | Claude Desktop MCP |
|---------|-------------|-------------------|
| Interface | Web browser + GUI | Claude Desktop |
| Stores | Multiple | Single |
| Data | Persistent | Stateless |
| Config | Database | Environment vars |
| Dependencies | Heavy (pandas, FastAPI) | Light (FastMCP) |
| Use Case | Full management | Quick operations |

## Migration Path

To migrate from current mixed structure:

1. **Phase 1**: Create new directory structure
2. **Phase 2**: Move files to appropriate locations
3. **Phase 3**: Update imports and paths
4. **Phase 4**: Create system-specific configs
5. **Phase 5**: Test each system independently

## Benefits of Separation

1. **Clarity**: Clear which code belongs to which system
2. **Maintenance**: Update systems independently
3. **Dependencies**: Minimize deps for Claude Desktop
4. **Deployment**: Deploy only what's needed
5. **Documentation**: System-specific docs