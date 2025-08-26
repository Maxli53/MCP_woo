# Document Management System - API Reference

**Version**: 1.0  
**Date**: August 26, 2025  
**MCP Tools**: 12 available

## Core Tools API

### 1. store_document

Store uploaded documents in appropriate repository folders with automatic categorization.

#### Signature
```python
def store_document(file_data: str, category: str = "auto", metadata: Dict[str, Any] = None) -> str
```

#### Parameters
- **file_data** (str): Base64 encoded file content or file path
  - Format: `data:mime/type;base64,<encoded_content>` or `/path/to/file.pdf`
  - Supported formats: PDF, Excel (.xlsx, .xls), CSV, images
- **category** (str, optional): Document category
  - Values: `"auto"`, `"supplier_catalogs"`, `"pricing_data"`, `"technical_specifications"`, `"marketing_materials"`, `"compliance_documents"`, `"service_manuals"`
  - Default: `"auto"` (automatic categorization)
- **metadata** (Dict, optional): Additional document metadata
  - Keys: `filename`, `supplier`, `date_received`, `version`, `notes`

#### Returns
```json
{
  "success": true,
  "document_id": "doc_20250826_143022_a1b2c3d4e5f6",
  "storage_path": "/path/to/document_repository/supplier_catalogs/doc_20250826_143022_a1b2c3d4e5f6.pdf",
  "category": "supplier_catalogs",
  "metadata": {
    "document_id": "doc_20250826_143022_a1b2c3d4e5f6",
    "original_filename": "lynx_catalogue_2025.pdf",
    "category": "supplier_catalogs",
    "file_size": 2048576,
    "mime_type": "application/pdf",
    "upload_date": "2025-08-26T14:30:22.123456",
    "file_hash": "a1b2c3d4e5f6"
  }
}
```

#### Example Usage
```bash
# Upload PDF catalogue with auto-categorization
store_document(
  file_data="data:application/pdf;base64,JVBERi0xLjQK...",
  metadata={"filename": "lynx_catalogue_2025.pdf", "supplier": "BRP"}
)

# Upload from file path
store_document(
  file_data="/uploads/pricing_sheet.xlsx",
  category="pricing_data",
  metadata={"filename": "pricing_sheet.xlsx", "version": "2.1"}
)
```

---

### 2. process_catalogue

Extract product data from uploaded catalogues organized by SKU.

#### Signature
```python
def process_catalogue(document_id: str) -> str
```

#### Parameters
- **document_id** (str): ID of stored catalogue document
  - Format: `doc_YYYYMMDD_HHMMSS_<hash>` (from store_document response)

#### Returns
```json
{
  "success": true,
  "document_id": "doc_20250826_143022_a1b2c3d4e5f6",
  "extracted_products": 156,
  "skus_found": ["BRP001", "BRP002", "BRP003", "..."],
  "data_path": "/path/to/document_repository/_temp/extracted_doc_20250826_143022_a1b2c3d4e5f6.json",
  "extraction_summary": {
    "total_products": 156,
    "extraction_method": "pdf_parser",
    "skus": ["BRP001", "BRP002", "..."],
    "extraction_date": "2025-08-26T14:35:22.123456"
  }
}
```

#### Supported Formats
- **PDF**: Text extraction and pattern matching
- **Excel**: Column-based data extraction
- **CSV**: Structured data import

#### Example Usage
```bash
# Process uploaded catalogue
process_catalogue(document_id="doc_20250826_143022_a1b2c3d4e5f6")
```

---

### 3. review_products

Simple review interface for manual validation of consolidated product data.

#### Signature
```python
def review_products(sku_list: List[str], review_mode: str = "individual") -> str
```

#### Parameters
- **sku_list** (List[str]): List of SKUs to review
- **review_mode** (str): Review mode
  - Values: `"individual"`, `"batch"`
  - Default: `"individual"`

#### Returns
```json
{
  "success": true,
  "review_mode": "individual",
  "products_for_review": 3,
  "review_data": {
    "BRP001": {
      "sku": "BRP001",
      "source_data": {
        "catalogue_data": {"name": "Snowmobile Track", "category": "Tracks"},
        "excel_data": {"price": 299.99, "stock": 15},
        "database_data": {"manufacturer": "BRP", "weight": "5.2kg"}
      },
      "generated_content": {
        "description": "Professional snowmobile track designed for...",
        "confidence_score": 0.85,
        "generated_date": "2025-08-26T14:40:22.123456"
      },
      "data_completeness": 0.92,
      "conflicts": [],
      "review_status": "pending",
      "review_actions": ["accept", "reject", "edit", "flag_for_manual_review"]
    }
  },
  "batch_actions": []
}
```

