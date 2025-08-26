"""
Database Integration Tools
Core tool for connecting to and querying the fragmented SQL database
"""

import logging
import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Default database connection settings
DEFAULT_DB_PATH = None  # Will be set by user configuration
CONNECTION_POOL = {}    # Simple connection pooling

def query_database(query_type: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Tool 2: Connect to fragmented SQL database and query product data
    
    Args:
        query_type: Type of query (get_product_by_sku, list_all_skus, get_incomplete_products, etc.)
        parameters: Dictionary containing query parameters like {'sku': 'ABC123', 'filters': {...}}
    
    Returns:
        Query results with product data
    """
    try:
        # Handle parameters
        if parameters is None:
            parameters = {}
        
        # Extract common parameters
        sku = parameters.get('sku')
        filters = parameters.get('filters', {})
        
        # Get database connection
        connection = get_database_connection()
        if not connection:
            return {"error": "Database connection failed"}
        
        # Execute query based on type (with backward compatibility)
        if query_type in ["get_product_by_sku", "get_product"]:
            if not sku:
                return {"error": "SKU required for product query"}
            return get_product_by_sku(connection, sku)
            
        elif query_type in ["list_all_skus", "list_skus"]:
            return list_all_skus(connection, filters or {})
            
        elif query_type == "get_incomplete_products":
            return get_incomplete_products(connection, filters or {})
            
        elif query_type == "search_products":
            return search_products(connection, filters or {})
            
        elif query_type == "get_ai_template":
            template_type = parameters.get('template_type', 'basic')
            language = parameters.get('language', 'en')
            return get_ai_template(connection, template_type, language)
            
        elif query_type == "get_schema_info":
            return get_schema_info(connection)
            
        elif query_type == "update_product":
            if not sku:
                return {"error": "SKU required for product update"}
            return update_product_data(connection, sku, filters or {})
            
        elif query_type == "analyze_database":
            return analyze_database_structure(connection)
            
        else:
            return {"error": f"Unknown query type: {query_type}"}
            
    except Exception as e:
        logger.error(f"Database query error: {e}")
        return {"error": str(e)}


def get_database_connection(db_path: str = None) -> Optional[sqlite3.Connection]:
    """Get database connection with simple pooling"""
    
    try:
        # Use provided path or default
        if not db_path:
            db_path = DEFAULT_DB_PATH or get_default_db_path()
        
        # Check connection pool
        if db_path in CONNECTION_POOL:
            conn = CONNECTION_POOL[db_path]
            # Test connection
            conn.execute("SELECT 1")
            return conn
        
        # Create new connection
        if not Path(db_path).exists():
            logger.error(f"Database file not found: {db_path}")
            return None
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        
        # Store in pool
        CONNECTION_POOL[db_path] = conn
        
        return conn
        
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None


def get_product_by_sku(connection: sqlite3.Connection, sku: str) -> Dict[str, Any]:
    """Get complete product data for a specific SKU"""
    
    try:
        # Try different possible table structures since database is fragmented
        tables_to_check = [
            "articles", "products", "product_data", "snowmobile_products", 
            "items", "catalogue_data", "product_info"
        ]
        
        product_data = {}
        
        for table in tables_to_check:
            try:
                # Check if table exists
                cursor = connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
                    (table,)
                )
                if not cursor.fetchone():
                    continue
                
                # Get table columns
                columns = get_table_columns(connection, table)
                
                # Find SKU column (might have different names)
                sku_column = find_sku_column(columns)
                if not sku_column:
                    continue
                
                # Query the table
                query = f"SELECT * FROM {table} WHERE {sku_column} = ?"
                cursor = connection.execute(query, (sku,))
                rows = cursor.fetchall()
                
                if rows:
                    # Convert row to dictionary and merge with existing data
                    for row in rows:
                        row_dict = dict(row)
                        product_data.update(row_dict)
                
            except Exception as e:
                logger.warning(f"Error querying table {table}: {e}")
                continue
        
        if not product_data:
            return {"error": f"Product not found for SKU: {sku}"}
        
        return {
            "success": True,
            "sku": sku,
            "product_data": product_data,
            "data_completeness": calculate_data_completeness(product_data),
            "source_tables": [t for t in tables_to_check if check_table_has_sku(connection, t, sku)]
        }
        
    except Exception as e:
        logger.error(f"Error getting product {sku}: {e}")
        return {"error": str(e)}


def list_all_skus(connection: sqlite3.Connection, filters: Dict[str, Any]) -> Dict[str, Any]:
    """Get list of all available SKUs in database"""
    
    try:
        all_skus = set()
        
        # Priority tables with actual SKUs (article_code)
        priority_tables = ["articles", "article_kb_mapping", "articles_complete"]
        fallback_tables = []
        
        tables = get_all_tables(connection)
        
        # Separate priority tables from others
        for table in tables:
            if any(pt in table for pt in ["articles"]) and "backup" not in table:
                priority_tables.append(table)
            else:
                fallback_tables.append(table)
        
        # First, get SKUs from priority tables with article_code
        for table in priority_tables:
            try:
                columns = get_table_columns(connection, table)
                if "article_code" in columns:
                    query = f"SELECT DISTINCT article_code FROM {table} WHERE article_code IS NOT NULL"
                    cursor = connection.execute(query)
                    
                    for row in cursor:
                        sku = str(row[0]).strip()
                        if sku and sku.lower() != "null":
                            all_skus.add(sku)
                            
            except Exception as e:
                logger.warning(f"Error checking priority table {table}: {e}")
                continue
        
        # Only if we didn't find enough SKUs, check other tables (excluding model_line)
        if len(all_skus) < 10:
            for table in fallback_tables:
                try:
                    columns = get_table_columns(connection, table)
                    sku_column = find_sku_column(columns)
                    
                    # Skip model_line columns to avoid model names being treated as SKUs
                    if sku_column and sku_column != "model_line":
                        query = f"SELECT DISTINCT {sku_column} FROM {table} WHERE {sku_column} IS NOT NULL"
                        cursor = connection.execute(query)
                        
                        for row in cursor:
                            sku = str(row[0]).strip()
                            if sku and sku.lower() != "null":
                                all_skus.add(sku)
                                
                except Exception as e:
                    logger.warning(f"Error checking fallback table {table}: {e}")
                    continue
        
        sku_list = sorted(list(all_skus))
        
        # Apply filters if provided
        if filters.get("manufacturer"):
            sku_list = [sku for sku in sku_list if filters["manufacturer"].lower() in sku.lower()]
        
        if filters.get("limit"):
            sku_list = sku_list[:filters["limit"]]
        
        return {
            "success": True,
            "total_skus": len(sku_list),
            "skus": sku_list,
            "results": sku_list,  # Add results key for compatibility
            "source_tables": tables
        }
        
    except Exception as e:
        logger.error(f"Error listing SKUs: {e}")
        return {"error": str(e)}


def get_incomplete_products(connection: sqlite3.Connection, filters: Dict[str, Any]) -> Dict[str, Any]:
    """Find products with incomplete data"""
    
    try:
        all_skus_result = list_all_skus(connection, {})
        if not all_skus_result.get("success"):
            return all_skus_result
        
        incomplete_products = []
        
        for sku in all_skus_result["skus"][:50]:  # Limit to first 50 for performance
            product_result = get_product_by_sku(connection, sku)
            
            if product_result.get("success"):
                completeness = product_result.get("data_completeness", 0)
                if completeness < 0.7:  # Less than 70% complete
                    incomplete_products.append({
                        "sku": sku,
                        "completeness_score": completeness,
                        "missing_fields": identify_missing_fields(product_result.get("product_data", {}))
                    })
        
        return {
            "success": True,
            "incomplete_products": len(incomplete_products),
            "products": incomplete_products
        }
        
    except Exception as e:
        logger.error(f"Error finding incomplete products: {e}")
        return {"error": str(e)}


def search_products(connection: sqlite3.Connection, filters: Dict[str, Any]) -> Dict[str, Any]:
    """Search products based on filters"""
    
    try:
        search_term = filters.get("search_term", "")
        manufacturer = filters.get("manufacturer", "")
        limit = filters.get("limit", 50)
        
        matching_products = []
        
        # Get all SKUs first
        all_skus_result = list_all_skus(connection, {})
        if not all_skus_result.get("success"):
            return all_skus_result
        
        for sku in all_skus_result["skus"][:limit]:
            # Basic SKU matching
            if search_term and search_term.lower() not in sku.lower():
                continue
                
            if manufacturer and manufacturer.lower() not in sku.lower():
                continue
            
            product_result = get_product_by_sku(connection, sku)
            if product_result.get("success"):
                matching_products.append({
                    "sku": sku,
                    "data_completeness": product_result.get("data_completeness", 0),
                    "basic_info": extract_basic_info(product_result.get("product_data", {}))
                })
        
        return {
            "success": True,
            "matching_products": len(matching_products),
            "products": matching_products
        }
        
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        return {"error": str(e)}


def get_ai_template(connection: sqlite3.Connection, template_type: str = "basic", language: str = "en") -> Dict[str, Any]:
    """Extract AI description template from database"""
    
    try:
        # Look for specific template first
        specific_queries = [
            f"SELECT * FROM ai_templates WHERE template_type='{template_type}' AND language='{language}'",
            f"SELECT * FROM description_templates WHERE type='{template_type}' AND lang='{language}'",
            f"SELECT * FROM templates WHERE template_type='{template_type}' AND language='{language}'",
        ]
        
        template_data = {}
        
        # Try specific template queries first
        for query in specific_queries:
            try:
                cursor = connection.execute(query)
                rows = cursor.fetchall()
                
                if rows:
                    row_dict = dict(rows[0])  # Take first match
                    template_data = row_dict
                    break
                    
            except Exception:
                continue
        
        # If no specific template, try general queries
        if not template_data:
            general_queries = [
                "SELECT * FROM ai_templates LIMIT 1",
                "SELECT * FROM description_templates LIMIT 1", 
                "SELECT * FROM templates WHERE type='description' LIMIT 1",
                "SELECT * FROM settings WHERE key LIKE '%template%' LIMIT 1"
            ]
            
            for query in general_queries:
                try:
                    cursor = connection.execute(query)
                    rows = cursor.fetchall()
                    
                    if rows:
                        row_dict = dict(rows[0])
                        template_data = row_dict
                        break
                        
                except Exception:
                    continue
        
        if not template_data:
            # Return built-in template structure based on type
            builtin_templates = {
                "technical": {
                    "template": "Generate a technical product description for {name} (SKU: {sku}).\n\nKey Information:\n- Category: {category}\n- Manufacturer: {manufacturer}\n- Specifications: {specifications}\n- Price: {price}\n\nCreate a detailed technical description focusing on specifications and professional use cases.",
                    "fields": ["name", "specifications", "manufacturer", "category"]
                },
                "marketing": {
                    "template": "Create an engaging marketing description for {name} (SKU: {sku}).\n\nKey Information:\n- Category: {category}\n- Manufacturer: {manufacturer}\n- Key Features: {specifications}\n- Price: {price}\n\nWrite a compelling product description that highlights benefits and appeals to customers.",
                    "fields": ["name", "category", "manufacturer", "price"]
                },
                "basic": {
                    "template": "Create a basic product description for {name} (SKU: {sku}).\n\nProduct Details:\n- Category: {category}\n- Brand: {manufacturer}\n- Price: {price}\n\nWrite a clear, concise description covering the essential product information.",
                    "fields": ["name", "category", "manufacturer"]
                }
            }
            
            selected_template = builtin_templates.get(template_type, builtin_templates["basic"])
            
            return {
                "template_type": template_type,
                "language": language,
                "template": selected_template["template"],
                "required_fields": selected_template["fields"],
                "template_info": {
                    "source": "builtin",
                    "template_id": f"{template_type}_{language}"
                }
            }
        
        # Process database template data
        return {
            "template_type": template_type,
            "language": language,
            "template": template_data.get("template", template_data.get("content", template_data.get("description", ""))),
            "required_fields": template_data.get("required_fields", ["name", "category"]),
            "template_info": {
                "source": "database",
                "template_id": template_data.get("id", f"db_{template_type}_{language}"),
                "raw_data": template_data
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting AI template: {e}")
        return {"error": str(e)}


def get_schema_info(connection: sqlite3.Connection) -> Dict[str, Any]:
    """Get database schema information"""
    
    try:
        tables = get_all_tables(connection)
        
        schema_info = {}
        for table in tables:
            try:
                columns = get_table_columns(connection, table)
                row_count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                
                schema_info[table] = {
                    "columns": columns,
                    "row_count": row_count,
                    "has_sku_column": bool(find_sku_column(columns))
                }
                
            except Exception as e:
                schema_info[table] = {"error": str(e)}
        
        return {
            "success": True,
            "total_tables": len(tables),
            "tables": schema_info
        }
        
    except Exception as e:
        logger.error(f"Error getting schema info: {e}")
        return {"error": str(e)}


def update_product_data(connection: sqlite3.Connection, sku: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update product data in database"""
    
    try:
        # This is a placeholder - actual implementation depends on your database structure
        # For now, we'll create a updates log
        
        updates_log = {
            "sku": sku,
            "update_data": update_data,
            "timestamp": datetime.now().isoformat(),
            "status": "logged_for_manual_review"
        }
        
        # TODO: Implement actual database update logic based on your schema
        
        return {
            "success": True,
            "sku": sku,
            "updates_applied": False,
            "message": "Update logged for manual review - automatic updates not yet implemented",
            "update_log": updates_log
        }
        
    except Exception as e:
        logger.error(f"Error updating product {sku}: {e}")
        return {"error": str(e)}


def analyze_database_structure(connection: sqlite3.Connection) -> Dict[str, Any]:
    """Comprehensive database analysis for migration planning"""
    
    try:
        analysis = {
            "tables": {},
            "data_completeness": {},
            "recommendations": []
        }
        
        tables = get_all_tables(connection)
        
        for table in tables:
            columns = get_table_columns(connection, table)
            row_count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            
            analysis["tables"][table] = {
                "columns": columns,
                "row_count": row_count,
                "has_sku_column": bool(find_sku_column(columns)),
                "estimated_completeness": estimate_table_completeness(connection, table, columns)
            }
        
        # Generate recommendations
        analysis["recommendations"] = generate_migration_recommendations(analysis["tables"])
        
        return {
            "success": True,
            "analysis": analysis,
            "total_tables": len(tables),
            "tables_with_skus": sum(1 for t in analysis["tables"].values() if t["has_sku_column"])
        }
        
    except Exception as e:
        logger.error(f"Error analyzing database: {e}")
        return {"error": str(e)}


# Helper functions

def get_default_db_path() -> str:
    """Get default database path with environment variable support and fallbacks"""
    
    # First priority: Environment variable
    env_db_path = os.getenv('DATABASE_PATH')
    if env_db_path and Path(env_db_path).exists():
        return env_db_path
    
    # Second priority: Document repository temp folder (Snowmobile.db)
    repo_path = os.getenv('DOCUMENT_REPOSITORY')
    if repo_path:
        snowmobile_db = Path(repo_path) / "_temp" / "Snowmobile.db"
        if snowmobile_db.exists():
            return str(snowmobile_db)
    
    # Third priority: Hardcoded known path (YOUR ACTUAL PATH)
    hardcoded_path = "C:/Users/maxli/PycharmProjects/PythonProject/MCP/document_repository/_temp/Snowmobile.db"
    if Path(hardcoded_path).exists():
        logger.info(f"Using hardcoded Snowmobile.db path: {hardcoded_path}")
        return hardcoded_path
    
    # Fourth priority: Relative path from current location
    base_path = Path(__file__).parent.parent.parent.parent
    snowmobile_paths = [
        base_path / "document_repository" / "_temp" / "Snowmobile.db",
        base_path / "_temp" / "Snowmobile.db",
        base_path / "test_documents" / "Snowmobile.db"
    ]
    
    for path in snowmobile_paths:
        if path.exists():
            logger.info(f"Using relative path: {path}")
            return str(path)
    
    # Fifth priority: Test database
    test_db = base_path / "test_documents" / "test_db.sqlite"
    if test_db.exists():
        return str(test_db)
    
    # Log available paths for debugging
    logger.info(f"DATABASE_PATH env var: {env_db_path}")
    logger.info(f"DOCUMENT_REPOSITORY env var: {repo_path}")
    logger.info(f"Searched paths: {[str(p) for p in snowmobile_paths]}")
    
    # Return placeholder path
    return "database_path_not_configured"


def get_all_tables(connection: sqlite3.Connection) -> List[str]:
    """Get list of all tables in database"""
    cursor = connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return [row[0] for row in cursor.fetchall()]


def get_table_columns(connection: sqlite3.Connection, table: str) -> List[str]:
    """Get column names for a table"""
    cursor = connection.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cursor.fetchall()]


