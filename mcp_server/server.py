"""
Aetheris Omni-Agent: FastAPI MCP Server (Spec 2025-11-25) & Web Simulator Host
Supports Streamable HTTP, SSE streaming, JSON-RPC 2.0, and REST orchestration.
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .tools import MCP_TOOL_DEFINITIONS, execute_tool, init_db, reset_db
from .state_manager import state_manager
from .orchestrator_aws import agent_orchestrator

# Initialize database
init_db()

app = FastAPI(
    title="Aetheris Omni-Agent MCP Server",
    description="Amazon Developer Hackathon: Alexa+, Ring, Bee Wearable AI & Fire TV Orchestrator",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(BASE_DIR, "web_simulator")
STATIC_DIR = os.path.join(WEB_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)

# Generate high-resolution SVG assets for Ring Cam, Fire TV canvas, and Couriers so no image links break
def generate_default_assets():
    assets = {
        "courier_drop.jpg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400" width="100%" height="100%">
            <defs>
                <linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#0f172a"/>
                    <stop offset="100%" stop-color="#1e293b"/>
                </linearGradient>
            </defs>
            <rect width="600" height="400" fill="url(#g1)"/>
            <rect x="20" y="20" width="560" height="360" rx="12" fill="none" stroke="#007185" stroke-width="2" stroke-dasharray="8 4"/>
            <circle cx="300" cy="160" r="45" fill="#00A8E1" opacity="0.2"/>
            <path d="M280 160 L295 175 L325 145" fill="none" stroke="#00A8E1" stroke-width="4" stroke-linecap="round"/>
            <text x="300" y="240" fill="#f8fafc" font-family="system-ui, sans-serif" font-size="20" font-weight="700" text-anchor="middle">RING LIVE SECURE BUFFER</text>
            <text x="300" y="270" fill="#38bdf8" font-family="system-ui, sans-serif" font-size="14" text-anchor="middle">Amazon Prime Verified Courier • Door Access Granted</text>
            <rect x="220" y="300" width="160" height="30" rx="6" fill="#00A8E1" opacity="0.2"/>
            <text x="300" y="320" fill="#38bdf8" font-family="monospace" font-size="12" text-anchor="middle">1080p HDR 30 FPS</text>
        </svg>''',
        
        "clear_porch.jpg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400" width="100%" height="100%">
            <rect width="600" height="400" fill="#0b1120"/>
            <circle cx="300" cy="180" r="50" fill="#10b981" opacity="0.15"/>
            <text x="300" y="250" fill="#f8fafc" font-family="system-ui, sans-serif" font-size="18" font-weight="600" text-anchor="middle">FRONT PORCH MONITORED</text>
            <text x="300" y="280" fill="#94a3b8" font-family="system-ui, sans-serif" font-size="13" text-anchor="middle">Ring Security Active • Porch Clear • Lock Engaged</text>
        </svg>''',

        "door_unlocked.jpg": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400" width="100%" height="100%">
            <rect width="600" height="400" fill="#1e1b4b"/>
            <circle cx="300" cy="170" r="45" fill="#f59e0b" opacity="0.2"/>
            <text x="300" y="240" fill="#fbbf24" font-family="system-ui, sans-serif" font-size="20" font-weight="700" text-anchor="middle">SMART ACCESS UNLOCKED</text>
            <text x="300" y="270" fill="#f8fafc" font-family="system-ui, sans-serif" font-size="14" text-anchor="middle">Courier Delivery Window: 60s Temporary Access</text>
        </svg>''',

        "package_delivered.png": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400" width="100%" height="100%">
            <rect width="600" height="400" fill="#042f2e"/>
            <rect x="250" y="130" width="100" height="80" rx="8" fill="#14b8a6" opacity="0.3"/>
            <text x="300" y="250" fill="#f8fafc" font-family="system-ui, sans-serif" font-size="20" font-weight="700" text-anchor="middle">AMAZON 1-CLICK ORDER DISPATCHED</text>
            <text x="300" y="280" fill="#2dd4bf" font-family="system-ui, sans-serif" font-size="14" text-anchor="middle">Prime Express Delivery Confirmed</text>
        </svg>''',

        "calendar_resolved.png": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400" width="100%" height="100%">
            <rect width="600" height="400" fill="#1e1e38"/>
            <circle cx="300" cy="160" r="45" fill="#818cf8" opacity="0.2"/>
            <text x="300" y="245" fill="#f8fafc" font-family="system-ui, sans-serif" font-size="20" font-weight="700" text-anchor="middle">CALENDAR CONFLICT OPTIMIZED</text>
            <text x="300" y="275" fill="#a5b4fc" font-family="system-ui, sans-serif" font-size="14" text-anchor="middle">Operations Sync shifted to 2:00 PM • All Clear</text>
        </svg>''',

        "focus_mode.png": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400" width="100%" height="100%">
            <rect width="600" height="400" fill="#0f172a"/>
            <circle cx="300" cy="160" r="45" fill="#38bdf8" opacity="0.2"/>
            <text x="300" y="245" fill="#38bdf8" font-family="system-ui, sans-serif" font-size="20" font-weight="700" text-anchor="middle">WORKSPACE FOCUS AMBIENCE</text>
            <text x="300" y="275" fill="#94a3b8" font-family="system-ui, sans-serif" font-size="14" text-anchor="middle">5,500K Daylight White • Ring Chimes Muted • Bee Telemetry Synced</text>
        </svg>''',

        "ambient_firetv.png": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400" width="100%" height="100%">
            <defs>
                <linearGradient id="tvGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#181824"/>
                    <stop offset="100%" stop-color="#0b0b10"/>
                </linearGradient>
            </defs>
            <rect width="600" height="400" fill="url(#tvGrad)"/>
            <circle cx="300" cy="160" r="50" fill="#00A8E1" opacity="0.15"/>
            <text x="300" y="245" fill="#f8fafc" font-family="system-ui, sans-serif" font-size="22" font-weight="800" text-anchor="middle">AETHERIS AMBIENT CANVAS</text>
            <text x="300" y="275" fill="#94a3b8" font-family="system-ui, sans-serif" font-size="14" text-anchor="middle">Fire TV &amp; Vega OS Multimodal Display Engine</text>
            <text x="300" y="310" fill="#00A8E1" font-family="monospace" font-size="12" text-anchor="middle">MCP Spec 2025-11-25 Connected</text>
        </svg>'''
    }
    
    for filename, content in assets.items():
        file_path = os.path.join(STATIC_DIR, filename)
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

generate_default_assets()

# =====================================================================
# MCP SPEC 2025-11-25 IMPLEMENTATION (Streamable HTTP / SSE Protocol)
# =====================================================================

MCP_RESOURCES = [
    {
        "uri": "ring://camera/porch/live",
        "name": "Ring Video Doorbell Pro Live Snapshot",
        "description": "Live 1080p HDR frame and motion security buffer from Ring Front Porch.",
        "mimeType": "application/json"
    },
    {
        "uri": "bee://wearable/biometrics/stream",
        "name": "Bee Wearable AI Biometric Telemetry",
        "description": "Real-time heart rate, stress index, and ambient meeting transcription notes.",
        "mimeType": "application/json"
    },
    {
        "uri": "schedule://calendar/today",
        "name": "Executive Calendar & Room Allocation",
        "description": "Today's synced schedule with conflict flags and participants.",
        "mimeType": "application/json"
    },
    {
        "uri": "firetv://canvas/active",
        "name": "Fire TV Vega OS Ambient Canvas Screen",
        "description": "Active multimodal visual card rendered on the TV display.",
        "mimeType": "application/json"
    }
]

MCP_PROMPTS = [
    {
        "name": "autonomous_daily_briefing",
        "description": "Orchestrates a comprehensive morning briefing across Alexa+, Ring, Bee, and Fire TV.",
        "arguments": []
    },
    {
        "name": "handle_visitor_delivery",
        "description": "Verifies visitor at Ring Doorbell, logs package dropoff, and manages access.",
        "arguments": [
            {"name": "visitor_type", "description": "Type of visitor (courier, guest, contractor)", "required": True}
        ]
    },
    {
        "name": "engage_deep_work_mode",
        "description": "Synchronizes Bee stress indicators, dials lighting to 5500K, and mutes chimes.",
        "arguments": []
    }
]

@app.post("/mcp")
async def mcp_jsonrpc_endpoint(request: Request):
    """
    Standard Model Context Protocol JSON-RPC 2.0 endpoint (Spec 2025-11-25).
    Handles initialize, tools/list, tools/call, resources/list, resources/read, prompts/list.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON in MCP request")

    # Handle batch or single RPC
    is_batch = isinstance(body, list)
    requests = body if is_batch else [body]
    responses = []

    for req in requests:
        jsonrpc = req.get("jsonrpc", "2.0")
        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        # Log incoming MCP payload
        state_manager.log_protocol("INCOMING", method or "unknown", req)

        # 1. Initialize
        if method == "initialize":
            resp_data = {
                "protocolVersion": "2025-11-25",
                "capabilities": {
                    "tools": {"listChanged": True},
                    "resources": {"subscribe": True, "listChanged": True},
                    "prompts": {"listChanged": True},
                    "logging": {}
                },
                "serverInfo": {
                    "name": "aetheris-omni-mcp-server",
                    "version": "1.0.0",
                    "description": "Amazon Developer Hackathon Multi-Device MCP Hub for Alexa+, Ring, Bee, and Fire TV"
                }
            }
            res = {"jsonrpc": "2.0", "id": req_id, "result": resp_data}

        # 2. Notifications / Initialized
        elif method == "notifications/initialized":
            continue # No response required for notifications

        # 3. Ping
        elif method == "ping":
            res = {"jsonrpc": "2.0", "id": req_id, "result": {}}

        # 4. Tools List
        elif method == "tools/list":
            res = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": MCP_TOOL_DEFINITIONS
                }
            }

        # 5. Tools Call
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            exec_result = execute_tool(tool_name, tool_args)
            res = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": exec_result
            }

        # 6. Resources List
        elif method == "resources/list":
            res = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "resources": MCP_RESOURCES
                }
            }

        # 7. Resources Read
        elif method == "resources/read":
            uri = params.get("uri", "")
            system_state = state_manager.get_system_state()
            content_text = json.dumps(system_state, indent=2)
            res = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "contents": [{
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": content_text
                    }]
                }
            }

        # 8. Prompts List
        elif method == "prompts/list":
            res = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "prompts": MCP_PROMPTS
                }
            }

        else:
            res = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not found on Aetheris MCP server."
                }
            }

        # Log outgoing MCP payload
        state_manager.log_protocol("OUTGOING", method or "response", res)
        responses.append(res)

    if not responses:
        return Response(status_code=204)
        
    return JSONResponse(content=responses if is_batch else responses[0])

