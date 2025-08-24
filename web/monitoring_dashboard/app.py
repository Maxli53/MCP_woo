#!/usr/bin/env python3
"""
Monitoring Dashboard - Administrative interface for MCP servers
"""

import asyncio
import json
import logging
import psutil
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path
import time
import redis
from collections import defaultdict

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="MCP Monitoring Dashboard", description="Administrative monitoring for MCP servers")

# Templates
templates = Jinja2Templates(directory="web/templates")

# Redis connection for metrics storage
redis_client = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)

# Models
class ServerMetrics(BaseModel):
    server_id: str
    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    active_connections: int
    requests_per_minute: float
    response_time_ms: float
    error_rate: float

class ToolUsageStats(BaseModel):
    tool_name: str
    call_count: int
    avg_execution_time_ms: float
    success_rate: float
    last_used: datetime

# Global state for metrics collection
active_servers: Dict[str, Dict] = {}
metrics_history: List[Dict] = []
tool_usage_stats: Dict[str, Dict] = defaultdict(lambda: {
    'call_count': 0,
    'total_time_ms': 0,
    'success_count': 0,
    'last_used': None
})

class MetricsCollector:
    """Collects system and application metrics"""
    
    def __init__(self):
        self.start_time = datetime.now()
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory': {
                'total_mb': psutil.virtual_memory().total / (1024*1024),
                'used_mb': psutil.virtual_memory().used / (1024*1024),
                'percent': psutil.virtual_memory().percent
            },
            'disk': {
                'total_gb': psutil.disk_usage('/').total / (1024*1024*1024),
                'used_gb': psutil.disk_usage('/').used / (1024*1024*1024),
                'percent': (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100
            },
            'network': {
                'bytes_sent': psutil.net_io_counters().bytes_sent,
                'bytes_recv': psutil.net_io_counters().bytes_recv
            }
        }
    
    def get_uptime(self) -> Dict[str, Any]:
        """Get server uptime"""
        uptime = datetime.now() - self.start_time
        return {
            'uptime_seconds': uptime.total_seconds(),
            'uptime_string': str(uptime).split('.')[0],  # Remove microseconds
            'start_time': self.start_time.isoformat()
        }

metrics_collector = MetricsCollector()

class DashboardWebSocketManager:
    """Manages WebSocket connections for dashboard updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
    async def broadcast_metrics(self, metrics: dict):
        for connection in self.active_connections[:]:  # Copy list to avoid modification during iteration
            try:
                await connection.send_text(json.dumps({
                    "type": "metrics_update",
                    "data": metrics,
                    "timestamp": datetime.now().isoformat()
                }))
            except:
                self.active_connections.remove(connection)

dashboard_manager = DashboardWebSocketManager()

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main monitoring dashboard"""
    system_metrics = metrics_collector.get_system_metrics()
    uptime_info = metrics_collector.get_uptime()
    
    return templates.TemplateResponse("dashboard/index.html", {
        "request": request,
        "title": "Monitoring Dashboard",
        "current_time": datetime.now().isoformat(),
        "system_metrics": system_metrics,
        "uptime_info": uptime_info,
        "active_servers_count": len(active_servers)
    })

@app.get("/api/metrics/system")
async def get_system_metrics():
    """Get current system metrics"""
    metrics = metrics_collector.get_system_metrics()
    uptime = metrics_collector.get_uptime()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "system": metrics,
        "uptime": uptime,
        "active_servers": len(active_servers)
    }

@app.get("/api/metrics/servers")
async def get_server_metrics():
    """Get metrics for all active MCP servers"""
    server_metrics = []
    
    for server_id, server_info in active_servers.items():
        # Calculate metrics from stored data
        metrics = {
            "server_id": server_id,
            "name": server_info.get("name", server_id),
            "status": server_info.get("status", "unknown"),
            "uptime_seconds": (datetime.now() - server_info.get("start_time", datetime.now())).total_seconds(),
            "total_requests": server_info.get("total_requests", 0),
            "active_connections": server_info.get("active_connections", 0),
            "last_request": server_info.get("last_request"),
            "error_count": server_info.get("error_count", 0),
            "tools_count": len(server_info.get("tools", [])),
        }
        server_metrics.append(metrics)
    
    return {"servers": server_metrics}

@app.get("/api/metrics/tools")
async def get_tool_usage_stats():
    """Get tool usage statistics"""
    stats = []
    
    for tool_name, usage_data in tool_usage_stats.items():
        if usage_data['call_count'] > 0:
            avg_time = usage_data['total_time_ms'] / usage_data['call_count']
            success_rate = (usage_data['success_count'] / usage_data['call_count']) * 100
            
            stats.append({
                "tool_name": tool_name,
                "call_count": usage_data['call_count'],
                "avg_execution_time_ms": round(avg_time, 2),
                "success_rate": round(success_rate, 2),
                "last_used": usage_data['last_used']
            })
    
    # Sort by call count descending
    stats.sort(key=lambda x: x['call_count'], reverse=True)
    
    return {"tool_stats": stats}

@app.get("/api/metrics/history")
async def get_metrics_history(hours: int = 24):
    """Get historical metrics data"""
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    # Filter metrics history
    recent_metrics = [
        metric for metric in metrics_history
        if datetime.fromisoformat(metric.get('timestamp', '')) > cutoff_time
    ]
    
    return {
        "history": recent_metrics,
        "period_hours": hours,
        "data_points": len(recent_metrics)
    }

