# WordPress AI Content Management System

**Intelligent content analysis and automated optimization for conventum.kg**

## 🎯 Project Overview

This system provides AI-powered content management capabilities for WordPress websites, specifically designed for **conventum.kg**. It combines Model Context Protocol (MCP) servers with web-based interfaces to deliver intelligent content analysis and automated improvements.

## 🏗️ Architecture

### Core Components

1. **AI Content Analyzer** (`production/ai-content-system/content_analyzer.php`)
   - SEO score analysis (0-100 rating)
   - Content quality assessment
   - Technical analysis (Elementor detection)
   - Performance metrics

2. **AI Auto Improver** (`production/ai-content-system/auto_improver.php`)
   - Automated title optimization
   - Content structure enhancement
   - Meta description generation
   - Call-to-action insertion

3. **Content Showcase Manager** (`production/ai-content-system/showcase_manager.php`)
   - Content creation interface
   - Direct WordPress integration
   - SEO-optimized templates

### MCP Components

1. **Content Showcase Server** (`servers/content_showcase_server.py`)
   - MCP tools for content management
   - Database integration
   - AI-powered recommendations

2. **Web Inspector** (`web/mcp_inspector/`)
   - MCP server testing interface
   - Tool execution environment

3. **Monitoring Dashboard** (`web/monitoring_dashboard/`)
   - System health monitoring
   - Performance analytics

## 🚀 Features

### AI Content Analysis
- **SEO Scoring**: Comprehensive 0-100 SEO analysis
- **Readability Assessment**: Sentence structure and engagement metrics
- **Technical Analysis**: Elementor usage detection and optimization
- **Content Metrics**: Word count, title length, meta description analysis

### Automated Improvements
- **Title Optimization**: Power word insertion, length optimization
- **Content Enhancement**: Introduction addition, heading structure, CTAs
- **Meta Description**: Auto-generation of SEO-optimized summaries
- **Structure Improvement**: HTML formatting and readability enhancements

### WordPress Integration
- **Direct Database Access**: Real-time content modification
- **Admin Panel Integration**: Seamless workflow with existing WordPress setup
- **Elementor Compatibility**: Works with existing visual page builder
- **Non-Intrusive**: Enhances existing workflow without replacement

## 🛠️ Technology Stack

- **Backend**: Python 3.6+ (MCP servers), PHP 7.4+ (web interfaces)
- **Database**: MySQL/MariaDB (WordPress database)
- **Web Framework**: FastAPI (Python), Native PHP
- **Frontend**: Bootstrap 5, Chart.js for analytics
- **Protocol**: Model Context Protocol (MCP) for AI integration
- **Deployment**: FTP-compatible, shared hosting friendly

## 📁 Project Structure

```
MCP/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── launcher.py                        # MCP service launcher
├── config/
│   ├── production/
│   │   └── .env                       # Production configuration
│   └── templates/
├── servers/
│   ├── content_showcase_server.py     # Main MCP server
│   └── __init__.py
├── web/
│   ├── mcp_inspector/                 # MCP testing interface
│   ├── monitoring_dashboard/          # System monitoring
│   ├── static/                        # CSS, JS, images
│   └── templates/                     # HTML templates
├── production/
│   └── ai-content-system/             # Production PHP files
│       ├── content_analyzer.php       # AI content analysis
│       ├── auto_improver.php         # Automated improvements
│       ├── showcase_manager.php      # Content creation
│       └── wp_api_setup.php          # API configuration
├── docs/                             # Documentation
├── data/                             # Data files
└── logs/                             # Application logs
```

## 🌐 Deployment

### Production URLs (conventum.kg)

- **AI Content Analyzer**: https://conventum.kg/showcase/analyzer.php
- **Auto Improver**: https://conventum.kg/showcase/auto_improver.php
- **Content Manager**: https://conventum.kg/showcase/
- **MCP Inspector**: https://conventum.kg/mcp-installer/mcp-admin-suite/web/inspector/
- **Monitoring Dashboard**: https://conventum.kg/mcp-installer/mcp-admin-suite/web/dashboard/

### Deployment Process

1. **PHP Components** (Auto-deployed)
   ```bash
   # Files deployed to: /www/conventum.kg/showcase/
   - content_analyzer.php
   - auto_improver.php  
   - showcase_manager.php
   ```

