# WooCommerce Enterprise MCP Suite

A comprehensive enterprise-level Model Context Protocol (MCP) integration for WooCommerce, providing 100+ tools for complete store management through Claude Desktop. This suite offers full WooCommerce REST API coverage with advanced multi-store management, automation, and safety features.

## 🚀 Key Features

### Enterprise Capabilities
- ✅ **100+ MCP Tools** - Complete WooCommerce REST API coverage
- ✅ **Multi-Store Management** - Manage unlimited stores from single interface
- ✅ **Store Cloning** - Complete store replication with localization
- ✅ **Bulk Operations** - Safe bulk processing with preview and rollback
- ✅ **Multi-Language Support** - Complete translation management
- ✅ **Multi-Currency** - Regional pricing and currency conversion
- ✅ **Theme Management** - Customization and branding tools
- ✅ **SEO Optimization** - Advanced SEO and marketing tools
- ✅ **Performance Monitoring** - Real-time metrics and alerts
- ✅ **Automated Backups** - Scheduled backups with restore capabilities

### Safety & Security
- 🛡️ **Dry-Run Mode** - Preview all changes before execution
- 🔄 **Automatic Rollback** - Revert on errors
- 💾 **Backup Before Changes** - Automatic safety snapshots
- ⚡ **Rate Limiting** - Prevent API overload
- ✔️ **Validation** - Input validation and error checking

## 🏗️ Architecture

The suite is organized into two complementary systems:

### System 1: Web Platform
- **Location:** `/web-platform/`
- **Purpose:** Browser-based management interface
- **Features:** Multi-store dashboard, visual analytics, REST API

### System 2: Claude Desktop MCP (Enhanced)
- **Location:** `/claude-desktop-mcp/enhanced/`
- **Purpose:** AI-powered store management through Claude
- **Features:** 100+ MCP tools, natural language interface, automation

## 📁 Project Structure

```
MCP/
├── ARCHITECTURE.md              # Detailed architecture documentation
├── README.md                    # This file (comprehensive guide)
├── TOOL_REFERENCE.md            # Complete API reference for all 100+ tools
├── CREDENTIALS.md               # Credential management guide
│
├── web-platform/                # System 1: Web Management Platform
│   ├── README.md               # Web platform documentation
│   ├── main.py                 # FastAPI application entry
│   ├── web_server.py           # Web server implementation
│   └── src/                    # Application source code
│
├── claude-desktop-mcp/          # System 2: Claude Desktop Integration
│   ├── enhanced/               # Enhanced MCP implementation (100+ tools)
│   │   ├── core.py            # Main MCP server with all tools
│   │   ├── multi_store.py     # Multi-store management system
│   │   ├── store_cloner.py    # Store cloning functionality
│   │   ├── bulk_operations.py # Safe bulk processing
│   │   └── tools/             # Enhanced tool modules
│   │       ├── products_enhanced.py  # Product management (15+ tools)
│   │       ├── orders_enhanced.py    # Order management (12+ tools)
│   │       ├── customers.py          # Customer management (10+ tools)
│   │       ├── multi_language.py     # Language & currency (8+ tools)
│   │       ├── store_config.py       # Store configuration (6+ tools)
│   │       ├── theme_manager.py      # Theme & branding (8+ tools)
│   │       ├── content_manager.py    # Content management (10+ tools)
│   │       ├── seo_marketing.py      # SEO & marketing (10+ tools)
│   │       └── monitoring.py         # Monitoring & health (7+ tools)
│   ├── mcp_server.py           # Basic MCP server (legacy)
│   └── config.ridebase.json    # RideBase.fi configuration
│
├── shared/                      # Shared components
│   ├── woocommerce_api/        # WooCommerce API wrapper
│   └── models/                 # Data models
│
└── backups/                     # Store backup directory
```

## 🛠️ Tool Categories (100+ Tools)

### Product Management (15+ tools)
`create_product`, `update_product`, `bulk_update_products`, `manage_variations`, `import_products`, `export_products`, `duplicate_product`, `manage_inventory`, `set_sale_prices`, `manage_categories`, `manage_tags`, `product_reviews`, `cross_sells_upsells`, `product_attributes`, `product_search`

### Order Management (12+ tools)
`get_orders`, `create_order`, `update_order_status`, `bulk_fulfill_orders`, `process_refunds`, `generate_invoices`, `print_shipping_labels`, `track_shipments`, `order_notes`, `recurring_orders`, `abandoned_cart_recovery`, `sales_analytics`

