"""
Database Integration Tools
Core tool for connecting to and querying the fragmented SQL database
"""

import logging
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Default database connection settings
DEFAULT_DB_PATH = None  # Will be set by user configuration
CONNECTION_POOL = {}    # Simple connection pooling

def query_database(query_type: str, sku: str = None, filters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Tool 2: Connect to fragmented SQL database and query product data
    
    Args:
        query_type: Type of query (get_product_by_sku, list_all_skus, get_incomplete_products, etc.)
        sku: Product SKU for specific queries
        filters: Additional filters for queries
    
    Returns:
        Query results with product data
    """
    try:
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
            return get_ai_template(connection)
            
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
        
        # Check all potential tables
        tables = get_all_tables(connection)
        
        for table in tables:
            try:
                columns = get_table_columns(connection, table)
                sku_column = find_sku_column(columns)
                
                if sku_column:
                    query = f"SELECT DISTINCT {sku_column} FROM {table} WHERE {sku_column} IS NOT NULL"
                    cursor = connection.execute(query)
                    
                    for row in cursor:
                        sku = str(row[0]).strip()
                        if sku and sku.lower() != "null":
                            all_skus.add(sku)
                            
            except Exception as e:
                logger.warning(f"Error checking table {table}: {e}")
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


def get_ai_template(connection: sqlite3.Connection) -> Dict[str, Any]:
    """Extract AI description template from database"""
    
    try:
        # Look for template in different possible locations
        template_queries = [
            "SELECT * FROM ai_templates",
            "SELECT * FROM description_templates", 
            "SELECT * FROM templates WHERE type='description'",
            "SELECT * FROM settings WHERE key LIKE '%template%'"
        ]
        
        template_data = {}
        
        for query in template_queries:
            try:
                cursor = connection.execute(query)
                rows = cursor.fetchall()
                
                if rows:
                    for row in rows:
                        row_dict = dict(row)
                        template_data.update(row_dict)
                    break
                    
            except Exception:
                continue
        
        if not template_data:
            # Return default template structure
            return {
                "success": True,
                "template_found": False,
                "default_template": {
                    "intro": "{product_name} by {manufacturer}",
                    "specifications": "Technical specifications: {engine_specs}",
                    "features": "Key features include {key_features}",
                    "conclusion": "Perfect for {intended_use}"
                },
                "message": "No custom template found in database, using default structure"
            }
        
        return {
            "success": True,
            "template_found": True,
            "template_data": template_data
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
    
    # Third priority: Relative path from current location
    base_path = Path(__file__).parent.parent.parent.parent
    snowmobile_paths = [
        base_path / "document_repository" / "_temp" / "Snowmobile.db",
        base_path / "_temp" / "Snowmobile.db",
        base_path / "test_documents" / "Snowmobile.db"
    ]
    
    for path in snowmobile_paths:
        if path.exists():
            return str(path)
    
    # Fourth priority: Test database
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
    sku_patterns = ["sku", "article", "part", "model", "product_id", "item_code"]
    
    for column in columns:
        for pattern in sku_patterns:
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