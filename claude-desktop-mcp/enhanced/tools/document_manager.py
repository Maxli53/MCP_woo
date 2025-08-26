"""
Document Management Tools
Core tools for document storage, catalogue processing, and product review
"""

import logging
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import base64
import mimetypes

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

def store_document(file_data: str, category: str = "auto", metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Tool 1: Store uploaded documents in appropriate repository folders
    
    Args:
        file_data: Base64 encoded file content or file path
        category: Document category (auto-detect if not specified)
        metadata: Optional document metadata
    
    Returns:
        Document storage information including path and metadata
    """
    try:
        # Parse file data
        if file_data.startswith("data:"):
            # Handle base64 encoded data
            header, data = file_data.split(",", 1)
            decoded_data = base64.b64decode(data)
            file_content = decoded_data
            
            # Extract mime type and extension
            mime_type = header.split(":")[1].split(";")[0]
            extension = mimetypes.guess_extension(mime_type) or ".bin"
        else:
            # Handle file path
            if os.path.exists(file_data):
                with open(file_data, 'rb') as f:
                    file_content = f.read()
                extension = Path(file_data).suffix
                mime_type = mimetypes.guess_type(file_data)[0]
            else:
                return {"error": "File not found"}
        
        # Generate document ID and filename
        file_hash = hashlib.md5(file_content).hexdigest()[:12]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        document_id = f"doc_{timestamp}_{file_hash}"
        
        # Auto-categorize if needed
        if category == "auto":
            category = auto_categorize_document(file_content, extension, metadata)
        
        # Determine storage folder
        storage_folder = get_storage_folder(category)
        if not storage_folder.exists():
            storage_folder.mkdir(parents=True, exist_ok=True)
        
        # Create filename
        filename = f"{document_id}{extension}"
        storage_path = storage_folder / filename
        
        # Store document
        with open(storage_path, 'wb') as f:
            f.write(file_content)
        
        # Create metadata
        doc_metadata = {
            "document_id": document_id,
            "original_filename": metadata.get("filename") if metadata else "unknown",
            "category": category,
            "storage_path": str(storage_path),
            "file_size": len(file_content),
            "mime_type": mime_type,
            "upload_date": datetime.now().isoformat(),
            "file_hash": file_hash,
            "custom_metadata": metadata or {}
        }
        
        # Store metadata
        metadata_folder = DOCUMENT_REPOSITORY / "_metadata"
        metadata_folder.mkdir(exist_ok=True)
        metadata_path = metadata_folder / f"{document_id}.json"
        
        with open(metadata_path, 'w') as f:
            json.dump(doc_metadata, f, indent=2)
        
        return {
            "success": True,
            "document_id": document_id,
            "storage_path": str(storage_path),
            "category": category,
            "metadata": doc_metadata
        }
        
    except Exception as e:
        logger.error(f"Error storing document: {e}")
        return {"error": str(e)}


def process_catalogue(document_id: str) -> Dict[str, Any]:
    """
    Tool 3: Extract product data from uploaded catalogues by SKU
    
    Args:
        document_id: ID of stored catalogue document
    
    Returns:
        Extracted product data organized by SKU
    """
    try:
        # Get document metadata and path
        metadata_path = DOCUMENT_REPOSITORY / "_metadata" / f"{document_id}.json"
        
        if not metadata_path.exists():
            return {"error": "Document metadata not found"}
        
        with open(metadata_path, 'r') as f:
            doc_metadata = json.load(f)
        
        storage_path = doc_metadata.get("storage_path")
        if not storage_path or not os.path.exists(storage_path):
            return {"error": "Document file not found"}
        
        # Extract data based on file type
        file_extension = Path(storage_path).suffix.lower()
        
        if file_extension == ".pdf":
            extracted_data = extract_from_pdf(storage_path)
        elif file_extension in [".xlsx", ".xls"]:
            extracted_data = extract_from_excel(storage_path)
        elif file_extension == ".csv":
            extracted_data = extract_from_csv(storage_path)
        else:
            return {"error": f"Unsupported file type: {file_extension}"}
        
        # Organize data by SKU
        organized_data = organize_by_sku(extracted_data)
        
        # Store extracted data for future reference
        extracted_data_path = DOCUMENT_REPOSITORY / "_temp" / f"extracted_{document_id}.json"
        extracted_data_path.parent.mkdir(exist_ok=True)
        
        with open(extracted_data_path, 'w') as f:
            json.dump(organized_data, f, indent=2)
        
        return {
            "success": True,
            "document_id": document_id,
            "extracted_products": len(organized_data.get("products", {})),
            "skus_found": list(organized_data.get("products", {}).keys()),
            "data_path": str(extracted_data_path),
            "extraction_summary": organized_data.get("summary", {})
        }
        
    except Exception as e:
        logger.error(f"Error processing catalogue {document_id}: {e}")
        return {"error": str(e)}


def review_products(sku_list: List[str], review_mode: str = "individual") -> Dict[str, Any]:
    """
    Tool 7: Simple review interface for manual validation
    
    Args:
        sku_list: List of SKUs to review
        review_mode: Review mode (individual, batch)
    
    Returns:
        Review interface data and actions
    """
    try:
        review_data = {}
        
        for sku in sku_list:
            # Get consolidated product data
            from .data_consolidator import consolidate_product_data
            consolidated_data = consolidate_product_data(sku)
            
            if consolidated_data.get("error"):
                continue
            
            # Prepare review information
            review_item = {
                "sku": sku,
                "source_data": {
                    "catalogue_data": consolidated_data.get("catalogue_data", {}),
                    "excel_data": consolidated_data.get("excel_data", {}),
                    "database_data": consolidated_data.get("database_data", {})
                },
                "generated_content": {
                    "description": consolidated_data.get("ai_description"),
                    "confidence_score": consolidated_data.get("confidence_score", 0),
                    "generated_date": consolidated_data.get("generation_date")
                },
                "data_completeness": calculate_completeness_score(consolidated_data),
                "conflicts": consolidated_data.get("conflicts", []),
                "review_status": "pending",
                "review_actions": ["accept", "reject", "edit", "flag_for_manual_review"]
            }
            
            review_data[sku] = review_item
        
        return {
            "success": True,
            "review_mode": review_mode,
            "products_for_review": len(review_data),
            "review_data": review_data,
            "batch_actions": ["accept_all", "reject_all", "export_for_review"] if review_mode == "batch" else []
        }
        
    except Exception as e:
        logger.error(f"Error preparing product review: {e}")
        return {"error": str(e)}


# Helper functions

def auto_categorize_document(file_content: bytes, extension: str, metadata: Dict[str, Any] = None) -> str:
    """Auto-categorize document based on content and filename"""
    
    # Category mapping based on content and filename patterns
    category_patterns = {
        "supplier_catalogs": ["catalog", "catalogue", "product", "spec", "lynx", "ski-doo", "can-am"],
        "pricing_data": ["price", "pricing", "cost", "msrp", "retail"],
        "technical_specifications": ["spec", "technical", "manual", "guide", "dimension"],
        "marketing_materials": ["marketing", "brochure", "image", "photo", "promotional"],
        "compliance_documents": ["compliance", "certification", "safety", "regulatory"],
        "service_manuals": ["service", "maintenance", "repair", "parts", "warranty"]
    }
    
    # Check filename and metadata for patterns
    filename = metadata.get("filename", "").lower() if metadata else ""
    
    for category, patterns in category_patterns.items():
        for pattern in patterns:
            if pattern in filename:
                return category
    
    # Default category based on file type
    if extension.lower() in [".pdf"]:
        return "supplier_catalogs"
    elif extension.lower() in [".xlsx", ".xls", ".csv"]:
        return "pricing_data"
    else:
        return "technical_specifications"


def get_storage_folder(category: str) -> Path:
    """Get appropriate storage folder for document category"""
    
    folder_mapping = {
        "supplier_catalogs": DOCUMENT_REPOSITORY / "supplier_catalogs",
        "pricing_data": DOCUMENT_REPOSITORY / "pricing_data",
        "technical_specifications": DOCUMENT_REPOSITORY / "technical_specifications",
        "marketing_materials": DOCUMENT_REPOSITORY / "marketing_materials",
        "compliance_documents": DOCUMENT_REPOSITORY / "compliance_documents",
        "service_manuals": DOCUMENT_REPOSITORY / "service_manuals",
        "inventory_sheets": DOCUMENT_REPOSITORY / "inventory_sheets",
        "supplier_availability": DOCUMENT_REPOSITORY / "supplier_availability"
    }
    
    return folder_mapping.get(category, DOCUMENT_REPOSITORY / "technical_specifications")


def extract_from_pdf(file_path: str) -> Dict[str, Any]:
    """Extract data from PDF catalogue (placeholder - needs PDF parsing library)"""
    # TODO: Implement PDF text extraction
    # For now, return placeholder structure
    return {
        "extraction_method": "pdf_parser",
        "raw_text": "PDF content extraction not yet implemented",
        "products": {}
    }


def extract_from_excel(file_path: str) -> Dict[str, Any]:
    """Extract data from Excel file"""
    try:
        import pandas as pd
        
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Convert to dictionary format
        products = {}
        for index, row in df.iterrows():
            # Look for SKU column
            sku = None
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ["sku", "article", "part", "model"]):
                    sku = str(row[col]).strip()
                    break
            
            if sku and sku != "nan":
                products[sku] = row.to_dict()
        
        return {
            "extraction_method": "excel_parser",
            "total_rows": len(df),
            "products": products
        }
        
    except Exception as e:
        logger.error(f"Error extracting from Excel: {e}")
        return {"error": str(e)}


def extract_from_csv(file_path: str) -> Dict[str, Any]:
    """Extract data from CSV file"""
    try:
        import pandas as pd
        
        # Read CSV file
        df = pd.read_csv(file_path)
        
        # Convert to dictionary format (similar to Excel)
        products = {}
        for index, row in df.iterrows():
            # Look for SKU column
            sku = None
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ["sku", "article", "part", "model"]):
                    sku = str(row[col]).strip()
                    break
            
            if sku and sku != "nan":
                products[sku] = row.to_dict()
        
        return {
            "extraction_method": "csv_parser",
            "total_rows": len(df),
            "products": products
        }
        
    except Exception as e:
        logger.error(f"Error extracting from CSV: {e}")
        return {"error": str(e)}


def organize_by_sku(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """Organize extracted data by SKU"""
    
    products = extracted_data.get("products", {})
    
    organized = {
        "products": products,
        "summary": {
            "total_products": len(products),
            "extraction_method": extracted_data.get("extraction_method"),
            "skus": list(products.keys()),
            "extraction_date": datetime.now().isoformat()
        }
    }
    
    return organized


def calculate_completeness_score(consolidated_data: Dict[str, Any]) -> float:
    """Calculate data completeness score for a product"""
    
    required_fields = ["name", "sku", "price", "description"]
    optional_fields = ["specifications", "images", "category", "manufacturer"]
    
    total_fields = len(required_fields) + len(optional_fields)
    filled_fields = 0
    
    # Check required fields (weight: 2x)
    for field in required_fields:
        if consolidated_data.get(field):
            filled_fields += 2
    
    # Check optional fields (weight: 1x)
    for field in optional_fields:
        if consolidated_data.get(field):
            filled_fields += 1
    
    max_score = (len(required_fields) * 2) + len(optional_fields)
    return filled_fields / max_score if max_score > 0 else 0