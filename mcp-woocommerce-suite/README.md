# MCP WooCommerce Suite

A comprehensive Model Context Protocol (MCP) solution for professional WooCommerce store management. This suite provides a modern GUI application with LocalTunnel integration for managing multiple WooCommerce stores from a single interface.

## 🚀 Features

### Core Components
- **MCP Server (Port 8083)**: Admin tools for WooCommerce management via MCP protocol
- **MCP Inspector (Port 8001)**: Web interface for testing and debugging MCP tools
- **Monitoring Dashboard (Port 8002)**: Real-time system metrics and analytics
- **Professional GUI**: Modern desktop application with system tray integration

### Store Management
- Connect and manage multiple WooCommerce stores
- Secure credential storage with encryption
- Real-time store health monitoring
- Automatic synchronization capabilities

### Product Management
- **Single Store Operations**:
  - List, search, and filter products
  - Update product details
  - Bulk delete operations
  - Product duplication
  - Performance analytics

- **Cross-Store Operations**:
  - Compare products across stores
  - Synchronize product data
  - Find missing products
  - Bulk copy between stores
  - Standardize product information
  - Inventory synchronization

### Bulk Data Operations
- Import products from CSV/Excel files
- Export products to multiple formats
- Data validation before import
- Preview import results
- Bulk updates from files
- Generate import templates

### Advanced Features
- **Store Cloning**: Complete store duplication
- **Batch Operations**: Price, category, image, and SEO updates
- **Data Validation**: Find duplicates, audit completeness
- **Scheduled Operations**: Automate bulk tasks
- **Backup System**: Automatic backups before major operations

### LocalTunnel Integration
- Automatic LocalTunnel setup with custom subdomains
- Fallback to ngrok if configured
- Public URLs for remote access
- Health monitoring and auto-restart
- Connection status in GUI

## 📋 Requirements

- Windows 10/11
- Python 3.8+
- Node.js 14+ (for LocalTunnel)
- 4GB RAM minimum
- 500MB disk space

## 🔧 Installation

### Quick Install

1. Clone or download this repository
2. Run the installation script:
```batch
install.bat
```

3. Configure your settings:
   - Copy `.env.example` to `.env`
   - Edit `.env` with your configuration

4. Start the application:
```batch
start.bat
```

### Manual Installation

1. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install LocalTunnel (optional):
```bash
npm install -g localtunnel
```

4. Configure environment:
```bash
copy .env.example .env
# Edit .env with your settings
```

5. Run the application:
```bash
python main.py
```

## 🖥️ Usage

### GUI Application

The main interface provides:
- **Dashboard**: Quick statistics and recent activity
- **Stores**: Manage WooCommerce connections
- **Products**: Browse and manage products
- **Operations**: Bulk operations and tools
- **Logs**: View application logs
- **Settings**: Configure application preferences

### Adding a Store

1. Click "Add Store" in the Stores tab
2. Enter store details:
   - Store ID (unique identifier)
   - WooCommerce URL
   - Consumer Key (from WooCommerce API)
   - Consumer Secret
3. Test connection
4. Save store configuration

### Importing Products

1. Select target store
2. Click "Import CSV" or "Import Excel"
3. Choose file and configure mapping
4. Preview import results
5. Confirm import

### Exporting Products

1. Select source store
2. Click "Export Excel"
3. Choose fields to export
4. Configure formatting options
5. Save file

### Using LocalTunnel

1. Click "Connect Tunnel" in toolbar
2. Wait for connection (URLs appear in status panel)
3. Share public URLs for remote access
4. URLs format: `https://[subdomain]-[service].loca.lt`

## 🔐 Security

- Credentials encrypted with Fernet encryption
- JWT authentication for API access
- Optional 2FA support
- API key management
- Secure credential storage
- Input validation and sanitization

## 📁 Project Structure

```
mcp-woocommerce-suite/
├── src/
│   ├── mcp_server/         # MCP server implementation
│   ├── gui/                # GUI application
│   ├── web/                # Web interfaces
│   │   ├── inspector/      # MCP Inspector
│   │   └── dashboard/      # Monitoring Dashboard
│   ├── utils/              # Utility modules
│   └── config/             # Configuration
├── data/                   # Application data
│   ├── stores/            # Store configurations
│   ├── logs/              # Application logs
│   └── backups/           # Backup files
├── resources/             # Icons and templates
├── main.py                # Main entry point
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── install.bat           # Installation script
└── start.bat            # Startup script
```

## 🛠️ Configuration

### Environment Variables (.env)

```env
# Environment
ENVIRONMENT=production
DEBUG=False

# LocalTunnel
TUNNEL_ENABLED=true
TUNNEL_SUBDOMAIN=my-woocommerce
NGROK_AUTH_TOKEN=your_token_here

# Database
DB_TYPE=sqlite

# Monitoring
LOG_LEVEL=INFO
ENABLE_SENTRY=false

# Notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

### GUI Settings

- Theme: Dark/Light/Auto
- Start minimized option
- System tray integration
- Auto-start on boot
- Notification preferences

## 🚀 Advanced Usage

### Running Specific Components

```bash
# GUI only
python main.py --mode gui

# MCP Server only
python main.py --mode server

# Inspector only
python main.py --mode inspector

# Dashboard only
python main.py --mode dashboard

# Headless mode (all services, no GUI)
python main.py --headless
```

### Scheduled Operations

Configure automated tasks:
1. Go to Operations tab
2. Select operation type
3. Configure schedule
4. Enable automation

### Backup Management

- Automatic backups before major operations
- Manual backup creation
- Restore from backup
- Backup compression and encryption

## 🐛 Troubleshooting

### Common Issues

**Port Already in Use**
- The application will attempt to kill existing processes
- Manually check ports: 8001, 8002, 8083

**LocalTunnel Connection Failed**
- Ensure Node.js is installed
- Check firewall settings
- Try fallback to ngrok

**Store Connection Failed**
- Verify WooCommerce REST API is enabled
- Check API credentials
- Ensure proper permissions

### Logs Location

- Application logs: `data/logs/`
- Service logs: `data/logs/[service_name]/`
- Error logs: `data/logs/error.log`

## 📊 Performance

### System Requirements

- **Minimum**: 2 CPU cores, 4GB RAM
- **Recommended**: 4 CPU cores, 8GB RAM
- **Network**: Stable internet for tunnel features

### Optimization Tips

- Limit concurrent operations
- Use batch operations for large datasets
- Enable caching for frequently accessed data
- Schedule heavy operations during off-peak hours

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to branch
5. Open a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
- Check the documentation in `/docs`
- Review existing issues
- Create a new issue with details

## 🎯 Roadmap

- [ ] Linux/macOS support
- [ ] Cloud backup integration
- [ ] Advanced analytics dashboard
- [ ] Mobile companion app
- [ ] API rate limiting
- [ ] Multi-language support
- [ ] Plugin system
- [ ] Docker containerization

## 🙏 Acknowledgments

- WooCommerce for the excellent e-commerce platform
- LocalTunnel for tunnel services
- The MCP protocol developers
- Open source community

---

**MCP WooCommerce Suite** - Professional WooCommerce Management Made Easy