@app.get("/mcp")
async def mcp_streamable_sse_endpoint(request: Request):
    """
    Streamable HTTP / SSE Endpoint (MCP Spec 2025-11-25).
    Streams real-time tool change notifications and system logs.
    """
    async def sse_generator():
        client_queue = await state_manager.subscribe()
        try:
            # Yield initial connect handshake
            handshake = {
                "jsonrpc": "2.0",
                "method": "notifications/stream_connected",
                "params": {
                    "server": "aetheris-omni-mcp-server",
                    "spec": "2025-11-25",
                    "status": "STREAMABLE_HTTP_ACTIVE"
                }
            }
            yield f"data: {json.dumps(handshake)}\n\n"

            while True:
                # Check for client disconnect
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(client_queue.get(), timeout=20.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat comment
                    yield ": ping\n\n"
        finally:
            state_manager.unsubscribe(client_queue)

    return StreamingResponse(sse_generator(), media_type="text/event-stream")

# =====================================================================
# SIMULATED ALEXA+ REST API & UI CONTROLLER ENDPOINTS
# =====================================================================

class ChatRequest(BaseModel):
    text: str

@app.post("/api/chat")
async def api_chat_endpoint(req: ChatRequest):
    """
    Simulated Alexa+ agent interaction endpoint.
    Processes user speech/text and coordinates multi-device autonomous actions.
    """
    result = await agent_orchestrator.process_user_query(req.text)
    return JSONResponse(content=result)

@app.get("/api/state")
async def api_state_endpoint():
    """Returns real-time telemetry snapshot of all Amazon devices and DB records."""
    state = state_manager.get_system_state()
    return JSONResponse(content=state)

@app.post("/api/scenario/{scenario_name}")
async def api_scenario_endpoint(scenario_name: str):
    """Triggers scripted high-impact cross-device scenarios for demonstration."""
    result = await state_manager.run_scenario(scenario_name)
    return JSONResponse(content=result)

@app.post("/api/reset")
async def api_reset_endpoint():
    """Resets SQLite database and devices to clean demonstration state."""
    reset_db()
    state = state_manager.get_system_state()
    await state_manager.broadcast_event("state_sync", state)
    return JSONResponse(content={"status": "reset_complete", "state": state})

@app.post("/api/device/{device_id}/action")
async def api_device_action(device_id: str, request: Request):
    """Allows manual UI overrides and interactive testing for judges."""
    data = await request.json()
    action = data.get("action")
    
    if device_id == "ring_doorbell":
        if action == "toggle_lock":
            res = execute_tool("ring_grant_access", {"duration_seconds": 30, "reason": "Manual operator override from Alexa+ UI"})
            return JSONResponse(content=res)
    elif device_id == "bee_wearable":
        if action == "sync_telemetry":
            res = execute_tool("bee_get_wearable_telemetry", {})
            return JSONResponse(content=res)
    elif device_id == "fire_tv":
        if action == "refresh_canvas":
            res = execute_tool("firetv_push_canvas_card", {
                "card_type": "status",
                "headline": "Fire TV Canvas Refreshed",
                "body": "System running at 60 FPS on Vega OS simulator engine."
            })
            return JSONResponse(content=res)

    return JSONResponse(content={"status": "executed", "device_id": device_id, "action": action})

@app.get("/api/mcp-logs")
async def api_mcp_logs():
    """Returns protocol inspector logs for real-time verification."""
    return JSONResponse(content=state_manager.protocol_logs)

@app.get("/api/events")
async def api_events_sse(request: Request):
    """Web UI EventSource stream for zero-latency live updates."""
    async def event_stream():
        q = await state_manager.subscribe()
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield f"event: message\ndata: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            state_manager.unsubscribe(q)

    return StreamingResponse(event_stream(), media_type="text/event-stream")

# Mount static files & web simulator
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def root_index():
    index_file = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Aetheris Omni-Agent is running</h1>")

# Serve other web simulator assets (app.js, style.css)
@app.get("/style.css")
async def get_css():
    css_file = os.path.join(WEB_DIR, "style.css")
    with open(css_file, "r", encoding="utf-8") as f:
        return Response(content=f.read(), media_type="text/css")

@app.get("/app.js")
async def get_js():
    js_file = os.path.join(WEB_DIR, "app.js")
    with open(js_file, "r", encoding="utf-8") as f:
        return Response(content=f.read(), media_type="application/javascript")

if __name__ == "__main__":
    import uvicorn
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("\n" + "="*70)
    print("[*] AETHERIS OMNI-AGENT MCP SERVER INITIALIZED")
    print("[*] MCP Spec 2025-11-25 Endpoint: http://localhost:8000/mcp")
    print("[*] Alexa+ Web Simulator & Studio: http://localhost:8000")
    print("="*70 + "\n")
    uvicorn.run("mcp_server.server:app", host="0.0.0.0", port=8000, reload=True)

