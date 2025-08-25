"""
Script to add RideBase.fi store to the Web Platform
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def add_ridebase_store():
    """Add RideBase.fi store configuration"""
    
    # Get credentials from environment
    store_url = os.getenv('STORE_URL', 'https://ridebase.fi/')
    consumer_key = os.getenv('WOOCOMMERCE_KEY')
    consumer_secret = os.getenv('WOOCOMMERCE_SECRET')
    
    if not consumer_key or not consumer_secret:
        print("ERROR: WooCommerce credentials not found in .env file!")
        return False
    
    # Store configuration
    store_config = {
        "id": "ridebase",
        "name": "RideBase.fi",
        "url": store_url,
        "consumer_key": consumer_key,
        "consumer_secret": consumer_secret,
        "active": True,
        "created_at": "2024-01-01T00:00:00",
        "last_synced": None,
        "settings": {
            "sync_interval": 3600,
            "auto_sync": False,
            "notifications": True
        }
    }
    
    # Load existing stores
    stores_file = Path("data/stores.json")
    if stores_file.exists():
        with open(stores_file, 'r') as f:
            stores = json.load(f)
    else:
        stores = {"stores": []}
    
    # Check if store already exists
    existing_store = next((s for s in stores["stores"] if s["id"] == "ridebase"), None)
    
    if existing_store:
        print("RideBase.fi store already exists. Updating...")
        # Update existing store
        existing_store.update(store_config)
    else:
        print("Adding RideBase.fi store...")
        stores["stores"].append(store_config)
    
    # Create data directory if it doesn't exist
    Path("data").mkdir(exist_ok=True)
    
    # Save stores
    with open(stores_file, 'w') as f:
        json.dump(stores, f, indent=2)
    
    print(f"✅ RideBase.fi store configured successfully!")
    print(f"   URL: {store_url}")
    print(f"   Key: {consumer_key[:20]}...")
    print(f"   Secret: {consumer_secret[:20]}...")
    
    return True

if __name__ == "__main__":
    add_ridebase_store()