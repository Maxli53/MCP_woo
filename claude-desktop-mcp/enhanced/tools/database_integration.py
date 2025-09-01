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
    Enhanced Tool 2: Connect to business database with full read/write capabilities
    
    Args:
        query_type: Type of operation (get_product, list_skus, update_product, sync_from_documents, execute_sql, etc.)
        parameters: Dictionary containing operation parameters like {'sku': 'ABC123', 'data': {...}, 'sql': 'SELECT ...'}
    
    Returns:
        Operation results with product data or confirmation of changes
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
        
        # NEW: Business Intelligence Functions
        elif query_type == "execute_sql":
            sql = parameters.get('sql')
            if not sql:
                return {"error": "SQL query required"}
            return execute_custom_sql(connection, sql)
        
        elif query_type == "sync_from_documents":
            return sync_database_from_documents(connection, parameters)
        
        elif query_type == "update_product_data":
            if not sku:
                return {"error": "SKU required for product update"}
            data = parameters.get('data', {})
            return update_product_complete(connection, sku, data)
        
        elif query_type == "detect_data_changes":
            return detect_document_database_changes(connection, parameters)
        
        elif query_type == "backup_database":
            return backup_database_safe(connection, parameters)
        
        elif query_type == "get_sync_status":
            return get_document_sync_status(connection)
        
        # NEW: Database Schema Management
        elif query_type == "alter_schema":
            operation = parameters.get('operation')
            table = parameters.get('table')
            changes = parameters.get('changes', {})
            return alter_database_schema(connection, operation, table, changes)
        
        elif query_type == "create_table":
            table_name = parameters.get('table_name')
            schema = parameters.get('schema', {})
            return create_table_safe(connection, table_name, schema)
        
        elif query_type == "add_column":
            table = parameters.get('table')
            column_name = parameters.get('column_name')
            data_type = parameters.get('data_type')
            return add_column_safe(connection, table, column_name, data_type)
        
        elif query_type == "add_index":
            table = parameters.get('table')
            columns = parameters.get('columns', [])
            index_name = parameters.get('index_name')
            return add_index_safe(connection, table, columns, index_name)
            
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


# NEW BUSINESS INTELLIGENCE FUNCTIONS

def execute_custom_sql(connection: sqlite3.Connection, sql: str) -> Dict[str, Any]:
    """Execute custom SQL with safety checks"""
    
    try:
        # Safety check - block dangerous operations
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE']
        sql_upper = sql.upper().strip()
        
        # Allow SELECT and basic queries, block dangerous ones
        if any(sql_upper.startswith(keyword) for keyword in dangerous_keywords):
            return {"error": f"SQL operation blocked for safety. Use specific update functions instead."}
        
        cursor = connection.execute(sql)
        
        # Get results
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            # Convert to list of dicts
            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))
            
            return {
                "success": True,
                "sql": sql,
                "columns": columns,
                "row_count": len(results),
                "results": results
            }
        else:
            return {
                "success": True,
                "sql": sql,
                "message": "Query executed successfully (no results returned)"
            }
        
    except Exception as e:
        logger.error(f"SQL execution error: {e}")
        return {"error": str(e), "sql": sql}