### Customer Management (10+ tools)
`get_customers`, `create_customer`, `update_customer`, `customer_segments`, `loyalty_programs`, `customer_analytics`, `export_customers`, `import_customers`, `merge_customers`, `customer_communications`

### Multi-Store Management (8+ tools)
`add_store`, `sync_stores`, `clone_store`, `compare_stores`, `bulk_store_updates`, `store_migration`, `regional_settings`, `store_permissions`

### Content & SEO (10+ tools)
`manage_pages`, `create_blog_posts`, `optimize_seo`, `generate_sitemaps`, `meta_tags_management`, `schema_markup`, `content_translation`, `image_optimization`, `url_redirects`, `analytics_integration`

### Monitoring & Health (7+ tools)
`monitor_performance`, `health_check`, `create_backup`, `restore_backup`, `error_logs`, `uptime_monitoring`, `alert_management`

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

## 📊 System Comparison

| Feature | Web Platform | Enhanced Claude MCP |
|---------|--------------|--------------------|
| **Interface** | Web browser | Claude Desktop |
| **MCP Tools** | N/A | 100+ tools |
| **Stores** | Multiple | Unlimited |
| **Store Cloning** | Manual | Automated |
| **Setup** | Medium | Simple |
| **Storage** | Database | In-memory + backups |
| **Bulk Operations** | ✅ Yes | ✅ Yes (with safety) |
| **API Access** | ✅ REST API | ✅ Full coverage |
| **Multi-Language** | Basic | ✅ Complete |
| **Multi-Currency** | Basic | ✅ Advanced |
| **Monitoring** | Basic | ✅ Real-time |
| **Backup/Restore** | Manual | ✅ Automated |
| **Best For** | Web UI needs | Enterprise automation |

## 📋 Requirements

- **Python**: 3.11+ (required for pandas/numpy)
- **OS**: Windows 10/11
- **RAM**: 2GB minimum
- **WooCommerce**: REST API enabled

## 🔧 Installation

### Prerequisites
- Python 3.9+ (3.11+ recommended)
- Node.js 16+ (for Claude Desktop)
- WooCommerce store with REST API enabled
- Windows 10/11 or Linux/macOS

### Setup Steps

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/woocommerce-mcp-suite.git
cd MCP
```

2. **Install Python dependencies:**
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install fastmcp woocommerce httpx python-dotenv beautifulsoup4 PyQt6 pandas
```

3. **Configure store credentials:**
```bash
# Copy example configuration
cp .env.example .env

# Edit .env with your WooCommerce credentials
# STORE_URL=https://yourstore.com
# CONSUMER_KEY=ck_xxxxx
# CONSUMER_SECRET=cs_xxxxx
```

4. **Configure Claude Desktop for Enhanced MCP:**
```json
// Add to %APPDATA%\Claude\claude_desktop_config.json
{
  "mcpServers": {
    "woocommerce-enterprise": {
      "command": "C:\\path\\to\\venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\claude-desktop-mcp\\enhanced\\core.py"],
      "env": {
        "STORE_URL": "https://yourstore.com",
        "CONSUMER_KEY": "ck_xxxxx",
        "CONSUMER_SECRET": "cs_xxxxx"
      }
    }
  }
}
```

5. **Restart Claude Desktop** to load the enhanced MCP server

## 📚 Documentation

- **Architecture**: [ARCHITECTURE.md](./ARCHITECTURE.md) - System design details
- **Web Platform**: [web-platform/README.md](./web-platform/README.md)
- **Claude MCP**: [claude-desktop-mcp/README.md](./claude-desktop-mcp/README.md)

## 💡 Usage Examples

### Multi-Store Management
```python
# Clone store to new region with localization
clone_store({
    "source_store_id": "main",
    "target_config": {
        "name": "EU Store",
        "url": "https://eu.store.com",
        "language": "de",
        "currency": "EUR"
    },
    "clone_options": {
        "products": true,
        "transform_prices": true,
        "currency_conversion_rate": 1.1
    }
})

# Sync inventory across all stores
sync_multi_store({
    "sync_type": "inventory",
    "source_store": "main",
    "target_stores": ["eu", "uk", "us"],
    "conflict_resolution": "source_wins"
})
```

### Bulk Operations with Safety
```python
# Preview changes before applying
bulk_update_products({
    "product_ids": [123, 124, 125],
    "updates": {"sale_price": "39.99"},
    "safety_config": {
        "dry_run": true,  # Preview mode
        "backup_before": true,
        "rollback_on_error": true
    }
})
```