#### Example Usage
```bash
# Review individual products
review_products(sku_list=["BRP001", "BRP002", "BRP003"])

# Batch review mode
review_products(sku_list=["BRP001", "BRP002"], review_mode="batch")
```

---

### 4. query_database

Query the fragmented SQL database for product data with multiple query types.

#### Signature
```python
def query_database(query_type: str, parameters: Dict[str, Any] = None) -> str
```

#### Parameters
- **query_type** (str): Type of query to execute
  - Values: `"get_product"`, `"list_skus"`, `"incomplete_products"`, `"ai_template"`, `"custom"`
- **parameters** (Dict): Query-specific parameters

#### Query Types & Parameters

##### get_product
```python
parameters = {"sku": "BRP001"}
```

##### list_skus
```python
parameters = {"limit": 100, "offset": 0}  # Optional
```

##### incomplete_products
```python
parameters = {"missing_fields": ["price", "description"]}  # Optional
```

##### ai_template
```python
parameters = {"template_type": "technical", "language": "en"}
```

##### custom
```python
parameters = {"query": "SELECT * FROM products WHERE category = ?", "params": ["Tracks"]}
```

#### Returns
```json
{
  "success": true,
  "query_type": "get_product",
  "parameters": {"sku": "BRP001"},
  "results": {
    "sku": "BRP001",
    "name": "Snowmobile Track",
    "description": "Professional track for snowmobiles",
    "price": 299.99,
    "category": "Tracks",
    "manufacturer": "BRP",
    "specifications": {"width": "15 inches", "length": "121 inches"}
  },
  "source_tables": ["products", "specifications"],
  "query_date": "2025-08-26T14:45:22.123456"
}
```

#### Example Usage
```bash
# Get specific product data
query_database(query_type="get_product", parameters={"sku": "BRP001"})

# List all available SKUs
query_database(query_type="list_skus")

# Find incomplete products
query_database(query_type="incomplete_products", parameters={"missing_fields": ["price"]})

# Get AI template
query_database(query_type="ai_template", parameters={"template_type": "technical", "language": "en"})

# Custom query
query_database(query_type="custom", parameters={
  "query": "SELECT sku, name FROM products WHERE price > ?",
  "params": [100.0]
})
```

---

### 5. import_excel_data

Import and process pricing Excel files with automatic SKU detection.

#### Signature
```python
def import_excel_data(file_path: str, sheet_name: str = None, sku_column: str = "auto") -> str
```

#### Parameters
- **file_path** (str): Path to Excel file or document ID
  - Format: `/path/to/file.xlsx` or `doc_20250826_143022_a1b2c3d4e5f6`
- **sheet_name** (str, optional): Specific worksheet name
  - Default: None (uses first sheet)
- **sku_column** (str): SKU column identifier
  - Values: `"auto"` (auto-detection) or specific column name
  - Default: `"auto"`

#### Returns
```json
{
  "success": true,
  "processed_products": 89,
  "skus_found": ["BRP001", "BRP002", "BRP003", "..."],
  "summary": {
    "total_products": 89,
    "skus_processed": ["BRP001", "BRP002", "..."],
    "columns_found": ["SKU", "Product Name", "Retail Price", "Cost", "Stock"],
    "sku_column_used": "SKU",
    "pricing_fields": 15,
    "inventory_fields": 3,
    "processing_date": "2025-08-26T14:50:22.123456",
    "source_info": {
      "file_path": "/path/to/pricing.xlsx",
      "sheet_name": "Sheet1",
      "total_rows": 89
    }
  },
  "temp_file": "/path/to/document_repository/_temp/excel_import_20250826_145022.json"
}
```

#### Auto-Detection Features
- **SKU Column Detection**: Finds columns with names like "SKU", "Article", "Part Number", "Model"
- **Data Type Classification**: Automatically categorizes pricing, inventory, and product data
- **Nordic Language Support**: Handles Norwegian, Swedish, Danish column names

#### Example Usage
```bash
# Import with auto-detection
import_excel_data(file_path="/uploads/pricing.xlsx")

# Import specific sheet with manual SKU column
import_excel_data(
  file_path="doc_20250826_143022_a1b2c3d4e5f6", 
  sheet_name="Pricing Data",
  sku_column="Article_Number"
)
```

---

### 6. consolidate_product_data

Consolidate product data from multiple sources with intelligent conflict resolution.

#### Signature
```python
def consolidate_product_data(sku: str, sources: List[str] = None) -> str
```

#### Parameters
- **sku** (str): Product SKU to consolidate
- **sources** (List[str], optional): Data sources to include
  - Values: `["database", "excel", "catalogue", "all"]`
  - Default: `["all"]`

