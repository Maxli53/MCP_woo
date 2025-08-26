"""
Excel Processing Tools
Core tools for processing pricing Excel files and inventory sheets
"""

import logging
import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Document repository base path with environment variable and fallback support
def get_document_repository_path():
    # First: Environment variable
    env_path = os.getenv('DOCUMENT_REPOSITORY')
    if env_path and Path(env_path).exists():
        return Path(env_path)
    
    # Second: Hardcoded known path
    hardcoded_path = "C:/Users/maxli/PycharmProjects/PythonProject/MCP/document_repository"
    if Path(hardcoded_path).exists():
        return Path(hardcoded_path)
    
    # Third: Relative path
    return Path(__file__).parent.parent.parent.parent / "document_repository"

DOCUMENT_REPOSITORY = get_document_repository_path()

def import_excel_data(file_path: str, sheet_name: str = None, sku_column: str = "auto") -> Dict[str, Any]:
    """
    Tool 4: Import and process pricing Excel files with automatic SKU detection
    
    Args:
        file_path: Path to Excel file or document ID from stored documents
        sheet_name: Specific sheet name to process (optional)
        sku_column: SKU column name or "auto" for automatic detection
    
    Returns:
        Processed Excel data organized by SKU with pricing and inventory information
    """
    try:
        # Determine if file_path is a document ID or actual file path
        if file_path.startswith("doc_") and len(file_path) == 25:  # doc_YYYYMMDD_HHMMSS_hash format
            # It's a document ID, get the file path from metadata
            metadata_path = DOCUMENT_REPOSITORY / "_metadata" / f"{file_path}.json"
            
            if not metadata_path.exists():
                return {"error": f"Document metadata not found for ID: {file_path}"}
            
            with open(metadata_path, 'r') as f:
                doc_metadata = json.load(f)
            
            actual_file_path = doc_metadata.get("storage_path")
            if not actual_file_path or not os.path.exists(actual_file_path):
                return {"error": "Document file not found"}
        else:
            # Direct file path or filename - search in document repository
            if os.path.exists(file_path):
                actual_file_path = file_path
            else:
                # Search in document repository structure
                search_paths = [
                    DOCUMENT_REPOSITORY / "pricing_data" / "margin_calculations" / file_path,
                    DOCUMENT_REPOSITORY / "pricing_data" / "supplier_pricing" / file_path,
                    DOCUMENT_REPOSITORY / file_path,
                    DOCUMENT_REPOSITORY / "_temp" / file_path
                ]
                
                actual_file_path = None
                for search_path in search_paths:
                    if search_path.exists():
                        actual_file_path = str(search_path)
                        break
                
                if not actual_file_path:
                    return {"error": f"Excel file not found: {file_path}. Searched in document repository structure."}
                    
            logger.info(f"Using Excel file path: {actual_file_path}")
        
        # Read Excel file
        if sheet_name:
            df = pd.read_excel(actual_file_path, sheet_name=sheet_name)
        else:
            # Read first sheet by default
            df = pd.read_excel(actual_file_path)
        
        # Auto-detect SKU column if needed
        if sku_column == "auto":
            sku_column = detect_sku_column(df)
            if not sku_column:
                return {"error": "Could not auto-detect SKU column"}
        
        # Validate SKU column exists
        if sku_column not in df.columns:
            return {"error": f"SKU column '{sku_column}' not found in Excel file"}
        
        # Process data by SKU
        processed_data = {}
        pricing_data = {}
        inventory_data = {}
        
        for index, row in df.iterrows():
            sku = str(row[sku_column]).strip()
            
            # Skip empty or invalid SKUs
            if not sku or sku == "nan" or pd.isna(sku):
                continue
            
            # Convert row to dictionary and clean up
            row_data = row.to_dict()
            cleaned_data = {}
            
            for key, value in row_data.items():
                # Skip the SKU column itself and empty values
                if key == sku_column or pd.isna(value):
                    continue
                
                # Clean column names and categorize data
                clean_key = str(key).strip().lower()
                
                # Categorize data types
                if any(price_keyword in clean_key for price_keyword in ['price', 'cost', 'msrp', 'retail', 'wholesale']):
                    pricing_data[sku] = pricing_data.get(sku, {})
                    pricing_data[sku][clean_key] = clean_price_value(value)
                elif any(inv_keyword in clean_key for inv_keyword in ['stock', 'inventory', 'quantity', 'available', 'qty']):
                    inventory_data[sku] = inventory_data.get(sku, {})
                    inventory_data[sku][clean_key] = clean_numeric_value(value)
                else:
                    cleaned_data[clean_key] = clean_text_value(value)
            
            # Store comprehensive product data
            processed_data[sku] = {
                "sku": sku,
                "excel_data": cleaned_data,
                "pricing": pricing_data.get(sku, {}),
                "inventory": inventory_data.get(sku, {}),
                "source_file": actual_file_path,
                "source_sheet": sheet_name or "Sheet1",
                "processed_date": datetime.now().isoformat()
            }
        
        # Generate summary statistics
        summary = {
            "total_products": len(processed_data),
            "skus_processed": list(processed_data.keys()),
            "columns_found": list(df.columns),
            "sku_column_used": sku_column,
            "pricing_fields": len([k for data in pricing_data.values() for k in data.keys()]),
            "inventory_fields": len([k for data in inventory_data.values() for k in data.keys()]),
            "processing_date": datetime.now().isoformat(),
            "source_info": {
                "file_path": actual_file_path,
                "sheet_name": sheet_name,
                "total_rows": len(df)
            }
        }
        
        # Store processed data for later consolidation
        temp_folder = DOCUMENT_REPOSITORY / "_temp"
        temp_folder.mkdir(exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = temp_folder / f"excel_import_{timestamp}.json"
        
        export_data = {
            "processed_data": processed_data,
            "summary": summary
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return {
            "success": True,
            "processed_products": len(processed_data),
            "skus_found": list(processed_data.keys())[:20],  # First 20 SKUs for preview
            "summary": summary,
            "temp_file": str(output_file),
            "data": processed_data if len(processed_data) <= 10 else {}  # Include data if small dataset
        }
        
    except Exception as e:
        logger.error(f"Error importing Excel data: {e}")
        return {"error": str(e)}


def detect_sku_column(df: pd.DataFrame) -> Optional[str]:
    """Auto-detect SKU column based on common naming patterns"""
    
    sku_patterns = [
        "sku", "article", "part", "model", "item", "product_code", 
        "article_number", "part_number", "model_number", "code",
        "artikkel", "varenr", "produktkode"  # Nordic variations
    ]
    
    # Check exact matches first
    for column in df.columns:
        column_lower = str(column).lower().strip()
        for pattern in sku_patterns:
            if pattern == column_lower:
                return column
    
    # Check partial matches
    for column in df.columns:
        column_lower = str(column).lower().strip()
        for pattern in sku_patterns:
            if pattern in column_lower:
                return column
    
    # Check for numeric patterns that might be SKUs
    for column in df.columns:
        if df[column].dtype in ['object', 'str']:
            # Check if column contains SKU-like patterns
            sample_values = df[column].dropna().head(10).astype(str)
            if any(is_sku_like(value) for value in sample_values):
                return column
    
    return None


def is_sku_like(value: str) -> bool:
    """Check if a value looks like a SKU"""
    value = str(value).strip()
    
    # Common SKU patterns
    if len(value) < 3 or len(value) > 50:
        return False
    
    # Has alphanumeric characters
    if not any(c.isalnum() for c in value):
        return False
    
    # Contains mix of letters and numbers (typical SKU pattern)
    has_letter = any(c.isalpha() for c in value)
    has_number = any(c.isdigit() for c in value)
    
    return has_letter and has_number


def clean_price_value(value: Any) -> Optional[float]:
    """Clean and convert price values to float"""
    if pd.isna(value):
        return None
    
    try:
        # Convert to string first
        str_value = str(value).strip()
        
        # Remove currency symbols and spaces
        str_value = str_value.replace('$', '').replace('€', '').replace('£', '').replace('kr', '').replace(',', '')
        
        # Convert to float
        return float(str_value)
    except (ValueError, TypeError):
        return None


def clean_numeric_value(value: Any) -> Optional[int]:
    """Clean and convert numeric values to int"""
    if pd.isna(value):
        return None
    
    try:
        # Convert to string first, then to int
        str_value = str(value).strip().replace(',', '')
        return int(float(str_value))  # Handle decimal inputs
    except (ValueError, TypeError):
        return None


def clean_text_value(value: Any) -> Optional[str]:
    """Clean text values"""
    if pd.isna(value):
        return None
    
    try:
        return str(value).strip()
    except (ValueError, TypeError):
        return None


def get_excel_sheet_names(file_path: str) -> Dict[str, Any]:
    """Helper function to get available sheet names from Excel file"""
    try:
        # Handle document ID or direct file path
        if file_path.startswith("doc_") and len(file_path) == 25:
            metadata_path = DOCUMENT_REPOSITORY / "_metadata" / f"{file_path}.json"
            
            if not metadata_path.exists():
                return {"error": f"Document metadata not found for ID: {file_path}"}
            
            with open(metadata_path, 'r') as f:
                doc_metadata = json.load(f)
            
            actual_file_path = doc_metadata.get("storage_path")
            if not actual_file_path or not os.path.exists(actual_file_path):
                return {"error": "Document file not found"}
        else:
            if not os.path.exists(file_path):
                return {"error": f"File not found: {file_path}"}
            actual_file_path = file_path
        
        # Get sheet names
        xl_file = pd.ExcelFile(actual_file_path)
        sheet_names = xl_file.sheet_names
        
        return {
            "success": True,
            "file_path": actual_file_path,
            "sheet_names": sheet_names,
            "total_sheets": len(sheet_names)
        }
        
    except Exception as e:
        logger.error(f"Error getting Excel sheet names: {e}")
        return {"error": str(e)}


def preview_excel_structure(file_path: str, sheet_name: str = None, rows: int = 5) -> Dict[str, Any]:
    """Preview Excel file structure and data"""
    try:
        # Handle document ID or direct file path
        if file_path.startswith("doc_") and len(file_path) == 25:
            metadata_path = DOCUMENT_REPOSITORY / "_metadata" / f"{file_path}.json"
            
            if not metadata_path.exists():
                return {"error": f"Document metadata not found for ID: {file_path}"}
            
            with open(metadata_path, 'r') as f:
                doc_metadata = json.load(f)
            
            actual_file_path = doc_metadata.get("storage_path")
            if not actual_file_path or not os.path.exists(actual_file_path):
                return {"error": "Document file not found"}
        else:
            if not os.path.exists(file_path):
                return {"error": f"File not found: {file_path}"}
            actual_file_path = file_path
        
        # Read Excel file preview
        if sheet_name:
            df = pd.read_excel(actual_file_path, sheet_name=sheet_name, nrows=rows)
        else:
            df = pd.read_excel(actual_file_path, nrows=rows)
        
        # Detect potential SKU column
        potential_sku_column = detect_sku_column(df)
        
        # Convert DataFrame to preview format
        preview_data = df.to_dict('records')
        
        return {
            "success": True,
            "file_path": actual_file_path,
            "sheet_name": sheet_name or "Sheet1",
            "columns": list(df.columns),
            "total_columns": len(df.columns),
            "preview_rows": len(preview_data),
            "potential_sku_column": potential_sku_column,
            "sample_data": preview_data
        }
        
    except Exception as e:
        logger.error(f"Error previewing Excel structure: {e}")
        return {"error": str(e)}