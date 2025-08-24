# System Architecture

## Overview

The WordPress AI Content Management System is designed as a hybrid architecture combining Python MCP servers with PHP web interfaces for maximum compatibility and automated content optimization.

## Component Architecture

### 1. Production AI Content System (PHP)
```
/production/ai-content-system/
├── content_analyzer.php     # AI content analysis engine
├── auto_improver.php       # Automated content optimization
├── showcase_manager.php    # Content creation interface
└── wp_api_setup.php       # WordPress API configuration
```

**Purpose**: Direct WordPress integration for immediate AI-powered content management
**Technology**: Native PHP with direct database access
**Benefits**: 
- Works on any shared hosting
- No Python requirements for core functionality
- Direct WordPress database integration
- Immediate deployment via FTP

### 2. MCP Server Components (Python)
```
/servers/
├── content_showcase_server.py   # Main MCP server
└── __init__.py
```

**Purpose**: Advanced AI tools accessible via MCP protocol
**Technology**: Python with MCP SDK
**Benefits**:
- Protocol-standardized AI tools
- Extensible architecture
- Integration with external MCP clients

### 3. Web Management Interfaces (Python)
```
/web/
├── mcp_inspector/          # MCP server testing
├── monitoring_dashboard/   # System monitoring
├── static/                # CSS, JS, images
└── templates/             # HTML templates
```

**Purpose**: Development and monitoring interfaces
**Technology**: FastAPI with Jinja2 templates
**Benefits**:
- Real-time system monitoring
- MCP server debugging
- Performance analytics

## Data Flow Architecture

### Content Analysis Flow
```
WordPress Database
      ↓
PHP Content Analyzer
      ↓
AI Analysis Engine
      ↓
SEO Score + Recommendations
      ↓
Web Interface Display
```

### Automated Improvement Flow
```
User clicks "Auto-Improve"
      ↓
AI Improvement Engine
      ↓
Content Optimization
      ↓
Direct Database Update
      ↓
WordPress Reflects Changes
```

### MCP Integration Flow
```
MCP Client Request
      ↓
MCP Server (Python)
      ↓
Database Query/Update
      ↓
AI Processing
      ↓
Structured Response
```

## Database Integration

### WordPress Database Schema
```sql
-- Core WordPress tables used
wp_posts          # Content storage
wp_postmeta       # Content metadata
wp_users          # User management
wp_options        # Configuration

-- Content analysis queries
SELECT post_title, post_content, post_excerpt 
FROM wp_posts 
WHERE post_type IN ('post', 'page')

-- Elementor integration
SELECT meta_value 
FROM wp_postmeta 
WHERE meta_key = '_elementor_data'
```

### Connection Strategy
- **Production**: Direct MySQL connection via native PHP
- **Development**: MySQL via Python mysql-connector-python
- **Security**: Uses existing WordPress database credentials
- **Performance**: Connection pooling and query optimization

## AI Processing Architecture

### Content Analysis Engine
```python
def analyzeSEO($title, $content, $excerpt):
    analysis = []
    score = 100
    
    # Title analysis (length, keywords)
    # Content analysis (word count, structure)
    # Meta analysis (description, length)
    # Readability scoring
    
    return {
        'score': score,
        'recommendations': analysis
    }
```

### Automated Improvement Engine
```python
class AIContentImprover:
    def improveContent(self, post_id):
        # Analyze current content
        # Generate optimizations
        # Apply improvements
        # Return results
```

## Security Architecture

### Access Control
- **Admin-only interfaces**: No customer-facing AI features
- **Database security**: Limited to WordPress database permissions
- **Input validation**: All user inputs sanitized
- **SSL/TLS**: HTTPS enforced for all production URLs

### Authentication Strategy
```
WordPress Admin
      ↓
AI Content System
      ↓
Database Access
```

## Performance Architecture

### Caching Strategy
- **Database queries**: Result caching for common analysis
- **Static assets**: Browser caching for CSS/JS
- **Content analysis**: Memoization of analysis results

### Optimization Techniques
- **Lazy loading**: Content loaded on-demand
- **Batch processing**: Multiple content pieces analyzed together
- **Database optimization**: Indexed queries and connection pooling

## Deployment Architecture

### Production Deployment (conventum.kg)
```
Domain: conventum.kg
├── /showcase/              # AI Content System (PHP)
│   ├── analyzer.php
│   ├── auto_improver.php
│   └── index.php
└── /mcp-installer/         # MCP Components (Python)
    └── mcp-admin-suite/
        ├── launcher.py
        ├── servers/
        └── web/
```

### Development Deployment
```
Local Environment
├── Python MCP servers (localhost:8001-8083)
├── PHP development server
└── MySQL/MariaDB instance
```

## Integration Points

### WordPress Integration
- **Direct database access**: Real-time content modification
- **Admin panel links**: Seamless workflow integration
- **Elementor compatibility**: Design system preservation
- **REST API ready**: Future automation capabilities

### External Systems
- **MCP Protocol**: Standard AI tool integration
- **Chart.js**: Analytics visualization
- **Bootstrap 5**: Responsive UI framework
- **MySQL**: WordPress database compatibility

## Scalability Considerations

### Horizontal Scaling
- **Stateless design**: No server-side sessions
- **Database connection pooling**: Efficient resource usage
- **Load balancer ready**: Multi-server deployment capable

### Vertical Scaling
- **Memory optimization**: Efficient content processing
- **CPU utilization**: Parallel analysis processing
- **Database optimization**: Query performance tuning

## Monitoring & Observability

### Metrics Collection
- **Content analysis performance**: Processing time tracking
- **Database query performance**: Query execution monitoring
- **User interaction tracking**: Feature usage analytics
- **Error rate monitoring**: System health tracking

### Logging Strategy
```
Application Logs: logs/mcp-admin.log
Error Logs: logs/error.log
WordPress Logs: WordPress admin interface
Access Logs: Web server logs
```

## Future Architecture Enhancements

### Planned Improvements
- **Microservices architecture**: Service isolation
- **Event-driven processing**: Asynchronous content updates
- **Advanced caching**: Redis integration
- **Multi-tenant support**: Multiple WordPress installations

### Integration Roadmap
- **REST API layer**: Full automation capabilities
- **Webhook support**: Real-time event processing
- **Analytics integration**: Traffic and conversion tracking
- **Machine learning pipeline**: Advanced AI capabilities