#### Returns
```json
{
  "sku": "BRP001",
  "consolidation_date": "2025-08-26T14:55:22.123456",
  "sources_checked": ["database", "excel", "catalogue"],
  "data_found": {
    "database": {
      "sku": "BRP001",
      "name": "Snowmobile Track",
      "manufacturer": "BRP",
      "specifications": {"width": "15 inches"}
    },
    "excel": {
      "sku": "BRP001",
      "pricing": {"retail_price": 299.99, "cost_price": 180.00},
      "inventory": {"stock_quantity": 15}
    },
    "catalogue": {
      "sku": "BRP001",
      "name": "Professional Snowmobile Track",
      "description": "High-performance track for professional use"
    }
  },
  "consolidated_data": {
    "sku": "BRP001",
    "name": "Professional Snowmobile Track",
    "description": "High-performance track for professional use",
    "price": 299.99,
    "cost": 180.00,
    "inventory": 15,
    "manufacturer": "BRP",
    "specifications": {"width": "15 inches"}
  },
  "conflicts": [
    {
      "field": "name",
      "chosen_source": "catalogue",
      "chosen_value": "Professional Snowmobile Track",
      "conflicting_values": {
        "database": "Snowmobile Track"
      }
    }
  ],
  "confidence_score": 0.85,
  "completeness_score": 0.92,
  "ai_description_ready": true,
  "recommendation": "HIGH_CONFIDENCE - Ready for automated processing"
}
```

#### Consolidation Priority Rules
- **Name/Description**: Catalogue → Database → Excel
- **Pricing**: Excel → Database → Catalogue
- **Inventory**: Excel → Database → Catalogue
- **Specifications**: Catalogue → Database → Excel

#### Confidence Scoring
- **0.8-1.0**: HIGH_CONFIDENCE - Ready for automated processing
- **0.6-0.8**: MEDIUM_CONFIDENCE - Review recommended
- **0.0-0.6**: LOW_CONFIDENCE - Manual review required

#### Example Usage
```bash
# Consolidate from all sources
consolidate_product_data(sku="BRP001")

# Consolidate from specific sources
consolidate_product_data(sku="BRP001", sources=["database", "excel"])
```

---

### 7. generate_descriptions

Generate AI-powered product descriptions using stored templates.

#### Signature
```python
def generate_descriptions(sku_list: List[str], template_type: str = "auto", language: str = "en") -> str
```

#### Parameters
- **sku_list** (List[str]): SKUs to generate descriptions for
- **template_type** (str): Template type
  - Values: `"auto"`, `"technical"`, `"marketing"`, `"basic"`
  - Default: `"auto"`
- **language** (str): Language code
  - Values: `"en"`, `"no"`, `"se"`, `"dk"`
  - Default: `"en"`

#### Returns
```json
{
  "success": true,
  "results": {
    "BRP001": {
      "sku": "BRP001",
      "generated_description": "The Professional Snowmobile Track (SKU: BRP001) represents the pinnacle of snowmobile track technology. Manufactured by BRP, this high-performance track features a 15-inch width design optimized for professional snowmobile applications.\n\nKey specifications include advanced grip patterns for superior traction and durability construction for extended service life. At $299.99, this track offers exceptional value for professional and enthusiast riders seeking reliable performance in demanding conditions.\n\nThis Tracks category product from BRP offers reliable performance and quality construction.",
      "confidence_score": 0.88,
      "template_type": "technical",
      "language": "en",
      "generation_date": "2025-08-26T15:00:22.123456",
      "source_data_quality": 0.92
    }
  },
  "summary": {
    "total_requested": 1,
    "successful_generations": 1,
    "failed_generations": 0,
    "template_used": "technical",
    "language": "en"
  },
  "generation_date": "2025-08-26T15:00:22.123456"
}
```

#### Template Types
- **technical**: Focused on specifications and professional use cases
- **marketing**: Engaging descriptions highlighting benefits and features
- **basic**: Simple, factual descriptions with essential information
- **auto**: Automatically selects based on available data

#### Example Usage
```bash
# Generate with auto template selection
generate_descriptions(sku_list=["BRP001", "BRP002"])

# Generate marketing descriptions in Norwegian
generate_descriptions(
  sku_list=["BRP001"], 
  template_type="marketing", 
  language="no"
)
```

---

## Helper Tools API

### 8. get_excel_sheet_names

Get available sheet names from Excel file.

#### Signature
```python
def get_excel_sheet_names(file_path: str) -> str
```

#### Parameters
- **file_path** (str): Excel file path or document ID

#### Returns
```json
{
  "success": true,
  "file_path": "/path/to/pricing.xlsx",
  "sheet_names": ["Pricing Data", "Inventory", "Specifications"],
  "total_sheets": 3
}
```

---

### 9. preview_excel_structure

Preview Excel file structure and sample data.

