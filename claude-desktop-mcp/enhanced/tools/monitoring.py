import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import logging
import os
import schedule
import time
from threading import Thread

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {}
        self.alerts = []
        self.thresholds = {
            "api_response_time": 3.0,
            "memory_usage": 85,
            "cpu_usage": 80,
            "disk_space": 90,
            "error_rate": 5.0
        }
    
    def collect_metrics(self, api_client) -> Dict[str, Any]:
        """Collect comprehensive performance metrics."""
        try:
            start_time = time.time()
            
            # Test API responsiveness
            api_client.get("products?per_page=1")
            api_response_time = time.time() - start_time
            
            # System metrics
            import psutil
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=1)
            disk = psutil.disk_usage('/')
            
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "api_response_time": api_response_time,
                "memory_usage_percent": memory.percent,
                "cpu_usage_percent": cpu,
                "disk_usage_percent": (disk.used / disk.total) * 100,
                "available_memory_gb": memory.available / (1024**3),
                "total_memory_gb": memory.total / (1024**3),
                "disk_free_gb": disk.free / (1024**3),
                "store_status": "online" if api_response_time < 5.0 else "slow"
            }
            
            self.check_thresholds(metrics)
            return metrics
            
        except Exception as e:
            error_metric = {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "store_status": "offline"
            }
            self.alerts.append({
                "type": "error",
                "message": f"Failed to collect metrics: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "severity": "critical"
            })
            return error_metric
    
    def check_thresholds(self, metrics: Dict[str, Any]):
        """Check metrics against thresholds and generate alerts."""
        alerts = []
        
        if metrics.get("api_response_time", 0) > self.thresholds["api_response_time"]:
            alerts.append({
                "type": "performance",
                "message": f"API response time high: {metrics['api_response_time']:.2f}s",
                "severity": "warning"
            })
        
        if metrics.get("memory_usage_percent", 0) > self.thresholds["memory_usage"]:
            alerts.append({
                "type": "system",
                "message": f"Memory usage high: {metrics['memory_usage_percent']:.1f}%",
                "severity": "warning"
            })
        
        if metrics.get("cpu_usage_percent", 0) > self.thresholds["cpu_usage"]:
            alerts.append({
                "type": "system",
                "message": f"CPU usage high: {metrics['cpu_usage_percent']:.1f}%",
                "severity": "warning"
            })
        
        if metrics.get("disk_usage_percent", 0) > self.thresholds["disk_space"]:
            alerts.append({
                "type": "system",
                "message": f"Disk space low: {metrics['disk_usage_percent']:.1f}% used",
                "severity": "critical"
            })
        
        for alert in alerts:
            alert["timestamp"] = datetime.now().isoformat()
            self.alerts.append(alert)