### Advanced Analytics
```python
# Comprehensive sales analysis
get_sales_analytics({
    "date_range": "last_30_days",
    "grouping": "day",
    "metrics": ["revenue", "orders", "average_order_value"],
    "compare_period": "previous_period",
    "segment_by": "customer_type"
})
```

### Automated Monitoring
```python
# Setup 24/7 monitoring with alerts
setup_monitoring_schedule({
    "monitoring_interval_minutes": 15,
    "backup_interval_hours": 6,
    "health_check_interval_minutes": 5,
    "alert_thresholds": {
        "api_response_time": 3.0,
        "error_rate": 5.0
    }
})
```

## 🎯 Use Cases

### Enterprise Use Cases
- **Multi-Region Expansion**: Clone and localize stores for new markets
- **Inventory Synchronization**: Real-time sync across all locations
- **Dynamic Pricing**: Automated regional pricing with currency conversion
- **Bulk Migration**: Import/export entire product catalogs
- **SEO Optimization**: Multilingual SEO with schema markup
- **Performance Monitoring**: 24/7 health checks with alerts
- **Disaster Recovery**: Automated backups with quick restore
- **Customer Analytics**: Segment analysis and lifetime value tracking
- **Order Automation**: Bulk fulfillment and invoice generation
- **Content Management**: Multi-language content with translations

## 🔒 Security Best Practices

1. **Never commit credentials** - Use environment variables
2. **Rotate API keys regularly** - Update keys monthly
3. **Use read-only keys when possible** - Limit permissions
4. **Enable API request logging** - Maintain audit trail
5. **Implement IP whitelisting** - Restrict access
6. **Use HTTPS only** - Encrypted connections
7. **Regular security audits** - Check for vulnerabilities

## ⚡ Performance Optimization

1. **Use Bulk Operations** - Process multiple items in single request
2. **Enable Caching** - Cache frequently accessed data
3. **Optimize Queries** - Use specific fields parameter
4. **Implement Pagination** - Process large datasets in chunks
5. **Schedule Heavy Tasks** - Run intensive operations during off-peak
6. **Monitor API Limits** - Stay within rate limits
7. **Use Async Operations** - Non-blocking for better performance

## 🔄 Migration from Legacy

If you're using the combined `mcp-woocommerce-suite/` version:

1. **Backup your data**: `data/` folder contains stores config
2. **Choose your system**: Web Platform or Claude MCP
3. **Follow setup**: In the chosen system's README
4. **Migrate config**: Copy store credentials to new system

## 🧪 Testing

### Run Tests
```bash
# Unit tests
python -m pytest tests/unit

# Integration tests
python -m pytest tests/integration

# Test specific tool
python -m pytest tests/tools/test_products.py
```

### Test Coverage
```bash
python -m pytest --cov=claude-desktop-mcp/enhanced --cov-report=html
```

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

## 📈 Monitoring Dashboard

Access real-time metrics and health status:
```python
get_monitoring_dashboard()
# Returns:
# - Current performance metrics
# - Health check results
# - Recent alerts
# - Backup status
# - System statistics
```

## 🌍 Multi-Language & Currency

Supported languages: EN, DE, FR, ES, IT, NL, PT, SV, FI, NO, DA
Supported currencies: USD, EUR, GBP, SEK, NOK, DKK, CHF, AUD, CAD

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Support

- **Documentation:** See TOOL_REFERENCE.md for complete API reference
- **Architecture:** Review ARCHITECTURE.md for system design
- **Issues:** Report bugs via GitHub Issues
- **Logs:** Check `data/logs/` for troubleshooting
- **Requirements:** Python 3.9+, WooCommerce REST API enabled

## 🏆 Version History

### Version 2.0.0 (2025-01-26) - Enterprise Edition
- ✨ Complete architectural refactoring into dual-system design
- 🚀 Added 100+ MCP tools for full WooCommerce API coverage
- 🌍 Implemented multi-store management with synchronization
- 🔄 Added store cloning with localization support
- 💱 Integrated multi-language and currency management
- 📊 Built comprehensive monitoring and backup systems
- 🛡️ Added enterprise-level safety features (dry-run, rollback)
- ⚡ Performance optimizations for large-scale operations

### Version 1.0.0 (2025-01-20) - Initial Release
- Basic WooCommerce integration
- Web platform for store management
- Simple MCP tools for Claude Desktop

---

**🚀 Get Started:**
- 💼 [Enhanced Claude MCP](./claude-desktop-mcp/enhanced/) - Enterprise automation with 100+ tools
- 🌐 [Web Platform](./web-platform/) - Browser-based management interface
- 📖 [Tool Reference](./TOOL_REFERENCE.md) - Complete API documentation