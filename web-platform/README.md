# WooCommerce Web Management Platform

Full-featured web application for managing multiple WooCommerce stores.

## Features

- 🛒 **Multi-Store Management** - Connect unlimited stores
- 📊 **Web Dashboard** - Modern browser-based interface  
- 📦 **Bulk Operations** - Mass update products, prices, inventory
- 📈 **Data Processing** - Import/export CSV and Excel files
- 🔄 **REST API** - Full API for automation
- 💾 **Persistent Storage** - Database-backed configuration
- 🔐 **Secure Credentials** - Encrypted API key storage

## Quick Start

```batch
# First time setup
setup_webapp.bat

# Start the web server
start_webapp.bat
```

Access the web interface at: http://localhost:8000

## Project Structure

```
web-platform/
├── main.py              # Application entry point
├── web_server.py        # FastAPI server
├── src/
│   ├── config/         # Configuration management
│   ├── gui/            # Desktop GUI (optional)
│   ├── store_management/ # Store operations
│   ├── data_processing/ # Import/export logic
│   ├── utils/          # Utilities
│   └── web/            # Web interfaces
└── data/               # Persistent data storage
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/api/stores` | GET | List all stores |
| `/api/stores` | POST | Add new store |
| `/api/stores/{id}` | DELETE | Remove store |
| `/api/products` | GET | List products |
| `/api/products/bulk` | POST | Bulk update |
| `/api/import` | POST | Import CSV/Excel |
| `/api/export` | GET | Export data |
| `/docs` | GET | API documentation |

## Adding a Store

1. Navigate to http://localhost:8000
2. Click "Add Store"
3. Enter store details:
   - Store Name
   - WooCommerce URL
   - Consumer Key
   - Consumer Secret
4. Click "Save"

## Configuration

Create `.env` file:
```env
# Server settings
PORT=8000
HOST=0.0.0.0

# Security
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key

# Database
DATABASE_URL=sqlite:///data/stores.db

# Logging
LOG_LEVEL=INFO
```

## Requirements

- Python 3.11+
- 2GB RAM minimum
- Modern web browser
- Windows 10/11

## Troubleshooting

### Port Already in Use
```batch
netstat -an | findstr :8000
taskkill /F /PID [process_id]
```

### Reset Database
```batch
del data\stores.db
start_webapp.bat
```

## Development

### Run in Debug Mode
```batch
set DEBUG=true
python main.py --mode server
```

### Add Custom Endpoints
Edit `web_server.py`:
```python
@app.get("/api/custom")
async def custom_endpoint():
    return {"message": "Custom"}
```

## Security Notes

- API keys are encrypted at rest
- Use HTTPS in production
- Regular backups recommended
- Never commit .env file

## Support

Check logs in `data/logs/` for debugging information.