def find_sku_column(columns: List[str]) -> Optional[str]:
    """Find SKU column from list of column names"""
    # Priority order: article_code first (our main SKU field), then others
    priority_patterns = ["article_code"]  # Highest priority
    exact_patterns = ["sku", "part_number", "product_code", "item_code"]
    partial_patterns = ["model_line"]  # Lower priority, only if no better match
    
    # Check for article_code first (our main SKU field)
    for column in columns:
        if column.lower() in priority_patterns:
            return column
    
    # Then check for other exact matches
    for column in columns:
        if column.lower() in exact_patterns:
            return column
    
    # Finally check partial matches, excluding ID fields
    for column in columns:
        if "_id" not in column.lower():  # Exclude ID fields like article_id
            for pattern in partial_patterns:
                if pattern in column.lower():
                    return column
    return None


def check_table_has_sku(connection: sqlite3.Connection, table: str, sku: str) -> bool:
    """Check if table contains specific SKU"""
    try:
        columns = get_table_columns(connection, table)
        sku_column = find_sku_column(columns)
        
        if not sku_column:
            return False
        
        cursor = connection.execute(f"SELECT 1 FROM {table} WHERE {sku_column} = ? LIMIT 1", (sku,))
        return bool(cursor.fetchone())
        
    except Exception:
        return False