2. **MCP Servers** (Manual start required)
   ```bash
   # SSH to server and run:
   cd /www/conventum.kg/mcp-installer/mcp-admin-suite/
   python3 launcher.py
   ```

## 🔧 Configuration

### Database Connection
```php
// WordPress database connection
DB_HOST: mysql
DB_USER: user133859_mastconv
DB_NAME: user133859_conv
```

### MCP Server Configuration
```python
# Content Showcase Server
PORT: 8083
PROTOCOL: MCP over stdio/SSE
DATABASE: MySQL via mysql-connector-python
```

## 📊 Usage

### 1. Content Analysis Workflow
1. Visit: https://conventum.kg/showcase/analyzer.php
2. View content overview and statistics
3. Click "Analyze" on any content piece
4. Review AI-generated recommendations
5. Implement suggestions manually or use auto-improvement

### 2. Automated Improvement Workflow  
1. From content analyzer, click "Auto-Improve"
2. Review proposed changes (title, content, meta)
3. Click "Apply AI Improvements Automatically"
4. Changes are saved directly to WordPress
5. Review in WordPress admin panel

### 3. Content Creation Workflow
1. Visit: https://conventum.kg/showcase/
2. Create new content using AI-optimized templates
3. Content appears in WordPress admin
4. Design layout using Elementor
5. Publish to live site

## 🔒 Security

- **Database Access**: Uses existing WordPress credentials
- **Application Passwords**: WordPress REST API integration ready
- **Input Validation**: All user inputs sanitized and validated
- **Access Control**: Admin-only interfaces
- **SSL/TLS**: HTTPS enforced for all production URLs

## 📈 Analytics & Monitoring

### Content Performance Metrics
- SEO scores and recommendations
- Content quality assessments  
- Elementor usage statistics
- Publishing frequency analysis

### System Health Monitoring
- MCP server status and uptime
- Database connection health
- Application performance metrics
- Error logging and alerting

## 🛠️ Development

### Local Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp config/production/.env.example .env

# Start MCP servers
python launcher.py

# Access local interfaces
http://localhost:8001  # MCP Inspector
http://localhost:8002  # Monitoring Dashboard
```

### Adding New MCP Tools
1. Extend `servers/content_showcase_server.py`
2. Add new tool definitions in `@server.list_tools()`
3. Implement tool logic in `@server.call_tool()`
4. Test via MCP Inspector interface

## 📝 API Reference

### MCP Tools Available

- `create_product_showcase`: Create new showcase content
- `update_showcase_content`: Update existing content
- `analyze_content_performance`: Performance analytics
- `optimize_content_seo`: SEO recommendations
- `manage_media_assets`: Media file management
- `get_elementor_insights`: Elementor analysis

### Database Schema
Integrates with standard WordPress database structure:
- `wp_posts`: Content storage
- `wp_postmeta`: Content metadata
- `wp_users`: User management
- `wp_options`: Configuration storage

## 🐛 Troubleshooting

### Common Issues

1. **MCP Server Won't Start**
   - Check Python version (3.6+ required)
   - Verify database connectivity
   - Review error logs

2. **Database Connection Failed**
   - Confirm credentials in config
   - Test MySQL host accessibility
   - Check firewall settings

3. **AI Improvements Not Applying**
   - Verify database write permissions
   - Check WordPress table structure
   - Review error logs

### Logs Location
- Application logs: `logs/mcp-admin.log`
- Error logs: `logs/error.log`
- WordPress logs: WordPress admin → Tools → Site Health

## 📞 Support

For technical issues or feature requests:
1. Check troubleshooting section above
2. Review application logs
3. Test individual components via MCP Inspector
4. Verify database connectivity and permissions

## 🎯 Future Enhancements

- **WordPress REST API Integration**: Full automation capabilities
- **Content Templates**: Pre-built showcase page templates  
- **A/B Testing**: Automated content variation testing
- **Advanced Analytics**: Traffic and conversion tracking
- **Multi-site Support**: Manage multiple WordPress installations

---

**Status**: Production Ready ✅  
**Last Updated**: August 2025  
**Version**: 1.0.0  
**Environment**: conventum.kg production