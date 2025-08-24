#!/usr/bin/env python3
"""
Content Showcase MCP Server for conventum.kg
AI-powered product/service showcase content management
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
import mysql.connector
from mysql.connector import Error
import logging
from datetime import datetime, timedelta

# Database configuration
DB_CONFIG = {
    'host': 'mysql',
    'user': 'user133859_mastconv',
    'password': 'dsavdsEv616515s',
    'database': 'user133859_conv'
}

class ContentShowcaseServer:
    def __init__(self):
        self.db = None
        self.setup_logging()
    
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def get_db_connection(self):
        """Get database connection"""
        try:
            if not self.db or not self.db.is_connected():
                self.db = mysql.connector.connect(**DB_CONFIG)
            return self.db
        except Error as e:
            self.logger.error(f"Database connection failed: {e}")
            return None
    
    def execute_query(self, query: str, params: tuple = None, fetch: str = 'all'):
        """Execute database query safely"""
        try:
            db = self.get_db_connection()
            if not db:
                return None
            
            cursor = db.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch == 'one':
                result = cursor.fetchone()
            elif fetch == 'all':
                result = cursor.fetchall()
            else:
                db.commit()
                result = cursor.rowcount
            
            cursor.close()
            return result
        except Error as e:
            self.logger.error(f"Query execution failed: {e}")
            return None

# Initialize server
server = Server("content-showcase-server")
showcase = ContentShowcaseServer()

@server.list_resources()
async def handle_list_resources() -> List[Resource]:
    """List available content showcase resources"""
    return [
        Resource(
            uri="showcase://products",
            name="Product Showcase Items",
            description="All product/service showcase content",
            mimeType="application/json"
        ),
        Resource(
            uri="showcase://pages",
            name="Content Pages",
            description="WordPress pages and posts for showcase",
            mimeType="application/json"
        ),
        Resource(
            uri="showcase://media",
            name="Media Assets",
            description="Images and media files for products",
            mimeType="application/json"
        ),
        Resource(
            uri="showcase://analytics",
            name="Content Performance",
            description="Analytics for showcase content",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read showcase content resources"""
    if uri == "showcase://products":
        # Get all published posts and pages that could be products
        query = """
        SELECT p.ID, p.post_title, p.post_content, p.post_excerpt, 
               p.post_date, p.post_modified, p.post_type, p.post_status,
               (SELECT meta_value FROM wp_postmeta WHERE post_id = p.ID AND meta_key = '_thumbnail_id' LIMIT 1) as thumbnail_id
        FROM wp_posts p
        WHERE p.post_status = 'publish' 
        AND p.post_type IN ('post', 'page')
        ORDER BY p.post_modified DESC
        """
        results = showcase.execute_query(query)
        return json.dumps(results or [], indent=2)
    
    elif uri == "showcase://pages":
        # Get page structure and hierarchy
        query = """
        SELECT p.ID, p.post_title, p.post_content, p.post_type, 
               p.post_status, p.post_date, p.post_modified,
               pm.meta_value as page_template
        FROM wp_posts p
        LEFT JOIN wp_postmeta pm ON p.ID = pm.post_id AND pm.meta_key = '_wp_page_template'
        WHERE p.post_type IN ('post', 'page') 
        AND p.post_status = 'publish'
        ORDER BY p.post_type, p.post_title
        """
        results = showcase.execute_query(query)
        return json.dumps(results or [], indent=2)
    
    elif uri == "showcase://media":
        # Get all media files with metadata
        query = """
        SELECT p.ID, p.post_title, p.post_content, p.post_excerpt,
               p.guid as file_url, p.post_date,
               pm1.meta_value as file_path,
               pm2.meta_value as metadata
        FROM wp_posts p
        LEFT JOIN wp_postmeta pm1 ON p.ID = pm1.post_id AND pm1.meta_key = '_wp_attached_file'
        LEFT JOIN wp_postmeta pm2 ON p.ID = pm2.post_id AND pm2.meta_key = '_wp_attachment_metadata'
        WHERE p.post_type = 'attachment'
        ORDER BY p.post_date DESC
        LIMIT 50
        """
        results = showcase.execute_query(query)
        return json.dumps(results or [], indent=2)
    
    elif uri == "showcase://analytics":
        # Get content performance metrics
        analytics = {}
        
        # Post counts by type and status
        query = """
        SELECT post_type, post_status, COUNT(*) as count
        FROM wp_posts
        GROUP BY post_type, post_status
        ORDER BY count DESC
        """
        analytics['content_stats'] = showcase.execute_query(query) or []
        
        # Recent activity
        query = """
        SELECT post_title, post_type, post_modified
        FROM wp_posts
        WHERE post_status = 'publish'
        ORDER BY post_modified DESC
        LIMIT 10
        """
        analytics['recent_activity'] = showcase.execute_query(query) or []
        
        # Elementor usage
        query = """
        SELECT COUNT(DISTINCT post_id) as elementor_pages
        FROM wp_postmeta
        WHERE meta_key = '_elementor_edit_mode'
        """
        elementor_data = showcase.execute_query(query, fetch='one')
        analytics['elementor_pages'] = elementor_data['elementor_pages'] if elementor_data else 0
        
        return json.dumps(analytics, indent=2)
    
    else:
        raise ValueError(f"Unknown resource: {uri}")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available content management tools"""
    return [
        Tool(
            name="create_product_showcase",
            description="Create a new product/service showcase page",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Product/service title"},
                    "description": {"type": "string", "description": "Detailed description"},
                    "excerpt": {"type": "string", "description": "Short summary"},
                    "content_type": {"type": "string", "enum": ["post", "page"], "default": "page"},
                    "status": {"type": "string", "enum": ["draft", "publish"], "default": "draft"}
                },
                "required": ["title", "description"]
            }
        ),
        Tool(
            name="update_showcase_content",
            description="Update existing showcase page content",
            inputSchema={
                "type": "object",
                "properties": {
                    "post_id": {"type": "integer", "description": "WordPress post ID"},
                    "title": {"type": "string", "description": "Updated title"},
                    "content": {"type": "string", "description": "Updated content"},
                    "excerpt": {"type": "string", "description": "Updated excerpt"}
                },
                "required": ["post_id"]
            }
        ),
        Tool(
            name="analyze_content_performance",
            description="Analyze performance of showcase content",
            inputSchema={
                "type": "object",
                "properties": {
                    "period_days": {"type": "integer", "default": 30, "description": "Analysis period in days"}
                }
            }
        ),
        Tool(
            name="optimize_content_seo",
            description="Analyze and suggest SEO improvements for content",
            inputSchema={
                "type": "object",
                "properties": {
                    "post_id": {"type": "integer", "description": "WordPress post ID to analyze"}
                },
                "required": ["post_id"]
            }
        ),
        Tool(
            name="manage_media_assets",
            description="Manage media files for product showcase",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["list", "analyze", "optimize"]},
                    "media_type": {"type": "string", "enum": ["image", "video", "document", "all"], "default": "all"}
                },
                "required": ["action"]
            }
        ),
        Tool(
            name="get_elementor_insights",
            description="Analyze Elementor page structure and suggest improvements",
            inputSchema={
                "type": "object",
                "properties": {
                    "post_id": {"type": "integer", "description": "Page ID to analyze"},
                    "analysis_type": {"type": "string", "enum": ["structure", "performance", "design"], "default": "structure"}
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls for content showcase management"""
    
    if name == "create_product_showcase":
        title = arguments["title"]
        description = arguments["description"]
        excerpt = arguments.get("excerpt", "")
        content_type = arguments.get("content_type", "page")
        status = arguments.get("status", "draft")
        
        # Create new WordPress post/page
        query = """
        INSERT INTO wp_posts (post_title, post_content, post_excerpt, post_type, 
                             post_status, post_date, post_modified, post_author)
        VALUES (%s, %s, %s, %s, %s, NOW(), NOW(), 1)
        """
        params = (title, description, excerpt, content_type, status)
        result = showcase.execute_query(query, params, fetch='none')
        
        if result:
            return [TextContent(
                type="text",
                text=f"Successfully created {content_type} '{title}' with status '{status}'. "
                     f"You can now edit it in WordPress admin or use Elementor to design the layout."
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Failed to create {content_type}. Please check database connection."
            )]
    
    elif name == "update_showcase_content":
        post_id = arguments["post_id"]
        updates = []
        params = []
        
        if "title" in arguments:
            updates.append("post_title = %s")
            params.append(arguments["title"])
        
        if "content" in arguments:
            updates.append("post_content = %s")
            params.append(arguments["content"])
        
        if "excerpt" in arguments:
            updates.append("post_excerpt = %s")
            params.append(arguments["excerpt"])
        
        if updates:
            updates.append("post_modified = NOW()")
            params.append(post_id)
            
            query = f"UPDATE wp_posts SET {', '.join(updates)} WHERE ID = %s"
            result = showcase.execute_query(query, tuple(params), fetch='none')
            
            if result:
                return [TextContent(
                    type="text",
                    text=f"Successfully updated content for post ID {post_id}"
                )]
        
        return [TextContent(
            type="text",
            text=f"No updates made to post ID {post_id}"
        )]
    
    elif name == "analyze_content_performance":
        period_days = arguments.get("period_days", 30)
        
        # Get content statistics
        query = """
        SELECT 
            COUNT(*) as total_published,
            COUNT(CASE WHEN post_date >= DATE_SUB(NOW(), INTERVAL %s DAY) THEN 1 END) as recent_posts,
            COUNT(CASE WHEN post_modified >= DATE_SUB(NOW(), INTERVAL %s DAY) THEN 1 END) as recently_updated
        FROM wp_posts
        WHERE post_status = 'publish' AND post_type IN ('post', 'page')
        """
        stats = showcase.execute_query(query, (period_days, period_days), fetch='one')
        
        # Get most active content types
        query = """
        SELECT post_type, COUNT(*) as count
        FROM wp_posts
        WHERE post_status = 'publish' 
        AND post_date >= DATE_SUB(NOW(), INTERVAL %s DAY)
        GROUP BY post_type
        ORDER BY count DESC
        """
        activity = showcase.execute_query(query, (period_days,))
        
        analysis = f"""Content Performance Analysis ({period_days} days):

📊 Overview:
- Total published content: {stats['total_published'] if stats else 0}
- New content created: {stats['recent_posts'] if stats else 0}
- Content updated: {stats['recently_updated'] if stats else 0}

📈 Content Activity:
"""
        if activity:
            for item in activity:
                analysis += f"- {item['post_type']}: {item['count']} items\n"
        else:
            analysis += "- No recent activity found\n"
        
        return [TextContent(type="text", text=analysis)]
    
    elif name == "optimize_content_seo":
        post_id = arguments["post_id"]
        
        # Get post content for analysis
        query = """
        SELECT post_title, post_content, post_excerpt
        FROM wp_posts
        WHERE ID = %s
        """
        post = showcase.execute_query(query, (post_id,), fetch='one')
        
        if not post:
            return [TextContent(
                type="text",
                text=f"Post ID {post_id} not found"
            )]
        
        # Basic SEO analysis
        title = post['post_title'] or ""
        content = post['post_content'] or ""
        excerpt = post['post_excerpt'] or ""
        
        suggestions = []
        
        # Title analysis
        if len(title) < 30:
            suggestions.append("📝 Title is too short - aim for 30-60 characters")
        elif len(title) > 60:
            suggestions.append("📝 Title is too long - keep under 60 characters")
        
        # Content analysis
        if len(content) < 300:
            suggestions.append("📄 Content is quite short - consider adding more detailed information")
        
        # Excerpt analysis
        if not excerpt:
            suggestions.append("📋 Add a meta description (excerpt) for better SEO")
        elif len(excerpt) > 160:
            suggestions.append("📋 Excerpt is too long - keep under 160 characters")
        
        if not suggestions:
            suggestions.append("✅ Basic SEO structure looks good!")
        
        seo_report = f"""SEO Analysis for Post ID {post_id}:

Title: "{title}"
Content length: {len(content)} characters
Excerpt length: {len(excerpt)} characters

Recommendations:
""" + "\n".join(f"- {s}" for s in suggestions)
        
        return [TextContent(type="text", text=seo_report)]
    
    elif name == "manage_media_assets":
        action = arguments["action"]
        media_type = arguments.get("media_type", "all")
        
        if action == "list":
            query = """
            SELECT p.ID, p.post_title, p.guid as file_url, p.post_date,
                   pm.meta_value as file_path
            FROM wp_posts p
            LEFT JOIN wp_postmeta pm ON p.ID = pm.post_id AND pm.meta_key = '_wp_attached_file'
            WHERE p.post_type = 'attachment'
            ORDER BY p.post_date DESC
            LIMIT 20
            """
            media = showcase.execute_query(query)
            
            if media:
                media_list = "📁 Recent Media Files:\n\n"
                for item in media:
                    media_list += f"- ID: {item['ID']} | {item['post_title'] or 'Untitled'}\n"
                    media_list += f"  File: {item['file_path'] or 'Unknown'}\n"
                    media_list += f"  Date: {item['post_date']}\n\n"
            else:
                media_list = "No media files found"
            
            return [TextContent(type="text", text=media_list)]
        
        elif action == "analyze":
            # Get media statistics
            query = """
            SELECT 
                COUNT(*) as total_files,
                COUNT(CASE WHEN post_date >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 END) as recent_files
            FROM wp_posts
            WHERE post_type = 'attachment'
            """
            stats = showcase.execute_query(query, fetch='one')
            
            analysis = f"""📊 Media Asset Analysis:

Total files: {stats['total_files'] if stats else 0}
Recent uploads (30 days): {stats['recent_files'] if stats else 0}

💡 Recommendations:
- Optimize images before upload to improve site speed
- Use descriptive filenames for better SEO
- Consider adding alt text for accessibility
- Regularly clean up unused media files
"""
            return [TextContent(type="text", text=analysis)]
    
    elif name == "get_elementor_insights":
        post_id = arguments.get("post_id")
        analysis_type = arguments.get("analysis_type", "structure")
        
        if post_id:
            # Get Elementor data for specific page
            query = """
            SELECT meta_value as elementor_data
            FROM wp_postmeta
            WHERE post_id = %s AND meta_key = '_elementor_data'
            """
            elementor_data = showcase.execute_query(query, (post_id,), fetch='one')
            
            if elementor_data and elementor_data['elementor_data']:
                try:
                    data = json.loads(elementor_data['elementor_data'])
                    element_count = len(data) if isinstance(data, list) else 0
                    
                    insight = f"""🎨 Elementor Analysis for Post ID {post_id}:

Structure Overview:
- Total elements: {element_count}
- Page built with Elementor: ✅

💡 Insights:
- This page uses Elementor's visual builder
- You can edit the layout directly in Elementor
- Consider optimizing for mobile responsiveness
- Check loading speed with many elements
"""
                except json.JSONDecodeError:
                    insight = f"Elementor data found for post {post_id} but couldn't parse structure"
                
                return [TextContent(type="text", text=insight)]
            else:
                return [TextContent(
                    type="text", 
                    text=f"Post ID {post_id} doesn't appear to use Elementor"
                )]
        else:
            # General Elementor overview
            query = """
            SELECT COUNT(DISTINCT post_id) as elementor_pages
            FROM wp_postmeta
            WHERE meta_key = '_elementor_edit_mode'
            """
            stats = showcase.execute_query(query, fetch='one')
            
            overview = f"""🎨 Elementor Usage Overview:

Total Elementor pages: {stats['elementor_pages'] if stats else 0}

💡 General Insights:
- Elementor is your main page builder
- Great for visual content creation
- Perfect for product showcase pages
- Consider creating templates for consistency
"""
            return [TextContent(type="text", text=overview)]
    
    return [TextContent(
        type="text",
        text=f"Tool {name} not implemented yet"
    )]

async def main():
    """Main server entry point"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="content-showcase-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())