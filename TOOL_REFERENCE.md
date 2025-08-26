# WooCommerce Enterprise MCP Suite - Tool Reference

## Complete API Reference for 100+ MCP Tools

This document provides a comprehensive reference for all available MCP tools in the WooCommerce Enterprise Suite. Each tool includes its purpose, parameters, return values, and usage examples.

---

## Table of Contents

1. [Product Management Tools](#product-management-tools)
2. [Order Management Tools](#order-management-tools)
3. [Customer Management Tools](#customer-management-tools)
4. [Multi-Store Management Tools](#multi-store-management-tools)
5. [Content & SEO Tools](#content--seo-tools)
6. [Theme & Branding Tools](#theme--branding-tools)
7. [Monitoring & Health Tools](#monitoring--health-tools)
8. [Multi-Language & Currency Tools](#multi-language--currency-tools)
9. [Store Configuration Tools](#store-configuration-tools)
10. [Bulk Operations Tools](#bulk-operations-tools)

---

## Product Management Tools

### 1. create_product
**Purpose:** Create a new product in WooCommerce
**Parameters:**
- `product_data` (dict): Product information including name, type, price, description
- `store_id` (str, optional): Target store ID for multi-store setup

**Returns:** Created product object with ID
**Example:**
```python
create_product({
    "name": "Premium Widget",
    "type": "simple",
    "regular_price": "49.99",
    "description": "High-quality widget",
    "sku": "WIDGET-001",
    "stock_quantity": 100,
    "categories": [{"id": 15}],
    "images": [{"src": "https://example.com/image.jpg"}]
})
```

### 2. update_product
**Purpose:** Update an existing product
**Parameters:**
- `product_id` (int): Product ID to update
- `updates` (dict): Fields to update

**Returns:** Updated product object
**Example:**
```python
update_product(123, {
    "sale_price": "39.99",
    "stock_quantity": 50,
    "description": "Updated description"
})
```

### 3. bulk_update_products
**Purpose:** Update multiple products simultaneously with safety features
**Parameters:**
- `product_ids` (list): List of product IDs
- `updates` (dict): Updates to apply
- `safety_config` (dict): Safety options (dry_run, backup, rollback)

**Returns:** Batch operation results with preview/confirmation
**Example:**
```python
bulk_update_products({
    "product_ids": [123, 124, 125],
    "updates": {"sale_price": "29.99"},
    "safety_config": {
        "dry_run": True,
        "backup_before": True,
        "rollback_on_error": True
    }
})
```

### 4. manage_product_variations
**Purpose:** Manage variations for variable products
**Parameters:**
- `product_id` (int): Parent product ID
- `variations` (list): Variation configurations

**Returns:** Created/updated variations
**Example:**
```python
manage_product_variations(123, [
    {
        "attributes": [{"id": 1, "option": "Red"}],
        "regular_price": "49.99",
        "stock_quantity": 20
    },
    {
        "attributes": [{"id": 1, "option": "Blue"}],
        "regular_price": "49.99",
        "stock_quantity": 30
    }
])
```

### 5. import_products
**Purpose:** Bulk import products from CSV/JSON
**Parameters:**
- `import_data` (dict): Import configuration
- `format` (str): Data format (csv, json)
- `mapping` (dict): Field mapping rules

**Returns:** Import results with success/error counts
**Example:**
```python
import_products({
    "file_path": "./products.csv",
    "format": "csv",
    "mapping": {
        "Product Name": "name",
        "Price": "regular_price",
        "SKU": "sku"
    },
    "options": {
        "update_existing": True,
        "skip_errors": True
    }
})
```

### 6. export_products
**Purpose:** Export products to various formats
**Parameters:**
- `export_config` (dict): Export settings
- `filters` (dict): Product filters
- `format` (str): Output format

**Returns:** Export file path or data
**Example:**
```python
export_products({
    "format": "csv",
    "filters": {"category": "electronics"},
    "fields": ["name", "sku", "price", "stock"],
    "include_variations": True
})
```

### 7. duplicate_product
**Purpose:** Clone an existing product
**Parameters:**
- `product_id` (int): Source product ID
- `modifications` (dict): Changes to apply to duplicate

**Returns:** New product object
**Example:**
```python
duplicate_product(123, {
    "name_suffix": " - Copy",
    "sku_prefix": "COPY-",
    "status": "draft"
})
```

### 8. manage_inventory
**Purpose:** Advanced inventory management
**Parameters:**
- `operation` (str): Operation type (adjust, set, transfer)
- `items` (list): Products and quantities

**Returns:** Inventory update results
**Example:**
```python
manage_inventory({
    "operation": "adjust",
    "items": [
        {"product_id": 123, "adjustment": -5},
        {"product_id": 124, "adjustment": 10}
    ],
    "reason": "Manual stock count"
})
```

### 9. set_sale_prices
**Purpose:** Bulk manage sale prices and schedules
**Parameters:**
- `price_rules` (dict): Pricing configuration
- `schedule` (dict): Sale schedule

**Returns:** Updated products with new prices
**Example:**
```python
set_sale_prices({
    "products": [123, 124, 125],
    "discount_type": "percentage",
    "discount_value": 20,
    "schedule": {
        "start_date": "2025-02-01",
        "end_date": "2025-02-14"
    }
})
```

### 10. manage_categories
**Purpose:** Create, update, delete product categories
**Parameters:**
- `operation` (str): Operation type
- `category_data` (dict): Category information

**Returns:** Category operation result
**Example:**
```python
manage_categories({
    "operation": "create",
    "data": {
        "name": "New Category",
        "parent": 15,
        "description": "Category description",
        "image": {"src": "https://example.com/cat.jpg"}
    }
})
```

---

## Order Management Tools

### 1. get_orders
**Purpose:** Retrieve orders with advanced filtering
**Parameters:**
- `filters` (dict): Filter criteria
- `pagination` (dict): Page settings

**Returns:** List of orders matching criteria
**Example:**
```python
get_orders({
    "status": ["processing", "on-hold"],
    "date_after": "2025-01-01",
    "customer_id": 456,
    "per_page": 50,
    "orderby": "date",
    "order": "desc"
})
```

### 2. create_order
**Purpose:** Manually create an order
**Parameters:**
- `order_data` (dict): Complete order information

**Returns:** Created order object
**Example:**
```python
create_order({
    "status": "processing",
    "customer_id": 456,
    "billing": {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com"
    },
    "line_items": [
        {"product_id": 123, "quantity": 2}
    ],
    "payment_method": "stripe"
})
```

### 3. update_order_status
**Purpose:** Change order status with notifications
**Parameters:**
- `order_id` (int): Order ID
- `new_status` (str): Target status
- `notify_customer` (bool): Send email notification

**Returns:** Updated order
**Example:**
```python
update_order_status(789, {
    "status": "completed",
    "notify_customer": True,
    "note": "Order shipped via FedEx"
})
```

### 4. bulk_fulfill_orders
**Purpose:** Mass fulfillment processing
**Parameters:**
- `order_ids` (list): Orders to fulfill
- `fulfillment_data` (dict): Shipping information

**Returns:** Fulfillment results
**Example:**
```python
bulk_fulfill_orders({
    "order_ids": [789, 790, 791],
    "carrier": "ups",
    "tracking_prefix": "1Z999AA1",
    "send_notification": True,
    "mark_completed": True
})
```

### 5. process_refunds
**Purpose:** Handle refunds and returns
**Parameters:**
- `order_id` (int): Order ID
- `refund_data` (dict): Refund details

**Returns:** Refund confirmation
**Example:**
```python
process_refunds(789, {
    "amount": "25.00",
    "reason": "Customer request",
    "refund_payment": True,
    "restock_items": True,
    "line_items": [
        {"id": 10, "quantity": 1, "refund_total": 25.00}
    ]
})
```

### 6. generate_invoices
**Purpose:** Create and send invoices
**Parameters:**
- `order_ids` (list): Orders requiring invoices
- `template` (str): Invoice template

**Returns:** Generated invoice URLs
**Example:**
```python
generate_invoices({
    "order_ids": [789, 790],
    "template": "default",
    "send_email": True,
    "include_packing_slip": True
})
```

### 7. print_shipping_labels
**Purpose:** Generate shipping labels
**Parameters:**
- `order_id` (int): Order ID
- `carrier_config` (dict): Carrier settings

**Returns:** Label PDF URL
**Example:**
```python
print_shipping_labels(789, {
    "carrier": "ups",
    "service": "ground",
    "package_type": "box",
    "weight": 2.5,
    "dimensions": {"length": 12, "width": 8, "height": 6}
})
```

### 8. track_shipments
**Purpose:** Track order shipments
**Parameters:**
- `tracking_numbers` (list): Tracking numbers

**Returns:** Tracking status information
**Example:**
```python
track_shipments({
    "tracking_numbers": ["1Z999AA1234567890"],
    "carrier": "ups",
    "include_history": True
})
```

### 9. manage_order_notes
**Purpose:** Add/manage order notes
**Parameters:**
- `order_id` (int): Order ID
- `note_data` (dict): Note information

**Returns:** Created note
**Example:**
```python
manage_order_notes(789, {
    "note": "Customer contacted about delay",
    "customer_note": False,
    "added_by": "admin"
})
```

### 10. sales_analytics
**Purpose:** Generate sales reports and analytics
**Parameters:**
- `date_range` (str): Analysis period
- `metrics` (list): Metrics to calculate

**Returns:** Analytics data
**Example:**
```python
sales_analytics({
    "date_range": "last_30_days",
    "metrics": ["revenue", "orders", "average_order_value"],
    "group_by": "day",
    "compare_period": "previous_month",
    "include_forecast": True
})
```

---

## Customer Management Tools

### 1. get_customers
**Purpose:** Retrieve customer data with filtering
**Parameters:**
- `filters` (dict): Filter criteria

**Returns:** Customer list
**Example:**
```python
get_customers({
    "role": "customer",
    "orderby": "total_spent",
    "order": "desc",
    "meta_query": {"vip_status": "gold"}
})
```

### 2. create_customer
**Purpose:** Register new customer
**Parameters:**
- `customer_data` (dict): Customer information

**Returns:** Created customer object
**Example:**
```python
create_customer({
    "email": "new@customer.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "username": "janesmith",
    "billing": {
        "address_1": "123 Main St",
        "city": "Seattle",
        "state": "WA",
        "postcode": "98101",
        "country": "US"
    }
})
```

### 3. update_customer
**Purpose:** Update customer information
**Parameters:**
- `customer_id` (int): Customer ID
- `updates` (dict): Fields to update

**Returns:** Updated customer
**Example:**
```python
update_customer(456, {
    "meta_data": [
        {"key": "loyalty_points", "value": "500"},
        {"key": "customer_segment", "value": "vip"}
    ]
})
```

### 4. customer_segments
**Purpose:** Manage customer segmentation
**Parameters:**
- `segment_rules` (dict): Segmentation criteria

**Returns:** Segment analysis
**Example:**
```python
customer_segments({
    "create_segment": {
        "name": "High Value",
        "rules": {
            "total_spent": {"operator": ">", "value": 1000},
            "order_count": {"operator": ">", "value": 5}
        }
    }
})
```

### 5. customer_analytics
**Purpose:** Analyze customer behavior and value
**Parameters:**
- `analysis_type` (str): Type of analysis

**Returns:** Analytics results
**Example:**
```python
customer_analytics({
    "type": "lifetime_value",
    "segment": "all",
    "include_predictions": True,
    "metrics": ["clv", "churn_risk", "purchase_frequency"]
})
```

---

## Multi-Store Management Tools

### 1. add_store
**Purpose:** Register a new store in multi-store system
**Parameters:**
- `store_config` (dict): Store configuration

**Returns:** Store registration confirmation
**Example:**
```python
add_store({
    "id": "eu_store",
    "name": "European Store",
    "url": "https://eu.store.com",
    "consumer_key": "ck_eu_xxx",
    "consumer_secret": "cs_eu_xxx",
    "language": "en",
    "currency": "EUR",
    "timezone": "Europe/Berlin"
})
```

### 2. sync_stores
**Purpose:** Synchronize data between stores
**Parameters:**
- `sync_config` (dict): Synchronization settings

**Returns:** Sync operation results
**Example:**
```python
sync_stores({
    "sync_type": "products",
    "source_store": "main",
    "target_stores": ["eu_store", "uk_store"],
    "options": {
        "sync_inventory": True,
        "sync_prices": True,
        "currency_conversion": True,
        "conflict_resolution": "source_wins"
    }
})
```

### 3. clone_store
**Purpose:** Create complete store replica
**Parameters:**
- `clone_config` (dict): Cloning configuration

**Returns:** Clone operation status
**Example:**
```python
clone_store({
    "source_store_id": "main",
    "target_config": {
        "name": "Asia Pacific Store",
        "url": "https://apac.store.com",
        "language": "en",
        "currency": "USD",
        "timezone": "Asia/Singapore"
    },
    "clone_options": {
        "products": True,
        "categories": True,
        "customers": False,
        "orders": False,
        "transform_prices": True,
        "localize_content": True
    }
})
```

### 4. compare_stores
**Purpose:** Compare performance across stores
**Parameters:**
- `store_ids` (list): Stores to compare
- `metrics` (list): Metrics to analyze

**Returns:** Comparative analysis
**Example:**
```python
compare_stores({
    "stores": ["main", "eu_store", "uk_store"],
    "metrics": ["revenue", "orders", "conversion_rate"],
    "period": "last_30_days",
    "currency": "USD"
})
```

---

## Content & SEO Tools

### 1. manage_pages
**Purpose:** Create and manage store pages
**Parameters:**
- `page_data` (dict): Page content and settings

**Returns:** Page operation result
**Example:**
```python
manage_pages({
    "operation": "create",
    "data": {
        "title": "About Us",
        "content": "Page content here",
        "status": "publish",
        "template": "full-width"
    }
})
```

### 2. optimize_seo
**Purpose:** SEO optimization for products/pages
**Parameters:**
- `target` (dict): Target items
- `seo_config` (dict): SEO settings

**Returns:** Optimization results
**Example:**
```python
optimize_seo({
    "target_type": "products",
    "target_ids": [123, 124],
    "optimizations": {
        "meta_title": {"template": "{name} | Best Price"},
        "meta_description": {"auto_generate": True},
        "schema_markup": True,
        "image_alt_text": True
    }
})
```

### 3. generate_sitemaps
**Purpose:** Create XML sitemaps
**Parameters:**
- `sitemap_config` (dict): Sitemap settings

**Returns:** Sitemap URLs
**Example:**
```python
generate_sitemaps({
    "include": ["products", "categories", "pages"],
    "exclude_ids": [456],
    "priority_rules": {
        "products": 0.8,
        "categories": 0.6,
        "pages": 0.5
    },
    "submit_to_search_engines": True
})
```

### 4. content_translation
**Purpose:** Manage multilingual content
**Parameters:**
- `translation_config` (dict): Translation settings

**Returns:** Translation results
**Example:**
```python
content_translation({
    "source_language": "en",
    "target_languages": ["de", "fr", "es"],
    "content_type": "products",
    "content_ids": [123, 124],
    "auto_translate": True,
    "review_required": True
})
```

---

## Theme & Branding Tools

### 1. customize_theme
**Purpose:** Modify theme settings and appearance
**Parameters:**
- `customizations` (dict): Theme modifications

**Returns:** Applied customizations
**Example:**
```python
customize_theme({
    "colors": {
        "primary": "#007cba",
        "secondary": "#f0f0f0",
        "text": "#333333"
    },
    "typography": {
        "font_family": "Open Sans",
        "base_size": "16px"
    },
    "layout": {
        "container_width": "1200px",
        "sidebar": "right"
    }
})
```

### 2. manage_menus
**Purpose:** Create and manage navigation menus
**Parameters:**
- `menu_data` (dict): Menu structure

**Returns:** Menu update confirmation
**Example:**
```python
manage_menus({
    "menu_name": "main_navigation",
    "items": [
        {"title": "Shop", "url": "/shop", "position": 1},
        {"title": "About", "url": "/about", "position": 2},
        {"title": "Contact", "url": "/contact", "position": 3}
    ]
})
```

---

## Monitoring & Health Tools

### 1. monitor_store_performance
**Purpose:** Real-time performance monitoring
**Parameters:**
- `monitoring_config` (dict): Monitoring settings

**Returns:** Performance metrics and alerts
**Example:**
```python
monitor_store_performance({
    "collect_system_metrics": True,
    "check_thresholds": True,
    "thresholds": {
        "api_response_time": 3.0,
        "error_rate": 5.0,
        "memory_usage": 85
    }
})
```

### 2. run_store_health_check
**Purpose:** Comprehensive health validation
**Parameters:** None

**Returns:** Health status report
**Example:**
```python
run_store_health_check()
# Returns API connectivity, database status, SSL certificate validity, etc.
```

### 3. create_store_backup
**Purpose:** Create store backup
**Parameters:**
- `backup_config` (dict): Backup settings

**Returns:** Backup creation confirmation
**Example:**
```python
create_store_backup({
    "backup_type": "full",
    "include": ["products", "orders", "customers"],
    "compress": True,
    "encrypt": True
})
```

### 4. restore_store_backup
**Purpose:** Restore from backup
**Parameters:**
- `restore_config` (dict): Restore settings

**Returns:** Restore operation status
**Example:**
```python
restore_store_backup({
    "backup_name": "backup_full_20250126_120000",
    "dry_run": True,
    "restore_products": True,
    "restore_orders": False,
    "restore_customers": False
})
```

### 5. setup_monitoring_schedule
**Purpose:** Configure automated monitoring
**Parameters:**
- `schedule_config` (dict): Schedule settings

**Returns:** Schedule confirmation
**Example:**
```python
setup_monitoring_schedule({
    "monitoring_interval_minutes": 15,
    "backup_interval_hours": 24,
    "health_check_interval_minutes": 5,
    "alert_email": "admin@store.com"
})
```

---

## Multi-Language & Currency Tools

### 1. manage_multi_currency
**Purpose:** Configure multi-currency support
**Parameters:**
- `currency_config` (dict): Currency settings

**Returns:** Currency configuration status
**Example:**
```python
manage_multi_currency({
    "base_currency": "USD",
    "enabled_currencies": ["EUR", "GBP", "JPY"],
    "auto_update_rates": True,
    "update_frequency": "daily",
    "rounding_rules": {
        "EUR": {"decimals": 2, "rounding": "normal"},
        "JPY": {"decimals": 0, "rounding": "up"}
    }
})
```

### 2. manage_translations
**Purpose:** Handle content translations
**Parameters:**
- `translation_data` (dict): Translation configuration

**Returns:** Translation status
**Example:**
```python
manage_translations({
    "languages": ["de", "fr", "es"],
    "content_type": "products",
    "auto_detect": True,
    "professional_review": False
})
```

---

## Store Configuration Tools

### 1. configure_payment_gateways
**Purpose:** Setup payment methods
**Parameters:**
- `gateway_config` (dict): Gateway settings

**Returns:** Configuration status
**Example:**
```python
configure_payment_gateways({
    "stripe": {
        "enabled": True,
        "test_mode": False,
        "public_key": "pk_live_xxx",
        "secret_key": "sk_live_xxx"
    },
    "paypal": {
        "enabled": True,
        "email": "business@store.com"
    }
})
```

### 2. configure_shipping_zones
**Purpose:** Setup shipping regions and methods
**Parameters:**
- `shipping_config` (dict): Shipping settings

**Returns:** Shipping configuration
**Example:**
```python
configure_shipping_zones({
    "zones": [
        {
            "name": "United States",
            "regions": ["US"],
            "methods": [
                {"id": "flat_rate", "cost": "5.00"},
                {"id": "free_shipping", "min_amount": "50.00"}
            ]
        }
    ]
})
```

### 3. configure_tax_settings
**Purpose:** Setup tax rules and rates
**Parameters:**
- `tax_config` (dict): Tax configuration

**Returns:** Tax setup confirmation
**Example:**
```python
configure_tax_settings({
    "enabled": True,
    "prices_include_tax": False,
    "tax_based_on": "shipping",
    "rates": [
        {
            "country": "US",
            "state": "CA",
            "rate": "7.25",
            "name": "CA Sales Tax"
        }
    ]
})
```

---

## Bulk Operations Tools

### 1. execute_bulk_operation
**Purpose:** Safe bulk operations with preview
**Parameters:**
- `operation_config` (dict): Bulk operation settings

**Returns:** Operation results
**Example:**
```python
execute_bulk_operation({
    "operation_type": "update_prices",
    "target_items": "all_products",
    "changes": {
        "increase_by_percent": 10
    },
    "safety_config": {
        "dry_run": True,
        "backup_before": True,
        "batch_size": 50,
        "rollback_on_error": True
    }
})
```

### 2. bulk_import
**Purpose:** Mass data import
**Parameters:**
- `import_config` (dict): Import settings

**Returns:** Import results
**Example:**
```python
bulk_import({
    "data_type": "products",
    "source": "./import/products.csv",
    "mapping": {
        "Product Name": "name",
        "SKU": "sku",
        "Price": "regular_price"
    },
    "options": {
        "update_existing": True,
        "skip_errors": True,
        "validate_before_import": True
    }
})
```

### 3. bulk_export
**Purpose:** Mass data export
**Parameters:**
- `export_config` (dict): Export settings

**Returns:** Export file path
**Example:**
```python
bulk_export({
    "data_type": "orders",
    "format": "csv",
    "filters": {
        "date_after": "2025-01-01",
        "status": ["completed", "processing"]
    },
    "fields": ["order_number", "total", "customer_email", "date"]
})
```

---

## Safety Features

All tools include built-in safety mechanisms:

### Dry-Run Mode
Test operations without making changes:
```python
any_operation({
    "safety_config": {"dry_run": True}
})
```

### Automatic Backup
Create backup before changes:
```python
any_operation({
    "safety_config": {"backup_before": True}
})
```

### Rollback on Error
Automatically revert on failure:
```python
any_operation({
    "safety_config": {"rollback_on_error": True}
})
```

### Rate Limiting
Prevent API overload:
```python
any_operation({
    "safety_config": {
        "rate_limit": 10,
        "batch_size": 50,
        "delay_between_batches": 1.0
    }
})
```

---

## Error Handling

All tools return standardized error responses:

```python
{
    "success": False,
    "error": "Error description",
    "error_code": "ERROR_CODE",
    "timestamp": "2025-01-26T12:00:00Z",
    "context": {
        "operation": "operation_name",
        "parameters": {...}
    },
    "recovery_suggestions": [
        "Suggestion 1",
        "Suggestion 2"
    ]
}
```

---

## Best Practices

1. **Always use dry-run first** for bulk operations
2. **Enable backups** for critical changes
3. **Set appropriate rate limits** to avoid API throttling
4. **Use batch processing** for large datasets
5. **Monitor operation status** with progress callbacks
6. **Validate inputs** before execution
7. **Check permissions** before sensitive operations
8. **Log all operations** for audit trail
9. **Handle errors gracefully** with retry logic
10. **Test in staging** before production deployment

---

## Support & Resources

- **GitHub Issues:** Report bugs and request features
- **Documentation:** See README.md for setup instructions
- **Architecture:** Review ARCHITECTURE.md for system design
- **Examples:** Check examples/ directory for use cases

---

*Last updated: January 26, 2025*
*Version: 2.0.0 - Enterprise Edition*