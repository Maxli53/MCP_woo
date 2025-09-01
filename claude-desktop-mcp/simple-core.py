"""
Simple MCP Server - Direct Data Access for Claude Desktop
Focus: Give Claude direct access to business data, not complex processing pipelines
"""

import os
import json
import sqlite3
import pandas as pd
from mcp.server.fastmcp import FastMCP
from pathlib import Path

# Simple MCP Server focused on DATA ACCESS
mcp = FastMCP("Business Data Access")

# Database path
def get_db_path():
    return "C:/Users/maxli/PycharmProjects/PythonProject/MCP/document_repository/_temp/Snowmobile.db"

# Document repository path  
def get_doc_path():
    return Path("C:/Users/maxli/PycharmProjects/PythonProject/MCP/document_repository")

@mcp.tool()
def query_database(sql: str) -> str:
    """Execute SQL query directly on the business database
    
    Examples:
    - "SELECT * FROM articles WHERE brand = 'LYNX'"
    - "SELECT article_code, brand, model, price_fi FROM articles LIMIT 10"
    - "SELECT * FROM articles WHERE article_code = 'AARC'"
    """
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute(sql)
        
        # Get column names
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        # Get results
        results = cursor.fetchall()
        conn.close()
        
        # Convert to list of dicts for better readability
        data = []
        for row in results:
            data.append(dict(zip(columns, row)))
        
        return json.dumps({
            "success": True,
            "columns": columns,
            "rows": len(data),
            "data": data
        }, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def get_product(sku: str) -> str:
    """Get complete product information by SKU"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        # Get product data
        cursor.execute("SELECT * FROM articles WHERE article_code = ?", (sku,))
        row = cursor.fetchone()
        
        if not row:
            return json.dumps({"error": f"Product {sku} not found"})
        
        # Get column names
        cursor.execute("PRAGMA table_info(articles)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Create product dict
        product = dict(zip(columns, row))
        
        # Check for knowledge base mapping
        cursor.execute("SELECT kb_model_line FROM article_kb_mapping WHERE article_code = ?", (sku,))
        kb_result = cursor.fetchone()
        if kb_result:
            product['knowledge_base_model'] = kb_result[0]
        
        conn.close()
        
        return json.dumps({
            "success": True,
            "sku": sku,
            "product": product
        }, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def list_products(brand: str = None, limit: int = 50) -> str:
    """List products with optional brand filter"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        if brand:
            cursor.execute("SELECT article_code, brand, model, price_fi FROM articles WHERE brand = ? LIMIT ?", (brand, limit))
        else:
            cursor.execute("SELECT article_code, brand, model, price_fi FROM articles LIMIT ?", (limit,))
        
        columns = ['sku', 'brand', 'model', 'price']
        results = cursor.fetchall()
        conn.close()
        
        products = []
        for row in results:
            products.append(dict(zip(columns, row)))
        
        return json.dumps({
            "success": True,
            "count": len(products),
            "products": products
        }, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def read_excel(file_path: str, sheet: str = None) -> str:
    """Read Excel file directly"""
    try:
        # Handle relative paths
        if not file_path.startswith('/') and not file_path.startswith('C:'):
            file_path = get_doc_path() / "pricing_data" / "margin_calculations" / file_path
        
        df = pd.read_excel(file_path, sheet_name=sheet)
        
        # Convert to records for JSON
        data = df.head(20).to_dict('records')  # Limit to first 20 rows for preview
        
        return json.dumps({
            "success": True,
            "file": str(file_path),
            "sheet": sheet or "default",
            "columns": list(df.columns),
            "rows": len(df),
            "preview": data
        }, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def get_excel_data_for_sku(file_path: str, sku: str, sku_column: int = 2) -> str:
    """Get Excel data for specific SKU"""
    try:
        if not file_path.startswith('/') and not file_path.startswith('C:'):
            file_path = get_doc_path() / "pricing_data" / "margin_calculations" / file_path
        
        df = pd.read_excel(file_path)
        
        # Find row with matching SKU in specified column (default column 2 = index 2)
        sku_data = df[df.iloc[:, sku_column] == sku]
        
        if sku_data.empty:
            return json.dumps({"error": f"SKU {sku} not found in Excel"})
        
        # Convert to dict
        row_data = sku_data.iloc[0].to_dict()
        
        return json.dumps({
            "success": True,
            "sku": sku,
            "file": str(file_path),
            "data": row_data
        }, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def list_files(category: str = "all") -> str:
    """List available files in document repository"""
    try:
        doc_repo = get_doc_path()
        files = {}
        
        if category in ["all", "excel"]:
            excel_dir = doc_repo / "pricing_data" / "margin_calculations"
            if excel_dir.exists():
                files["excel"] = [f.name for f in excel_dir.glob("*.xlsx")]
        
        if category in ["all", "pdfs"]:
            pdf_dir = doc_repo / "pricing_data" / "supplier_pricing"
            if pdf_dir.exists():
                files["pdfs"] = [f.name for f in pdf_dir.glob("*.pdf")]
        
        return json.dumps({
            "success": True,
            "repository": str(doc_repo),
            "files": files
        }, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def get_database_info() -> str:
    """Get database structure and table information"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        table_info = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            
            table_info[table] = {
                "rows": count,
                "columns": columns
            }
        
        conn.close()
        
        return json.dumps({
            "success": True,
            "database": get_db_path(),
            "tables": table_info
        }, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    mcp.run()