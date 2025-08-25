"""
Data Validator - Validates product data and bulk imports
"""

import re
import json
from typing import Dict, List, Any, Optional
import pandas as pd
from pathlib import Path
import magic
import chardet
from datetime import datetime
import logging

from ..config.settings import settings

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates WooCommerce product data"""
    
    def __init__(self):
        self.required_fields = ['name', 'type', 'status']
        self.valid_statuses = ['publish', 'draft', 'pending', 'private']
        self.valid_types = ['simple', 'grouped', 'external', 'variable']
        self.image_extensions = settings.validation.allowed_image_formats
        self.max_file_size = settings.validation.max_csv_size_mb * 1024 * 1024
    
    async def validate_product_updates(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Validate product update data"""
        errors = []
        warnings = []
        
        # Validate status
        if 'status' in updates and updates['status'] not in self.valid_statuses:
            errors.append(f"Invalid status: {updates['status']}")
        
        # Validate type
        if 'type' in updates and updates['type'] not in self.valid_types:
            errors.append(f"Invalid product type: {updates['type']}")
        
        # Validate price
        if 'regular_price' in updates:
            try:
                price = float(updates['regular_price'])
                if price < 0:
                    errors.append("Regular price cannot be negative")
            except (TypeError, ValueError):
                errors.append("Invalid regular price format")
        
        if 'sale_price' in updates:
            try:
                sale_price = float(updates['sale_price'])
                if sale_price < 0:
                    errors.append("Sale price cannot be negative")
                if 'regular_price' in updates:
                    regular_price = float(updates['regular_price'])
                    if sale_price > regular_price:
                        warnings.append("Sale price is higher than regular price")
            except (TypeError, ValueError):
                errors.append("Invalid sale price format")
        
        # Validate SKU
        if 'sku' in updates:
            sku = updates['sku']
            if not re.match(r'^[a-zA-Z0-9\-_]+$', sku):
                warnings.append("SKU contains special characters")
        
        # Validate stock quantity
        if 'stock_quantity' in updates:
            try:
                stock = int(updates['stock_quantity'])
                if stock < 0:
                    errors.append("Stock quantity cannot be negative")
            except (TypeError, ValueError):
                errors.append("Invalid stock quantity")
        
        # Validate images
        if 'images' in updates:
            for image in updates['images']:
                if 'src' in image:
                    if not self._is_valid_url(image['src']):
                        warnings.append(f"Invalid image URL: {image['src']}")
        
        # Validate categories
        if 'categories' in updates:
            if not isinstance(updates['categories'], list):
                errors.append("Categories must be a list")
        
        # Validate tags
        if 'tags' in updates:
            if not isinstance(updates['tags'], list):
                errors.append("Tags must be a list")
        
        # Check for HTML in text fields
        text_fields = ['name', 'description', 'short_description']
        for field in text_fields:
            if field in updates:
                if self._contains_malicious_html(updates[field]):
                    errors.append(f"Potentially malicious HTML in {field}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    async def validate_csv_data(self, df: pd.DataFrame, 
                               mapping_rules: Dict[str, str]) -> Dict[str, Any]:
        """Validate CSV data for import"""
        errors = []
        warnings = []
        
        # Apply mapping rules first
        if mapping_rules:
            df = df.rename(columns=mapping_rules)
        
        # Check required fields
        missing_fields = [field for field in self.required_fields if field not in df.columns]
        if missing_fields:
            errors.append(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Validate each row
        invalid_rows = []
        for index, row in df.iterrows():
            row_errors = []
            
            # Check required fields are not empty
            for field in self.required_fields:
                if field in df.columns and pd.isna(row.get(field)):
                    row_errors.append(f"Missing {field}")
            
            # Validate specific fields
            if 'status' in df.columns and pd.notna(row.get('status')):
                if row['status'] not in self.valid_statuses:
                    row_errors.append(f"Invalid status: {row['status']}")
            
            if 'type' in df.columns and pd.notna(row.get('type')):
                if row['type'] not in self.valid_types:
                    row_errors.append(f"Invalid type: {row['type']}")
            
            if 'regular_price' in df.columns and pd.notna(row.get('regular_price')):
                try:
                    price = float(row['regular_price'])
                    if price < 0:
                        row_errors.append("Negative price")
                except (TypeError, ValueError):
                    row_errors.append("Invalid price format")
            
            if row_errors:
                invalid_rows.append({
                    'row': index + 2,  # +2 for header and 0-index
                    'errors': row_errors
                })
        
        if len(invalid_rows) > 10:
            errors.append(f"Found {len(invalid_rows)} invalid rows. Showing first 10.")
            invalid_rows = invalid_rows[:10]
        
        if invalid_rows:
            errors.append(f"Invalid rows: {json.dumps(invalid_rows, indent=2)}")
        
        # Check for duplicates
        if 'sku' in df.columns:
            duplicate_skus = df[df.duplicated(subset=['sku'], keep=False)]['sku'].unique()
            if len(duplicate_skus) > 0:
                warnings.append(f"Duplicate SKUs found: {', '.join(duplicate_skus[:5])}")
        
        # Check data types
        numeric_fields = ['regular_price', 'sale_price', 'stock_quantity', 'weight', 'length', 'width', 'height']
        for field in numeric_fields:
            if field in df.columns:
                non_numeric = df[pd.notna(df[field]) & ~df[field].astype(str).str.match(r'^-?\d+\.?\d*$')]
                if len(non_numeric) > 0:
                    warnings.append(f"Non-numeric values in {field} column")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'total_rows': len(df),
            'valid_rows': len(df) - len(invalid_rows)
        }
    
    async def validate_file(self, file_path: str) -> Dict[str, Any]:
        """Validate file before processing"""
        errors = []
        warnings = []
        file_info = {}
        
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            errors.append("File does not exist")
            return {'valid': False, 'errors': errors}
        
        # Check file size
        file_size = path.stat().st_size
        file_info['size_bytes'] = file_size
        file_info['size_mb'] = file_size / (1024 * 1024)
        
        if file_size > self.max_file_size:
            errors.append(f"File too large: {file_info['size_mb']:.2f}MB (max: {settings.validation.max_csv_size_mb}MB)")
        
        # Check file extension
        extension = path.suffix.lower()
        file_info['extension'] = extension
        
        if extension not in settings.validation.allowed_file_extensions:
            errors.append(f"Invalid file extension: {extension}")
        
        # Detect file type
        if settings.validation.enable_virus_scan:
            try:
                file_type = magic.from_file(str(path), mime=True)
                file_info['mime_type'] = file_type
                
                # Basic virus scan (check for suspicious patterns)
                with open(path, 'rb') as f:
                    content = f.read(1024)  # Read first 1KB
                    if b'<script' in content or b'eval(' in content:
                        warnings.append("File contains potentially suspicious content")
            except Exception as e:
                warnings.append(f"Could not determine file type: {e}")
        
        # Detect encoding for text files
        if extension in ['.csv', '.txt']:
            try:
                with open(path, 'rb') as f:
                    raw_data = f.read(10000)  # Read first 10KB
                    result = chardet.detect(raw_data)
                    file_info['encoding'] = result['encoding']
                    file_info['encoding_confidence'] = result['confidence']
                    
                    if result['confidence'] < 0.8:
                        warnings.append(f"Low confidence in encoding detection: {result['confidence']:.2%}")
            except Exception as e:
                warnings.append(f"Could not detect encoding: {e}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'file_info': file_info
        }
    
    async def validate_bulk_operation(self, operation: str, 
                                     data: Any, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validate bulk operation before execution"""
        errors = []
        warnings = []
        
        # Validate operation type
        valid_operations = ['update', 'delete', 'create', 'duplicate']
        if operation not in valid_operations:
            errors.append(f"Invalid operation: {operation}")
        
        # Validate data structure
        if operation in ['update', 'create']:
            if not isinstance(data, (list, pd.DataFrame)):
                errors.append("Data must be a list or DataFrame")
        
        # Validate rules
        if rules:
            # Check for required rule fields based on operation
            if operation == 'update':
                if 'update_fields' not in rules:
                    warnings.append("No update fields specified")
            elif operation == 'delete':
                if 'confirm' not in rules or not rules['confirm']:
                    errors.append("Delete operation requires confirmation")
        
        # Check for data completeness
        if isinstance(data, pd.DataFrame):
            null_percentage = (data.isnull().sum() / len(data)) * 100
            high_null_columns = null_percentage[null_percentage > 50]
            if len(high_null_columns) > 0:
                warnings.append(f"Columns with >50% missing data: {', '.join(high_null_columns.index)}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
    
    def _contains_malicious_html(self, text: str) -> bool:
        """Check for potentially malicious HTML/JavaScript"""
        if not text:
            return False
        
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',  # Event handlers
            r'<iframe',
            r'<embed',
            r'<object',
            r'eval\s*\(',
            r'expression\s*\('
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                return True
        
        return False
    
    async def find_duplicates(self, df: pd.DataFrame, 
                             criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find duplicate products based on criteria"""
        duplicates = []
        
        # Default criteria
        if not criteria:
            criteria = {'columns': ['sku'], 'threshold': 1.0}
        
        columns = criteria.get('columns', ['sku'])
        threshold = criteria.get('threshold', 1.0)
        
        # Find exact duplicates
        if threshold == 1.0:
            duplicate_mask = df.duplicated(subset=columns, keep=False)
            duplicate_groups = df[duplicate_mask].groupby(columns)
            
            for name, group in duplicate_groups:
                duplicates.append({
                    'criteria': columns,
                    'value': name,
                    'count': len(group),
                    'rows': group.index.tolist()
                })
        else:
            # Fuzzy matching for similarity threshold < 1.0
            # This would require additional libraries like fuzzywuzzy
            pass
        
        return duplicates