@app.post("/api/metrics/server-event")
async def record_server_event(event_data: dict):
    """Record server events for monitoring"""
    server_id = event_data.get("server_id", "unknown")
    event_type = event_data.get("type", "unknown")
    
    # Initialize server if not exists
    if server_id not in active_servers:
        active_servers[server_id] = {
            "name": event_data.get("server_name", server_id),
            "start_time": datetime.now(),
            "status": "active",
            "total_requests": 0,
            "error_count": 0,
            "active_connections": 0,
            "tools": event_data.get("tools", []),
            "last_request": None
        }
    
    server_info = active_servers[server_id]
    
    # Update server info based on event type
    if event_type == "connection":
        server_info["active_connections"] = event_data.get("connection_count", 0)
        server_info["status"] = "connected"
    
    elif event_type == "tool_call":
        server_info["total_requests"] += 1
        server_info["last_request"] = datetime.now().isoformat()
        
        # Update tool usage stats
        tool_name = event_data.get("tool_name")
        execution_time = event_data.get("execution_time_ms", 0)
        success = event_data.get("success", False)
        
        if tool_name:
            tool_usage_stats[tool_name]['call_count'] += 1
            tool_usage_stats[tool_name]['total_time_ms'] += execution_time
            if success:
                tool_usage_stats[tool_name]['success_count'] += 1
            tool_usage_stats[tool_name]['last_used'] = datetime.now().isoformat()
    
    elif event_type == "error":
        server_info["error_count"] += 1
    
    elif event_type == "disconnect":
        server_info["status"] = "disconnected"
        server_info["active_connections"] = 0
    
    # Store metrics in history
    metrics_entry = {
        "timestamp": datetime.now().isoformat(),
        "server_id": server_id,
        "event_type": event_type,
        "data": event_data
    }
    metrics_history.append(metrics_entry)
    
    # Keep only last 1000 entries
    if len(metrics_history) > 1000:
        metrics_history.pop(0)
    
    # Broadcast update to dashboard
    await dashboard_manager.broadcast_metrics({
        "server_update": {
            "server_id": server_id,
            "event_type": event_type,
            "server_info": server_info
        }
    })
    
    return {"status": "recorded", "server_id": server_id}

@app.get("/api/logs/recent")
async def get_recent_logs(limit: int = 100):
    """Get recent log entries"""
    # Get recent metrics as log entries
    recent_logs = metrics_history[-limit:] if metrics_history else []
    
    return {
        "logs": recent_logs,
        "count": len(recent_logs)
    }

@app.post("/api/admin/restart-server")
async def restart_server(server_data: dict):
    """Administrative action to restart a server"""
    server_id = server_data.get("server_id")
    
    if server_id not in active_servers:
        return {"status": "error", "message": "Server not found"}
    
    # Record restart event
    await record_server_event({
        "server_id": server_id,
        "type": "restart",
        "timestamp": datetime.now().isoformat(),
        "admin_action": True
    })
    
    return {
        "status": "success", 
        "message": f"Restart signal sent to server {server_id}",
        "action": "restart"
    }

@app.post("/api/admin/stop-server")
async def stop_server(server_data: dict):
    """Administrative action to stop a server"""
    server_id = server_data.get("server_id")
    
    if server_id not in active_servers:
        return {"status": "error", "message": "Server not found"}
    
    # Update server status
    active_servers[server_id]["status"] = "stopped"
    
    # Record stop event
    await record_server_event({
        "server_id": server_id,
        "type": "stop",
        "timestamp": datetime.now().isoformat(),
        "admin_action": True
    })
    
    return {
        "status": "success",
        "message": f"Stop signal sent to server {server_id}",
        "action": "stop"
    }

@app.websocket("/dashboard/ws")
async def dashboard_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates"""
    await dashboard_manager.connect(websocket)
    try:
        while True:
            # Send periodic system metrics
            system_metrics = metrics_collector.get_system_metrics()
            uptime = metrics_collector.get_uptime()
            
            await websocket.send_text(json.dumps({
                "type": "system_metrics",
                "data": {
                    "system": system_metrics,
                    "uptime": uptime,
                    "active_servers": len(active_servers)
                },
                "timestamp": datetime.now().isoformat()
            }))
            
            # Wait for incoming messages or timeout
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)
                
                # Handle client requests
                if message.get("type") == "get_server_list":
                    await websocket.send_text(json.dumps({
                        "type": "server_list",
                        "data": list(active_servers.keys()),
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_text(json.dumps({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                }))
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        dashboard_manager.disconnect(websocket)

async def background_metrics_collection():
    """Background task to collect and store metrics"""
    while True:
        try:
            # Collect system metrics
            system_metrics = metrics_collector.get_system_metrics()
            
            # Store in metrics history
            metrics_entry = {
                "timestamp": datetime.now().isoformat(),
                "type": "system_metrics",
                "data": system_metrics
            }
            metrics_history.append(metrics_entry)
            
            # Keep history size manageable
            if len(metrics_history) > 2000:
                metrics_history.pop(0)
            
            # Broadcast to connected dashboards
            await dashboard_manager.broadcast_metrics({
                "system_metrics": system_metrics
            })
            
        except Exception as e:
            logger.error(f"Background metrics collection error: {e}")
        
        # Sleep for 30 seconds
        await asyncio.sleep(30)

@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    # Start background metrics collection
    asyncio.create_task(background_metrics_collection())
    logger.info("Monitoring Dashboard started")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)