#### Signature
```python
def preview_excel_structure(file_path: str, sheet_name: str = None, rows: int = 5) -> str
```

#### Parameters
- **file_path** (str): Excel file path or document ID
- **sheet_name** (str, optional): Specific sheet name
- **rows** (int): Number of preview rows (default: 5)

#### Returns
```json
{
  "success": true,
  "columns": ["SKU", "Product Name", "Retail Price", "Cost", "Stock"],
  "total_columns": 5,
  "preview_rows": 5,
  "potential_sku_column": "SKU",
  "sample_data": [
    {"SKU": "BRP001", "Product Name": "Track", "Retail Price": 299.99},
    {"SKU": "BRP002", "Product Name": "Belt", "Retail Price": 89.99}
  ]
}
```

---

### 10. batch_consolidate_products

Consolidate data for multiple SKUs efficiently.

#### Signature
```python
def batch_consolidate_products(sku_list: List[str], sources: List[str] = None) -> str
```

#### Parameters
- **sku_list** (List[str]): SKUs to consolidate
- **sources** (List[str], optional): Data sources to include

#### Returns
```json
{
  "success": true,
  "batch_results": {
    "BRP001": {"consolidated_data": {...}, "confidence_score": 0.85},
    "BRP002": {"consolidated_data": {...}, "confidence_score": 0.72}
  },
  "summary": {
    "total_processed": 2,
    "successful": 2,
    "failed": 0,
    "high_confidence": 1,
    "needs_review": 1
  }
}
```

---

### 11. batch_review_descriptions

Review and manage generated descriptions in batch.

#### Signature
```python
def batch_review_descriptions(sku_list: List[str], action: str = "preview") -> str
```

#### Parameters
- **sku_list** (List[str]): SKUs to review
- **action** (str): Review action
  - Values: `"preview"`, `"approve"`, `"regenerate"`

#### Returns
```json
{
  "success": true,
  "action": "preview",
  "results": {
    "BRP001": {
      "description": "Professional snowmobile track...",
      "confidence": 0.88,
      "generation_date": "2025-08-26T15:00:22.123456",
      "status": "ready_for_review"
    }
  }
}
```

---

### 12. list_available_templates

List all available description templates.

#### Signature
```python
def list_available_templates() -> str
```

#### Returns
```json
{
  "success": true,
  "templates": {
    "database_templates": [
      {"type": "snowmobile_technical", "language": "en", "description": "Technical snowmobile parts"},
      {"type": "marketing_premium", "language": "no", "description": "Premium marketing copy"}
    ],
    "builtin_templates": ["technical", "marketing", "basic"],
    "supported_languages": ["en", "no", "se", "dk"]
  }
}
```

---

## Error Handling

All tools return standardized error responses:

```json
{
  "error": "Error description",
  "details": "Additional error context",
  "timestamp": "2025-08-26T15:05:22.123456"
}
```

### Common Error Codes
- **File not found**: Document ID or file path invalid
- **Format not supported**: Unsupported file format
- **SKU not found**: SKU not present in any data sources
- **Database connection failed**: SQL database unavailable
- **Template not found**: Specified template doesn't exist

---

## Usage Examples

### Complete Workflow Example
```bash
# 1. Upload catalogue
result1 = store_document(file_data="data:application/pdf;base64,JVBERi...", 
                        metadata={"filename": "catalogue.pdf"})
doc_id = result1["document_id"]

# 2. Process catalogue
result2 = process_catalogue(document_id=doc_id)
skus = result2["skus_found"]

# 3. Import pricing data
result3 = import_excel_data(file_path="/pricing.xlsx")

# 4. Consolidate first product
result4 = consolidate_product_data(sku=skus[0])

# 5. Generate description if high confidence
if result4["confidence_score"] > 0.8:
    result5 = generate_descriptions(sku_list=[skus[0]])
    
# 6. Review before WooCommerce upload
result6 = review_products(sku_list=[skus[0]])
```

### Batch Processing Example
```bash
# Process multiple products efficiently
skus = ["BRP001", "BRP002", "BRP003", "BRP004", "BRP005"]

# Batch consolidate
consolidation_results = batch_consolidate_products(sku_list=skus)

# Identify high-confidence products
high_confidence_skus = []
for sku, result in consolidation_results["batch_results"].items():
    if result.get("confidence_score", 0) > 0.8:
        high_confidence_skus.append(sku)

# Generate descriptions for high-confidence products
if high_confidence_skus:
    description_results = generate_descriptions(sku_list=high_confidence_skus, 
                                              template_type="marketing")
    
    # Batch review
    review_results = batch_review_descriptions(sku_list=high_confidence_skus, 
                                             action="preview")
```

This API reference provides complete documentation for all 12 MCP tools in the Document Management & Product Data Pipeline system.