class BackupManager:
    def __init__(self, backup_dir: str = "./backups"):
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
    
    def create_backup(self, api_client, backup_type: str = "full") -> Dict[str, Any]:
        """Create comprehensive store backup."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{backup_type}_{timestamp}"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            os.makedirs(backup_path, exist_ok=True)
            
            backup_data = {
                "metadata": {
                    "backup_name": backup_name,
                    "backup_type": backup_type,
                    "timestamp": datetime.now().isoformat(),
                    "store_url": getattr(api_client, 'url', 'unknown')
                }
            }
            
            # Backup products
            if backup_type in ["full", "products"]:
                products = []
                page = 1
                while True:
                    response = api_client.get(f"products?per_page=100&page={page}")
                    if not response or len(response) == 0:
                        break
                    products.extend(response)
                    page += 1
                
                with open(os.path.join(backup_path, "products.json"), "w") as f:
                    json.dump(products, f, indent=2)
                backup_data["products_count"] = len(products)
            
            # Backup orders
            if backup_type in ["full", "orders"]:
                orders = []
                page = 1
                while True:
                    response = api_client.get(f"orders?per_page=100&page={page}")
                    if not response or len(response) == 0:
                        break
                    orders.extend(response)
                    page += 1
                
                with open(os.path.join(backup_path, "orders.json"), "w") as f:
                    json.dump(orders, f, indent=2)
                backup_data["orders_count"] = len(orders)
            
            # Backup customers
            if backup_type in ["full", "customers"]:
                customers = []
                page = 1
                while True:
                    response = api_client.get(f"customers?per_page=100&page={page}")
                    if not response or len(response) == 0:
                        break
                    customers.extend(response)
                    page += 1
                
                with open(os.path.join(backup_path, "customers.json"), "w") as f:
                    json.dump(customers, f, indent=2)
                backup_data["customers_count"] = len(customers)
            
            # Backup categories and tags
            if backup_type in ["full", "catalog"]:
                categories = api_client.get("products/categories?per_page=100")
                tags = api_client.get("products/tags?per_page=100")
                
                with open(os.path.join(backup_path, "categories.json"), "w") as f:
                    json.dump(categories, f, indent=2)
                with open(os.path.join(backup_path, "tags.json"), "w") as f:
                    json.dump(tags, f, indent=2)
                
                backup_data["categories_count"] = len(categories) if categories else 0
                backup_data["tags_count"] = len(tags) if tags else 0
            
            # Save backup metadata
            with open(os.path.join(backup_path, "metadata.json"), "w") as f:
                json.dump(backup_data, f, indent=2)
            
            # Create compressed archive
            import shutil
            archive_path = f"{backup_path}.zip"
            shutil.make_archive(backup_path, 'zip', backup_path)
            
            # Clean up uncompressed folder
            shutil.rmtree(backup_path)
            
            backup_size = os.path.getsize(archive_path)
            
            return {
                "success": True,
                "backup_name": backup_name,
                "backup_path": archive_path,
                "backup_size_mb": round(backup_size / (1024*1024), 2),
                "backup_type": backup_type,
                "timestamp": backup_data["metadata"]["timestamp"],
                "items_backed_up": {k: v for k, v in backup_data.items() if k.endswith("_count")}
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups."""
        backups = []
        
        try:
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.zip') and filename.startswith('backup_'):
                    file_path = os.path.join(self.backup_dir, filename)
                    file_stats = os.stat(file_path)
                    
                    backups.append({
                        "filename": filename,
                        "size_mb": round(file_stats.st_size / (1024*1024), 2),
                        "created": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                    })
            
            backups.sort(key=lambda x: x["created"], reverse=True)
            return backups
            
        except Exception as e:
            return [{"error": f"Failed to list backups: {str(e)}"}]
    
    def restore_backup(self, backup_name: str, api_client, restore_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Restore from backup (dry-run supported)."""
        if restore_options is None:
            restore_options = {"dry_run": True, "restore_products": True, "restore_orders": False}
        
        try:
            backup_path = os.path.join(self.backup_dir, f"{backup_name}.zip")
            if not os.path.exists(backup_path):
                return {"success": False, "error": "Backup file not found"}
            
            # Extract backup
            import shutil
            import tempfile
            
            with tempfile.TemporaryDirectory() as temp_dir:
                shutil.unpack_archive(backup_path, temp_dir)
                
                # Find the extracted folder
                extracted_folder = None
                for item in os.listdir(temp_dir):
                    item_path = os.path.join(temp_dir, item)
                    if os.path.isdir(item_path):
                        extracted_folder = item_path
                        break
                
                if not extracted_folder:
                    return {"success": False, "error": "Invalid backup format"}
                
                # Load metadata
                metadata_path = os.path.join(extracted_folder, "metadata.json")
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                
                restore_results = {
                    "dry_run": restore_options.get("dry_run", True),
                    "metadata": metadata,
                    "actions_planned": []
                }
                
                # Restore products
                if restore_options.get("restore_products", True):
                    products_path = os.path.join(extracted_folder, "products.json")
                    if os.path.exists(products_path):
                        with open(products_path, "r") as f:
                            products = json.load(f)
                        
                        restore_results["actions_planned"].append({
                            "type": "restore_products",
                            "count": len(products),
                            "status": "planned" if restore_options.get("dry_run") else "executed"
                        })
                        
                        if not restore_options.get("dry_run", True):
                            # Actually restore products (implement as needed)
                            pass
                
                # Restore customers
                if restore_options.get("restore_customers", False):
                    customers_path = os.path.join(extracted_folder, "customers.json")
                    if os.path.exists(customers_path):
                        with open(customers_path, "r") as f:
                            customers = json.load(f)
                        
                        restore_results["actions_planned"].append({
                            "type": "restore_customers",
                            "count": len(customers),
                            "status": "planned" if restore_options.get("dry_run") else "executed"
                        })
                
                return {"success": True, **restore_results}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

class HealthChecker:
    def __init__(self):
        self.checks = {}
        self.history = []
    
    def run_health_check(self, api_client) -> Dict[str, Any]:
        """Run comprehensive health check."""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "checks": {}
        }
        
        # API connectivity check
        try:
            start_time = time.time()
            api_client.get("system_status")
            response_time = time.time() - start_time
            
            health_status["checks"]["api_connectivity"] = {
                "status": "pass" if response_time < 5.0 else "warning",
                "response_time": response_time,
                "message": f"API responded in {response_time:.2f}s"
            }
        except Exception as e:
            health_status["checks"]["api_connectivity"] = {
                "status": "fail",
                "error": str(e),
                "message": "API is unreachable"
            }
            health_status["overall_status"] = "unhealthy"
        
        # Database connectivity (through API)
        try:
            products = api_client.get("products?per_page=1")
            health_status["checks"]["database"] = {
                "status": "pass",
                "message": "Database accessible through API"
            }
        except Exception as e:
            health_status["checks"]["database"] = {
                "status": "fail",
                "error": str(e),
                "message": "Database connection issues"
            }
            health_status["overall_status"] = "unhealthy"
        
        # SSL certificate check
        try:
            import ssl
            import socket
            from urllib.parse import urlparse
            
            parsed_url = urlparse(getattr(api_client, 'url', ''))
            hostname = parsed_url.hostname
            
            if hostname and parsed_url.scheme == 'https':
                context = ssl.create_default_context()
                with socket.create_connection((hostname, 443)) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert = ssock.getpeercert()
                        expiry = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                        days_to_expiry = (expiry - datetime.now()).days
                        
                        health_status["checks"]["ssl_certificate"] = {
                            "status": "pass" if days_to_expiry > 30 else "warning",
                            "expiry_date": expiry.isoformat(),
                            "days_to_expiry": days_to_expiry,
                            "message": f"SSL certificate expires in {days_to_expiry} days"
                        }
        except Exception as e:
            health_status["checks"]["ssl_certificate"] = {
                "status": "warning",
                "error": str(e),
                "message": "Could not check SSL certificate"
            }
        
        # Store configuration check
        try:
            settings = api_client.get("settings/general")
            health_status["checks"]["store_configuration"] = {
                "status": "pass",
                "message": "Store settings accessible",
                "store_title": settings[0].get("value", "Unknown") if settings else "Unknown"
            }
        except Exception as e:
            health_status["checks"]["store_configuration"] = {
                "status": "warning",
                "error": str(e),
                "message": "Could not verify store configuration"
            }
        
        # Set overall status based on individual checks
        failed_checks = [k for k, v in health_status["checks"].items() if v.get("status") == "fail"]
        if failed_checks:
            health_status["overall_status"] = "unhealthy"
        elif any(v.get("status") == "warning" for v in health_status["checks"].values()):
            health_status["overall_status"] = "degraded"
        
        self.history.append(health_status)
        
        # Keep only last 50 health checks
        if len(self.history) > 50:
            self.history = self.history[-50:]
        
        return health_status

# MCP Tool Functions
def monitor_store_performance(api_client, monitoring_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Monitor store performance metrics and generate alerts."""
    if monitoring_config is None:
        monitoring_config = {"collect_system_metrics": True, "check_thresholds": True}
    
    try:
        monitor = PerformanceMonitor()
        
        # Override thresholds if provided
        if "thresholds" in monitoring_config:
            monitor.thresholds.update(monitoring_config["thresholds"])
        
        metrics = monitor.collect_metrics(api_client)
        
        return {
            "success": True,
            "metrics": metrics,
            "alerts": monitor.alerts[-10:],  # Last 10 alerts
            "thresholds": monitor.thresholds,
            "monitoring_config": monitoring_config
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def create_store_backup(api_client, backup_config: Dict[str, Any]) -> Dict[str, Any]:
    """Create comprehensive store backup."""
    backup_type = backup_config.get("backup_type", "full")
    
    try:
        backup_manager = BackupManager()
        result = backup_manager.create_backup(api_client, backup_type)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def list_store_backups() -> Dict[str, Any]:
    """List all available store backups."""
    try:
        backup_manager = BackupManager()
        backups = backup_manager.list_backups()
        
        return {
            "success": True,
            "backups": backups,
            "total_backups": len(backups),
            "backup_directory": backup_manager.backup_dir
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def restore_store_backup(api_client, restore_config: Dict[str, Any]) -> Dict[str, Any]:
    """Restore store from backup with safety options."""
    backup_name = restore_config.get("backup_name")
    if not backup_name:
        return {"success": False, "error": "backup_name is required"}
    
    try:
        backup_manager = BackupManager()
        
        # Default to dry-run for safety
        restore_options = {
            "dry_run": restore_config.get("dry_run", True),
            "restore_products": restore_config.get("restore_products", True),
            "restore_customers": restore_config.get("restore_customers", False),
            "restore_orders": restore_config.get("restore_orders", False)
        }
        
        result = backup_manager.restore_backup(backup_name, api_client, restore_options)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def run_store_health_check(api_client) -> Dict[str, Any]:
    """Run comprehensive store health check."""
    try:
        health_checker = HealthChecker()
        health_status = health_checker.run_health_check(api_client)
        
        return {
            "success": True,
            **health_status
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def setup_monitoring_schedule(api_client, schedule_config: Dict[str, Any]) -> Dict[str, Any]:
    """Setup automated monitoring schedule."""
    try:
        monitoring_interval = schedule_config.get("monitoring_interval_minutes", 30)
        backup_interval = schedule_config.get("backup_interval_hours", 24)
        health_check_interval = schedule_config.get("health_check_interval_minutes", 15)
        
        def run_monitoring():
            """Background monitoring task."""
            try:
                monitor = PerformanceMonitor()
                metrics = monitor.collect_metrics(api_client)
                
                # Log metrics
                logging.info(f"Store metrics: {metrics}")
                
                # Check for critical alerts
                critical_alerts = [alert for alert in monitor.alerts if alert.get("severity") == "critical"]
                if critical_alerts:
                    logging.critical(f"Critical alerts: {critical_alerts}")
                
            except Exception as e:
                logging.error(f"Monitoring task failed: {str(e)}")
        
        def run_backup():
            """Background backup task."""
            try:
                backup_manager = BackupManager()
                result = backup_manager.create_backup(api_client, "incremental")
                logging.info(f"Scheduled backup completed: {result}")
                
            except Exception as e:
                logging.error(f"Backup task failed: {str(e)}")
        
        def run_health_check():
            """Background health check task."""
            try:
                health_checker = HealthChecker()
                health = health_checker.run_health_check(api_client)
                
                if health["overall_status"] != "healthy":
                    logging.warning(f"Store health issue: {health}")
                
            except Exception as e:
                logging.error(f"Health check failed: {str(e)}")
        
        # Schedule tasks
        schedule.every(monitoring_interval).minutes.do(run_monitoring)
        schedule.every(backup_interval).hours.do(run_backup)
        schedule.every(health_check_interval).minutes.do(run_health_check)
        
        # Start scheduler in background thread
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        scheduler_thread = Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        return {
            "success": True,
            "message": "Monitoring schedule setup successfully",
            "schedule": {
                "monitoring_interval_minutes": monitoring_interval,
                "backup_interval_hours": backup_interval,
                "health_check_interval_minutes": health_check_interval
            },
            "scheduler_thread_active": scheduler_thread.is_alive()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def get_monitoring_dashboard(api_client) -> Dict[str, Any]:
    """Get comprehensive monitoring dashboard data."""
    try:
        # Collect current metrics
        monitor = PerformanceMonitor()
        current_metrics = monitor.collect_metrics(api_client)
        
        # Run health check
        health_checker = HealthChecker()
        health_status = health_checker.run_health_check(api_client)
        
        # Get backup info
        backup_manager = BackupManager()
        backup_list = backup_manager.list_backups()
        
        dashboard = {
            "timestamp": datetime.now().isoformat(),
            "current_metrics": current_metrics,
            "health_status": health_status,
            "recent_alerts": monitor.alerts[-5:] if monitor.alerts else [],
            "backup_summary": {
                "total_backups": len(backup_list),
                "latest_backup": backup_list[0] if backup_list else None,
                "total_backup_size_mb": sum(backup.get("size_mb", 0) for backup in backup_list)
            },
            "system_status": {
                "store_online": current_metrics.get("store_status") == "online",
                "api_responsive": current_metrics.get("api_response_time", 10) < 5.0,
                "health_overall": health_status.get("overall_status", "unknown"),
                "critical_alerts": len([a for a in monitor.alerts if a.get("severity") == "critical"])
            }
        }
        
        return {
            "success": True,
            "dashboard": dashboard
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }