# Working Enterprise MCP Configuration

**Status**: ✅ WORKING - 100+ Enterprise Tools Confirmed  
**Date**: August 26, 2025  
**Commit**: `ccb109e` - feat: Implement Enterprise WooCommerce MCP Suite v2.0.0

## Git Branches

- `enterprise-7am-working` - **MAIN WORKING VERSION** (current state)
- `backup-2am-working` - Basic 11-tool fallback version  
- `main` - Current active branch (same as enterprise-7am-working)

## Claude Desktop Configuration

**Config File**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ridebase-woocommerce": {
      "command": "C:\\Users\\maxli\\PycharmProjects\\PythonProject\\MCP\\venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\maxli\\PycharmProjects\\PythonProject\\MCP\\claude-desktop-mcp\\enhanced\\core.py"],
      "env": {
        "STORE_URL": "https://ridebase.fi/",
        "WOOCOMMERCE_KEY": "ck_f6ad7b402ad502bcccd39616c94717f282954278",
        "WOOCOMMERCE_SECRET": "cs_9732d3b1cfe2db9fffd47316e99884efecac4b9c"
      }
    }
  }
}
```

## Key File Structure

```
claude-desktop-mcp/enhanced/
├── core.py                    # Main MCP server (100+ tools)
├── multi_store.py            # Multi-store management
├── store_cloner.py           # Store cloning functionality  
├── bulk_operations.py        # Safe bulk operations
└── tools/                    # Enhanced tool modules
    ├── products_enhanced.py  # 15+ product tools
    ├── orders_enhanced.py    # 12+ order tools
    ├── customers.py          # 10+ customer tools
    ├── store_config.py       # 6+ config tools
    ├── multi_language.py     # 8+ language tools
    ├── theme_manager.py      # 8+ theme tools
    ├── content_manager.py    # 10+ content tools
    ├── seo_marketing.py      # 10+ SEO tools
    └── monitoring.py         # 7+ monitoring tools
```

## Confirmed Working Tools

### Core Management (20+ tools)
- Product Management: `get_product_variations`, `manage_product_attributes`, `bulk_product_operations`, `import_products_from_file`, `export_products_to_file`
- Order Management: `get_order_details`, `update_order_status`, `manage_order_items`, `process_refund`, `get_sales_analytics`
- Customer Management: `get_customers`, `get_customer_details`, `manage_customer_data`, `get_customer_analytics`
- Store Settings: `get_store_settings`, `update_store_settings`, `manage_shipping_zones`, `manage_payment_gateways`, `manage_tax_settings`

### Enterprise Features (30+ tools)
- Multi-Store: `add_store`, `list_stores`, `switch_active_store`, `sync_stores`
- Store Cloning: `clone_store`, `export_store_data`
- Bulk Operations: `preview_bulk_changes`, `execute_bulk_operation`, `rollback_bulk_operation`
- Internationalization: `get_supported_languages`, `manage_translations`, `manage_multi_currency`
- Theme & Branding: `get_active_theme`, `manage_store_branding`
- Content & SEO: `manage_static_pages`, `manage_seo_settings`
- Monitoring: `monitor_store_health`, `manage_store_backups`

### VPS Management & Deployment (8+ tools) ✨ NEW
- VPS Provisioning: `provision_ubuntu_vps`
- Store Deployment: `deploy_store_to_vps`
- VPS Monitoring: `get_vps_resources`, `monitor_store_on_vps`
- Store Management: `list_stores_on_vps`, `backup_vps_store`
- System Operations: `execute_vps_command`, `optimize_vps_performance`

### Advanced Operations (50+ tools)
- All remaining enhanced tools confirmed working during test

## Store Connection Details

- **Store**: RideBase.fi
- **Location**: Helsinki, Finland (EUR currency)
- **Platform**: WordPress 6.8.2 + WooCommerce 9.4.2
- **Products**: 26 items (snowmobiles, ATVs, Sea-Doos)
- **Status**: Connected and functional

## Import Fixes Applied

Fixed relative import issues in `core.py`:
- Added try/except block for relative vs absolute imports
- Allows running directly via Claude Desktop config

## Emergency Rollback Procedures

### If Claude Desktop stops working:
1. Check if `enterprise-7am-working` branch exists: `git branch`
2. Switch to working branch: `git checkout enterprise-7am-working`
3. Restart Claude Desktop

### If tools are missing:
1. Verify config points to: `enhanced/core.py`
2. Check server status in Claude Desktop interface
3. Test with simple tool like `get_store_settings`

### Complete reset:
```bash
git checkout enterprise-7am-working
git reset --hard ccb109e
# Update Claude Desktop config to point to enhanced/core.py
# Restart Claude Desktop
```

## Next Steps

1. ✅ Safety branch created: `enterprise-7am-working`
2. ✅ Configuration documented
3. ✅ Research VPS tools from post-7am commits
4. ✅ Add VPS functionality incrementally (8 tools added)
5. ✅ Test each addition thoroughly

## Recent Changes (Aug 26, 2025)

- ✅ Added 8 VPS management tools to enterprise suite
- ✅ Server tested successfully with VPS integration
- ✅ All tools follow same pattern as existing enterprise tools
- ✅ Environment variable support for SSH credentials
- ✅ Security checks for dangerous commands

---

**⚠️ NEVER modify `enterprise-7am-working` branch directly**  
**⚠️ Always test changes on feature branches first**  
**⚠️ Keep this config as ultimate fallback**