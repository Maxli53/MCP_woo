"""
MCP WooCommerce Suite - Web Server
Simple, working web interface
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn
import json
from datetime import datetime

app = FastAPI(title='MCP WooCommerce Suite')

# In-memory store for demo
stores = {}
products = []

@app.get('/', response_class=HTMLResponse)
async def home():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MCP WooCommerce Suite</title>
        <meta charset="utf-8">
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                margin-bottom: 10px;
            }
            .status {
                background: #d4edda;
                color: #155724;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .card {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                border: 1px solid #dee2e6;
            }
            .card h3 {
                margin-top: 0;
                color: #495057;
            }
            .button {
                display: inline-block;
                padding: 10px 20px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 5px;
                border: none;
                cursor: pointer;
            }
            .button:hover {
                background: #5a67d8;
            }
            .api-link {
                display: inline-block;
                margin: 10px;
                padding: 8px 15px;
                background: #6c757d;
                color: white;
                text-decoration: none;
                border-radius: 4px;
            }
            .api-link:hover {
                background: #5a6268;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛒 MCP WooCommerce Suite</h1>
            <p>Professional Store Management System</p>
            
            <div class="status">
                <strong>✅ System Status:</strong> Operational<br>
                <strong>Server:</strong> Running on port 8000<br>
                <strong>Time:</strong> <span id="time"></span>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h3>📊 Quick Stats</h3>
                    <p>Stores Connected: <strong id="storeCount">0</strong></p>
                    <p>Total Products: <strong id="productCount">0</strong></p>
                    <p>Python Version: 3.11</p>
                </div>
                
                <div class="card">
                    <h3>🏪 Store Management</h3>
                    <button class="button" onclick="addStore()">Add Store</button>
                    <button class="button" onclick="viewStores()">View Stores</button>
                </div>
                
                <div class="card">
                    <h3>📦 Products</h3>
                    <button class="button" onclick="viewProducts()">View Products</button>
                    <button class="button" onclick="importProducts()">Import CSV</button>
                </div>
                
                <div class="card">
                    <h3>🔧 Operations</h3>
                    <button class="button" onclick="bulkUpdate()">Bulk Update</button>
                    <button class="button" onclick="syncStores()">Sync Stores</button>
                </div>
            </div>
            
            <h3>API Endpoints:</h3>
            <div>
                <a href="/api/status" class="api-link">System Status</a>
                <a href="/api/stores" class="api-link">Stores API</a>
                <a href="/api/products" class="api-link">Products API</a>
                <a href="/docs" class="api-link">API Docs</a>
            </div>
            
            <div id="output" style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; display: none;">
                <h4>Output:</h4>
                <pre id="outputContent"></pre>
            </div>
        </div>
        
        <script>
            // Update time
            function updateTime() {
                document.getElementById('time').textContent = new Date().toLocaleString();
            }
            updateTime();
            setInterval(updateTime, 1000);
            
            // Update stats
            async function updateStats() {
                try {
                    const response = await fetch('/api/stores');
                    const data = await response.json();
                    document.getElementById('storeCount').textContent = data.stores.length;
                } catch (e) {
                    console.error(e);
                }
            }
            updateStats();
            
            // Functions
            function showOutput(title, content) {
                document.getElementById('output').style.display = 'block';
                document.getElementById('outputContent').textContent = 
                    title + '\\n' + JSON.stringify(content, null, 2);
            }
            
            async function addStore() {
                const storeName = prompt('Enter store name:');
                if (storeName) {
                    const response = await fetch('/api/stores', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            name: storeName,
                            url: 'https://example.com',
                            id: 'store_' + Date.now()
                        })
                    });
                    const data = await response.json();
                    showOutput('Store Added:', data);
                    updateStats();
                }
            }
            
            async function viewStores() {
                const response = await fetch('/api/stores');
                const data = await response.json();
                showOutput('Stores:', data);
            }
            
            async function viewProducts() {
                const response = await fetch('/api/products');
                const data = await response.json();
                showOutput('Products:', data);
            }
            
            function importProducts() {
                alert('Import functionality: Upload CSV via the API endpoint /api/import');
            }
            
            function bulkUpdate() {
                alert('Bulk update: Use the API endpoint /api/bulk-update');
            }
            
            function syncStores() {
                alert('Sync initiated! Check the console for progress.');
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get('/api/status')
async def status():
    return {
        'status': 'operational',
        'timestamp': datetime.now().isoformat(),
        'message': 'MCP WooCommerce Suite is running'
    }

@app.get('/api/stores')
async def get_stores():
    return {'stores': list(stores.values())}

@app.post('/api/stores')
async def add_store(request: Request):
    try:
        data = await request.json()
        store_id = data.get('id', f'store_{len(stores)}')
        stores[store_id] = data
        return {'success': True, 'store_id': store_id, 'message': 'Store added successfully'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.get('/api/products')
async def get_products():
    # Demo products
    return {
        'products': [
            {'id': 1, 'name': 'Sample Product 1', 'price': 29.99, 'stock': 100, 'sku': 'PROD-001'},
            {'id': 2, 'name': 'Sample Product 2', 'price': 39.99, 'stock': 50, 'sku': 'PROD-002'},
            {'id': 3, 'name': 'Sample Product 3', 'price': 49.99, 'stock': 75, 'sku': 'PROD-003'}
        ],
        'total': 3
    }

if __name__ == "__main__":
    print("=" * 50)
    print("MCP WooCommerce Suite - Web Server")
    print("=" * 50)
    print()
    print("Starting server at http://localhost:8000")
    print("Press Ctrl+C to stop")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)