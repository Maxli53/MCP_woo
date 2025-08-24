#!/usr/bin/env python3
"""
MCP Inspector - Web Interface for Testing MCP Server Tools
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client, StdioServerParameters

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="MCP Inspector", description="Web interface for testing MCP servers")

# Templates and static files
templates = Jinja2Templates(directory="web/templates")
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Models
class ServerConfig(BaseModel):
    name: str
    transport: str  # "stdio" or "sse"
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    env: Optional[Dict[str, str]] = None

class ToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Global state
current_session: Optional[ClientSession] = None
server_tools: List[Dict] = []
connection_history: List[Dict] = []

@app.get("/", response_class=HTMLResponse)
async def inspector_home(request: Request):
    """Main inspector interface"""
    return templates.TemplateResponse("inspector/index.html", {
        "request": request,
        "title": "MCP Inspector",
        "current_time": datetime.now().isoformat()
    })

@app.get("/api/servers/test")
async def test_server_connection(server_url: str = None, command: str = None):
    """Test connection to an MCP server"""
    try:
        if server_url:
            # Test SSE connection
            async with sse_client(server_url) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    return {
                        "status": "success",
                        "message": f"Connected to SSE server at {server_url}",
                        "tools_count": len(tools.tools)
                    }
        elif command:
            # Test STDIO connection
            server_params = StdioServerParameters(
                command=command.split()[0],
                args=command.split()[1:] if len(command.split()) > 1 else [],
                env=None
            )
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    return {
                        "status": "success", 
                        "message": f"Connected to STDIO server: {command}",
                        "tools_count": len(tools.tools)
                    }
        else:
            return {"status": "error", "message": "No server URL or command provided"}
            
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/servers/connect")
async def connect_to_server(config: ServerConfig):
    """Connect to an MCP server and load tools"""
    global current_session, server_tools
    
    try:
        connection_info = {
            "timestamp": datetime.now().isoformat(),
            "server_name": config.name,
            "transport": config.transport,
            "status": "attempting"
        }
        
        if config.transport == "sse":
            if not config.url:
                raise ValueError("URL required for SSE transport")
                
            # Connect via SSE
            async with sse_client(config.url) as (read, write):
                session = ClientSession(read, write)
                await session.initialize()
                
                # Get available tools
                tools_result = await session.list_tools()
                server_tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    }
                    for tool in tools_result.tools
                ]
                
                # Get available resources if any
                try:
                    resources_result = await session.list_resources()
                    resources = [
                        {
                            "name": resource.name,
                            "uri": resource.uri,
                            "description": resource.description
                        }
                        for resource in resources_result.resources
                    ]
                except:
                    resources = []
                
                connection_info.update({
                    "status": "connected",
                    "tools_count": len(server_tools),
                    "resources_count": len(resources),
                    "url": config.url
                })
                
        elif config.transport == "stdio":
            if not config.command:
                raise ValueError("Command required for STDIO transport")
                
            # Connect via STDIO
            server_params = StdioServerParameters(
                command=config.command,
                args=config.args or [],
                env=config.env
            )
            
            async with stdio_client(server_params) as (read, write):
                session = ClientSession(read, write)
                await session.initialize()
                
                # Get available tools
                tools_result = await session.list_tools()
                server_tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    }
                    for tool in tools_result.tools
                ]
                
                connection_info.update({
                    "status": "connected",
                    "tools_count": len(server_tools),
                    "command": config.command
                })
        
        connection_history.append(connection_info)
        
        # Broadcast connection update
        await manager.broadcast({
            "type": "connection_update",
            "data": connection_info
        })
        
        return {
            "status": "success",
            "message": f"Connected to {config.name}",
            "tools": server_tools,
            "connection": connection_info
        }
        
    except Exception as e:
        logger.error(f"Failed to connect to server: {e}")
        connection_info["status"] = "failed"
        connection_info["error"] = str(e)
        connection_history.append(connection_info)
        
        return {"status": "error", "message": str(e)}

@app.get("/api/tools")
async def get_available_tools():
    """Get list of available tools from connected server"""
    return {"tools": server_tools}

@app.post("/api/tools/call")
async def call_tool(tool_call: ToolCall):
    """Execute a tool call and return results"""
    global current_session
    
    if not server_tools:
        raise HTTPException(status_code=400, detail="No server connected")
    
    try:
        # Find tool schema for validation
        tool_schema = next((t for t in server_tools if t["name"] == tool_call.tool_name), None)
        if not tool_schema:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_call.tool_name}' not found")
        
        # Record the call
        call_record = {
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_call.tool_name,
            "arguments": tool_call.arguments,
            "status": "executing"
        }
        
        # Broadcast call start
        await manager.broadcast({
            "type": "tool_call_start",
            "data": call_record
        })
        
        # Execute tool (this is a simplified version - in reality you'd need to maintain the session)
        # For demonstration, we'll simulate the call
        result = {
            "success": True,
            "content": [
                {
                    "type": "text",
                    "text": f"Simulated result for {tool_call.tool_name} with args: {tool_call.arguments}"
                }
            ],
            "execution_time_ms": 150
        }
        
        call_record.update({
            "status": "completed",
            "result": result,
            "execution_time_ms": result["execution_time_ms"]
        })
        
        # Broadcast call completion
        await manager.broadcast({
            "type": "tool_call_complete",
            "data": call_record
        })
        
        return call_record
        
    except Exception as e:
        logger.error(f"Tool call failed: {e}")
        call_record.update({
            "status": "failed",
            "error": str(e)
        })
        
        await manager.broadcast({
            "type": "tool_call_error",
            "data": call_record
        })
        
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history")
async def get_connection_history():
    """Get connection history"""
    return {"history": connection_history}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif message.get("type") == "get_status":
                await websocket.send_text(json.dumps({
                    "type": "status_update",
                    "data": {
                        "connected_server": bool(server_tools),
                        "tools_count": len(server_tools),
                        "timestamp": datetime.now().isoformat()
                    }
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)