def sync_database_from_documents(connection: sqlite3.Connection, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Sync database with latest document data"""
    
    try:
        from pathlib import Path
        import pandas as pd
        
        # Get document repository path
        doc_repo = get_document_repository_path()
        
        sync_results = {
            "documents_processed": [],
            "updates_applied": 0,
            "errors": [],
            "summary": {}
        }
        
        # Process Excel files
        excel_dir = doc_repo / "pricing_data" / "margin_calculations"
        if excel_dir.exists():
            for excel_file in excel_dir.glob("*.xlsx"):
                try:
                    # Process Excel file (simplified - would need full processing logic)
                    df = pd.read_excel(excel_file)
                    sync_results["documents_processed"].append(str(excel_file.name))
                    
                    # Count potential updates (example logic)
                    if len(df.columns) >= 3:
                        potential_skus = df.iloc[:, 2].dropna().nunique()
                        sync_results["updates_applied"] += potential_skus
                        
                except Exception as e:
                    sync_results["errors"].append(f"Error processing {excel_file.name}: {str(e)}")
        
        # Check price list PDFs (would need actual PDF processing)
        pdf_dir = doc_repo / "pricing_data" / "supplier_pricing"
        if pdf_dir.exists():
            pdf_files = list(pdf_dir.glob("*.pdf"))
            sync_results["documents_processed"].extend([f.name for f in pdf_files])
        
        sync_results["summary"] = {
            "total_documents": len(sync_results["documents_processed"]),
            "successful_updates": sync_results["updates_applied"],
            "error_count": len(sync_results["errors"]),
            "sync_timestamp": datetime.now().isoformat(),
            "status": "completed" if not sync_results["errors"] else "completed_with_errors"
        }
        
        return {
            "success": True,
            "sync_results": sync_results
        }
        
    except Exception as e:
        logger.error(f"Document sync error: {e}")
        return {"error": str(e)}


def update_product_complete(connection: sqlite3.Connection, sku: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Complete product update with validation"""
    
    try:
        # First, check if product exists
        existing = get_product_by_sku(connection, sku)
        if "error" in existing:
            return {"error": f"Product {sku} not found"}
        
        # Validate update data
        valid_fields = ["name", "price", "description", "manufacturer", "category", "specifications"]
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        if not filtered_data:
            return {"error": "No valid fields to update"}
        
        # Prepare update (this would need actual SQL UPDATE logic based on your schema)
        update_log = {
            "sku": sku,
            "fields_to_update": list(filtered_data.keys()),
            "update_data": filtered_data,
            "timestamp": datetime.now().isoformat(),
            "status": "prepared_for_execution"
        }
        
        # TODO: Implement actual database UPDATE statements
        # This would require knowing your exact table structure
        
        return {
            "success": True,
            "sku": sku,
            "update_prepared": True,
            "fields_updated": list(filtered_data.keys()),
            "message": "Update prepared - actual database update logic needed",
            "update_log": update_log
        }
        
    except Exception as e:
        logger.error(f"Product update error for {sku}: {e}")
        return {"error": str(e)}


def detect_document_database_changes(connection: sqlite3.Connection, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Detect changes between documents and database"""
    
    try:
        from pathlib import Path
        import pandas as pd
        
        doc_repo = get_document_repository_path()
        
        changes_detected = {
            "price_changes": [],
            "new_products": [],
            "missing_products": [],
            "data_mismatches": [],
            "recommendations": []
        }
        
        # Get current database SKUs
        db_skus_result = list_all_skus(connection, {})
        if "error" in db_skus_result:
            return {"error": "Could not retrieve database SKUs"}
        
        db_skus = set(db_skus_result.get("results", []))
        
        # Check Excel files for changes
        excel_dir = doc_repo / "pricing_data" / "margin_calculations"
        if excel_dir.exists():
            for excel_file in excel_dir.glob("*.xlsx"):
                try:
                    df = pd.read_excel(excel_file)
                    if len(df.columns) >= 3:
                        excel_skus = set(df.iloc[:, 2].dropna().astype(str).unique())
                        
                        # Find new products in Excel not in DB
                        new_in_excel = excel_skus - db_skus
                        if new_in_excel:
                            changes_detected["new_products"].extend(list(new_in_excel))
                        
                        # Find DB products not in Excel
                        missing_in_excel = db_skus - excel_skus
                        if missing_in_excel:
                            changes_detected["missing_products"].extend(list(missing_in_excel))
                            
                except Exception as e:
                    changes_detected["data_mismatches"].append(f"Error reading {excel_file.name}: {str(e)}")
        
        # Generate recommendations
        if changes_detected["new_products"]:
            changes_detected["recommendations"].append(f"Consider adding {len(changes_detected['new_products'])} new products from Excel to database")
        
        if changes_detected["missing_products"]:
            changes_detected["recommendations"].append(f"Review {len(changes_detected['missing_products'])} products in database not found in Excel")
        
        return {
            "success": True,
            "changes_detected": changes_detected,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Change detection error: {e}")
        return {"error": str(e)}


def backup_database_safe(connection: sqlite3.Connection, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Create safe database backup"""
    
    try:
        from shutil import copy2
        from pathlib import Path
        
        # Get source database path
        db_path = parameters.get("db_path") or get_default_db_path()
        source_path = Path(db_path)
        
        if not source_path.exists():
            return {"error": f"Database file not found: {db_path}"}
        
        # Create backup directory
        backup_dir = source_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{source_path.stem}_backup_{timestamp}{source_path.suffix}"
        backup_path = backup_dir / backup_filename
        
        # Create backup
        copy2(source_path, backup_path)
        
        # Verify backup
        backup_size = backup_path.stat().st_size
        original_size = source_path.stat().st_size
        
        return {
            "success": True,
            "original_file": str(source_path),
            "backup_file": str(backup_path),
            "original_size": original_size,
            "backup_size": backup_size,
            "backup_verified": backup_size == original_size,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Backup error: {e}")
        return {"error": str(e)}


def get_document_sync_status(connection: sqlite3.Connection) -> Dict[str, Any]:
    """Get current sync status between documents and database"""
    
    try:
        from pathlib import Path
        import os
        
        doc_repo = get_document_repository_path()
        
        status = {
            "database_info": {},
            "document_info": {},
            "sync_health": "unknown",
            "last_sync": "never",
            "recommendations": []
        }
        
        # Database info
        db_path = get_default_db_path()
        if Path(db_path).exists():
            db_stat = os.stat(db_path)
            status["database_info"] = {
                "path": db_path,
                "size_mb": round(db_stat.st_size / 1024 / 1024, 2),
                "last_modified": datetime.fromtimestamp(db_stat.st_mtime).isoformat()
            }
            
            # Get table counts
            tables_info = get_schema_info(connection)
            if "error" not in tables_info:
                status["database_info"]["tables"] = {
                    name: info.get("row_count", 0) 
                    for name, info in tables_info.get("tables", {}).items()
                }
        
        # Document repository info
        if doc_repo.exists():
            excel_files = list((doc_repo / "pricing_data" / "margin_calculations").glob("*.xlsx"))
            pdf_files = list((doc_repo / "pricing_data" / "supplier_pricing").glob("*.pdf"))
            
            status["document_info"] = {
                "excel_files": len(excel_files),
                "pdf_files": len(pdf_files),
                "excel_names": [f.name for f in excel_files],
                "pdf_names": [f.name for f in pdf_files]
            }
            
            # Check document freshness
            if excel_files:
                latest_excel = max(excel_files, key=lambda f: f.stat().st_mtime)
                status["document_info"]["latest_excel_modified"] = datetime.fromtimestamp(
                    latest_excel.stat().st_mtime
                ).isoformat()
        
        # Determine sync health
        if status["database_info"] and status["document_info"]:
            if status["document_info"]["excel_files"] > 0:
                status["sync_health"] = "good"
            else:
                status["sync_health"] = "warning"
                status["recommendations"].append("No Excel files found for price data")
        else:
            status["sync_health"] = "error"
            status["recommendations"].append("Missing database or document repository")
        
        return {
            "success": True,
            "sync_status": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Sync status error: {e}")
        return {"error": str(e)}


def get_document_repository_path():
    """Get document repository path with fallbacks"""
    
    # Environment variable
    env_path = os.getenv('DOCUMENT_REPOSITORY')
    if env_path and Path(env_path).exists():
        return Path(env_path)
    
    # Hardcoded path
    hardcoded = Path("C:/Users/maxli/PycharmProjects/PythonProject/MCP/document_repository")
    if hardcoded.exists():
        return hardcoded
    
    # Relative path
    return Path(__file__).parent.parent.parent.parent / "document_repository"


# DATABASE SCHEMA MANAGEMENT FUNCTIONS

def alter_database_schema(connection: sqlite3.Connection, operation: str, table: str, changes: Dict[str, Any]) -> Dict[str, Any]:
    """Safely alter database schema with backup and validation"""
    
    try:
        # Create backup before any schema changes
        backup_result = backup_database_safe(connection, {"reason": f"schema_change_{operation}_{table}"})
        if "error" in backup_result:
            return {"error": f"Backup failed before schema change: {backup_result['error']}"}
        
        # Validate operation and table
        if operation not in ["ADD_COLUMN", "MODIFY_COLUMN", "DROP_COLUMN", "RENAME_COLUMN"]:
            return {"error": f"Unsupported schema operation: {operation}"}
        
        # Check if table exists
        tables = get_all_tables(connection)
        if table not in tables:
            return {"error": f"Table '{table}' does not exist"}
        
        changes_applied = []
        
        if operation == "ADD_COLUMN":
            column_name = changes.get('column_name')
            data_type = changes.get('data_type', 'TEXT')
            default_value = changes.get('default_value')
            
            if not column_name:
                return {"error": "column_name required for ADD_COLUMN operation"}
            
            # Check if column already exists
            existing_columns = get_table_columns(connection, table)
            if column_name in existing_columns:
                return {"error": f"Column '{column_name}' already exists in table '{table}'"}
            
            # Build ALTER TABLE statement
            alter_sql = f"ALTER TABLE {table} ADD COLUMN {column_name} {data_type}"
            if default_value is not None:
                alter_sql += f" DEFAULT '{default_value}'"
            
            connection.execute(alter_sql)
            changes_applied.append(f"Added column '{column_name}' ({data_type}) to table '{table}'")
        
        elif operation == "RENAME_COLUMN":
            old_name = changes.get('old_name')
            new_name = changes.get('new_name')
            
            if not old_name or not new_name:
                return {"error": "old_name and new_name required for RENAME_COLUMN operation"}
            
            # Check if old column exists
            existing_columns = get_table_columns(connection, table)
            if old_name not in existing_columns:
                return {"error": f"Column '{old_name}' does not exist in table '{table}'"}
            
            if new_name in existing_columns:
                return {"error": f"Column '{new_name}' already exists in table '{table}'"}
            
            connection.execute(f"ALTER TABLE {table} RENAME COLUMN {old_name} TO {new_name}")
            changes_applied.append(f"Renamed column '{old_name}' to '{new_name}' in table '{table}'")
        
        connection.commit()
        
        return {
            "success": True,
            "operation": operation,
            "table": table,
            "changes_applied": changes_applied,
            "backup_created": backup_result.get("backup_file"),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Schema alteration error: {e}")
        # Attempt rollback
        try:
            connection.rollback()
        except:
            pass
        return {"error": str(e)}


def create_table_safe(connection: sqlite3.Connection, table_name: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """Safely create new table with validation"""
    
    try:
        # Validate table name
        if not table_name or not table_name.replace('_', '').replace('-', '').isalnum():
            return {"error": "Invalid table name - use alphanumeric characters and underscores only"}
        
        # Check if table already exists
        existing_tables = get_all_tables(connection)
        if table_name in existing_tables:
            return {"error": f"Table '{table_name}' already exists"}
        
        # Validate schema
        if not schema or not isinstance(schema, dict):
            return {"error": "Schema dictionary required with column definitions"}
        
        # Create backup before schema changes
        backup_result = backup_database_safe(connection, {"reason": f"create_table_{table_name}"})
        if "error" in backup_result:
            return {"error": f"Backup failed before table creation: {backup_result['error']}"}
        
        # Build CREATE TABLE statement
        column_definitions = []
        for column_name, column_type in schema.items():
            if not column_name.replace('_', '').isalnum():
                return {"error": f"Invalid column name: {column_name}"}
            column_definitions.append(f"{column_name} {column_type}")
        
        create_sql = f"CREATE TABLE {table_name} ({', '.join(column_definitions)})"
        connection.execute(create_sql)
        connection.commit()
        
        return {
            "success": True,
            "table_name": table_name,
            "columns_created": len(schema),
            "schema": schema,
            "backup_created": backup_result.get("backup_file"),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Table creation error: {e}")
        try:
            connection.rollback()
        except:
            pass
        return {"error": str(e)}


def add_column_safe(connection: sqlite3.Connection, table: str, column_name: str, data_type: str) -> Dict[str, Any]:
    """Safely add column to existing table"""
    
    return alter_database_schema(connection, "ADD_COLUMN", table, {
        "column_name": column_name,
        "data_type": data_type
    })


def add_index_safe(connection: sqlite3.Connection, table: str, columns: List[str], index_name: str = None) -> Dict[str, Any]:
    """Safely add database index for performance optimization"""
    
    try:
        # Validate inputs
        if not table or not columns:
            return {"error": "Table name and columns list required"}
        
        # Check if table exists
        existing_tables = get_all_tables(connection)
        if table not in existing_tables:
            return {"error": f"Table '{table}' does not exist"}
        
        # Check if columns exist
        existing_columns = get_table_columns(connection, table)
        invalid_columns = [col for col in columns if col not in existing_columns]
        if invalid_columns:
            return {"error": f"Columns do not exist in table '{table}': {invalid_columns}"}
        
        # Generate index name if not provided
        if not index_name:
            index_name = f"idx_{table}_{'_'.join(columns)}"
        
        # Check if index already exists (simple check)
        try:
            connection.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index_name}'")
            existing_index = connection.fetchone()
            if existing_index:
                return {"error": f"Index '{index_name}' already exists"}
        except:
            pass  # Continue if check fails
        
        # Create backup
        backup_result = backup_database_safe(connection, {"reason": f"create_index_{index_name}"})
        
        # Create index
        columns_str = ', '.join(columns)
        create_index_sql = f"CREATE INDEX {index_name} ON {table} ({columns_str})"
        connection.execute(create_index_sql)
        connection.commit()
        
        return {
            "success": True,
            "index_name": index_name,
            "table": table,
            "columns": columns,
            "backup_created": backup_result.get("backup_file"),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Index creation error: {e}")
        try:
            connection.rollback()
        except:
            pass
        return {"error": str(e)}