def calculate_data_completeness(product_data: Dict[str, Any]) -> float:
    """Calculate how complete the product data is"""
    
    important_fields = ["name", "price", "description", "manufacturer", "specifications"]
    filled_fields = sum(1 for field in important_fields if product_data.get(field))
    
    return filled_fields / len(important_fields) if important_fields else 0


def identify_missing_fields(product_data: Dict[str, Any]) -> List[str]:
    """Identify which important fields are missing"""
    
    important_fields = ["name", "price", "description", "manufacturer", "specifications"]
    return [field for field in important_fields if not product_data.get(field)]


def extract_basic_info(product_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract basic product information for search results"""
    
    return {
        "name": product_data.get("name"),
        "manufacturer": product_data.get("manufacturer"),
        "price": product_data.get("price"),
        "category": product_data.get("category")
    }


def estimate_table_completeness(connection: sqlite3.Connection, table: str, columns: List[str]) -> float:
    """Estimate data completeness for a table"""
    
    try:
        total_rows = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        if total_rows == 0:
            return 0.0
        
        filled_cells = 0
        total_cells = total_rows * len(columns)
        
        for column in columns:
            cursor = connection.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} IS NOT NULL AND {column} != ''")
            filled_cells += cursor.fetchone()[0]
        
        return filled_cells / total_cells if total_cells > 0 else 0.0
        
    except Exception:
        return 0.0


def generate_migration_recommendations(tables_analysis: Dict[str, Any]) -> List[str]:
    """Generate recommendations for database migration"""
    
    recommendations = []
    
    tables_with_skus = [name for name, info in tables_analysis.items() if info.get("has_sku_column")]
    if not tables_with_skus:
        recommendations.append("No tables with SKU columns found - manual mapping required")
    
    if len(tables_with_skus) > 3:
        recommendations.append(f"Multiple tables with SKUs found ({len(tables_with_skus)}) - consider consolidation")
    
    low_completeness_tables = [
        name for name, info in tables_analysis.items() 
        if info.get("estimated_completeness", 0) < 0.3
    ]
    
    if low_completeness_tables:
        recommendations.append(f"Low data completeness in tables: {', '.join(low_completeness_tables)}")
    
    return recommendations