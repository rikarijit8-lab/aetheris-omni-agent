"""
Aetheris Omni-Agent: State Manager & Multi-Device Orchestration Event Hub
Maintains live device telemetry, event streams, and scenario pipelines.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Set
from .tools import (
    get_db, 
    check_schedule_conflicts, 
    reschedule_event, 
    auto_procure_supplies, 
    prepare_workspace_ambience,
    ring_inspect_doorbell,
    ring_grant_access,
    bee_get_wearable_telemetry,
    firetv_push_canvas_card,
    dispatch_cross_device_alert
)

logger = logging.getLogger("AetherisStateManager")

class StateManager:
    def __init__(self):
        # Connected SSE and WebSocket clients
        self.subscribers: Set[asyncio.Queue] = set()
        
        # Real-time Device States
        self.devices = {
            "alexa_plus": {
                "id": "alexa_plus",
                "name": "Alexa+ Omni Echo Show 15",
                "status": "ONLINE",
                "mode": "ACTIVE_LISTENING",
                "mcp_version": "2025-11-25",
                "protocol": "Streamable HTTP / SSE",
                "last_active": datetime.now().isoformat()
            },
            "ring_doorbell": {
                "id": "ring_doorbell",
                "name": "Ring Video Doorbell Pro 2 & Smart Deadbolt",
                "status": "ONLINE",
                "battery": "94%",
                "lock_status": "LOCKED",
                "camera_stream": "1080p HDR Live",
                "last_event": "Amazon Courier detected at front porch"
            },
            "bee_wearable": {
                "id": "bee_wearable",
                "name": "Bee Wearable AI Wristband",
                "status": "CONNECTED",
                "battery": "88%",
                "heart_rate": 82,
                "stress_level": 78,
                "ambient_listening": True,
                "haptic_ready": True
            },
            "fire_tv": {
                "id": "fire_tv",
                "name": "Fire TV Omni Series (Vega OS)",
                "status": "ONLINE",
                "display_mode": "Multimodal Ambient Canvas",
                "current_card": "Aetheris Ambient Studio Active",
                "resolution": "4K UHD 60fps"
            }
        }
        
        # In-memory protocol logs for the UI Protocol Inspector
        self.protocol_logs: List[Dict[str, Any]] = []

    async def subscribe(self) -> asyncio.Queue:
        """Subscribes an SSE or WebSocket client queue."""
        q = asyncio.Queue()
        self.subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        """Unsubscribes a client queue."""
        self.subscribers.discard(q)

    async def broadcast_event(self, event_type: str, data: Dict[str, Any]):
        """Broadcasts real-time events to all connected UI clients."""
        payload = {
            "event": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        dead_subscribers = []
        for q in self.subscribers:
            try:
                await q.put(payload)
            except Exception:
                dead_subscribers.append(q)
        
        for q in dead_subscribers:
            self.subscribers.discard(q)

    def log_protocol(self, direction: str, method: str, payload: Any):
        """Logs MCP JSON-RPC 2.0 messages for the web inspector."""
        entry = {
            "id": len(self.protocol_logs) + 1,
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "direction": direction, # 'INCOMING' or 'OUTGOING'
            "method": method,
            "payload": payload
        }
        self.protocol_logs.append(entry)
        if len(self.protocol_logs) > 100:
            self.protocol_logs.pop(0)

    def get_system_state(self) -> Dict[str, Any]:
        """Returns the full unified snapshot of all devices and active context."""
        conn = get_db()
        cursor = conn.cursor()
        
        # Schedule
        cursor.execute("SELECT * FROM schedule ORDER BY start_time ASC")
        schedule = [dict(r) for r in cursor.fetchall()]
        
        # Inventory
        cursor.execute("SELECT * FROM inventory")
        inventory = [dict(r) for r in cursor.fetchall()]
        
        # Orders
        cursor.execute("SELECT * FROM orders ORDER BY timestamp DESC LIMIT 5")
        orders = [dict(r) for r in cursor.fetchall()]
        
        # Ring Events
        cursor.execute("SELECT * FROM ring_events ORDER BY id DESC LIMIT 5")
        ring_events = [dict(r) for r in cursor.fetchall()]
        
        # Bee Telemetry
        cursor.execute("SELECT * FROM bee_telemetry ORDER BY id DESC LIMIT 3")
        bee_telemetry = [dict(r) for r in cursor.fetchall()]
        
        # Fire TV Canvas
        cursor.execute("SELECT * FROM firetv_canvas ORDER BY id DESC LIMIT 5")
        canvas = [dict(r) for r in cursor.fetchall()]
        
        conn.close()

        return {
            "devices": self.devices,
            "schedule": schedule,
            "inventory": inventory,
            "recent_orders": orders,
            "ring_events": ring_events,
            "bee_telemetry": bee_telemetry,
            "firetv_canvas": canvas
        }

    async def run_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """
        Executes curated high-impact scenarios demonstrating cross-device autonomous orchestration.
        Perfect for the 3-minute hackathon demo video.
        """
        if scenario_name == "resolve_calendar_conflict":
            # 1. Detect Conflict
            conflicts = check_schedule_conflicts()
            # 2. Automatically reschedule the overlapping meeting to the open slot
            resched_res = reschedule_event(2, "14:00", "15:00")
            # 3. Push update to Fire TV
            firetv_res = firetv_push_canvas_card(
                "schedule", 
                "Calendar Conflict Resolved", 
                "Shifted 'Operations & Security Sync' to 14:00 - 15:00. Executive Strategy Keynote is now unimpeded.",
                "/static/calendar_resolved.png"
            )
            # 4. Dispatch notification
            alert_res = dispatch_cross_device_alert(
                "Calendar Conflict Resolved",
                "Operations & Security Sync moved to 2:00 PM. No executive meeting collision.",
                "normal"
            )
            await self.broadcast_event("scenario_update", {
                "scenario": scenario_name,
                "message": "Auto-rescheduled overlapping meeting and synchronized Fire TV canvas."
            })
            return {
                "step1_detection": conflicts,
                "step2_resolution": resched_res,
                "step3_firetv": firetv_res,
                "step4_alert": alert_res
            }

        elif scenario_name == "courier_delivery_restock":
            # 1. Ring detects courier
            conn = get_db()
            cursor = conn.cursor()
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO ring_events (timestamp, event_type, detected_object, confidence, snapshot_url, access_granted) VALUES (?, ?, ?, ?, ?, ?)",
                           (now_str, "package_delivered", "Amazon Logistics Driver (ID: AMZN-994)", 0.99, "/static/courier_drop.jpg", 1))
            conn.commit()
            conn.close()
            
            # 2. Grant 60-second smart vestibule entry
            access_res = ring_grant_access(60, "Amazon Logistics Prime Delivery")
            # 3. Auto-procure depleted items
            procure_res = auto_procure_supplies("coffee_pods", 3)
            # 4. Push to Fire TV
            firetv_res = firetv_push_canvas_card(
                "procurement", 
                "Package Delivered & Supplies Reordered", 
                "Amazon Prime Courier verified at Ring Doorbell. 3x Nespresso Dark Roast pods auto-ordered ($85.50).",
                "/static/package_delivered.png"
            )
            await self.broadcast_event("scenario_update", {
                "scenario": scenario_name,
                "message": "Ring granted courier access; Amazon 1-Click reorder dispatched."
            })
            return {
                "step1_ring_access": access_res,
                "step2_amazon_procure": procure_res,
                "step3_firetv": firetv_res
            }

        elif scenario_name == "bee_stress_focus_ambience":
            # 1. Record high cognitive stress on Bee Wearable
            conn = get_db()
            cursor = conn.cursor()
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO bee_telemetry (timestamp, heart_rate, stress_level, ambient_memo, action_items, coaching_tip) VALUES (?, ?, ?, ?, ?, ?)",
                           (now_str, 91, 86, "High-intensity technical keynote preparation with multiple deliverables.", "Finalize MCP Spec 2025-11-25 architecture", "High stress detected. Transitioning room to Focus Mode."))
            conn.commit()
            conn.close()
            
            # 2. Adjust workspace ambience
            ambience_res = prepare_workspace_ambience("focus_presentation")
            # 3. Push relaxation card to Fire TV
            firetv_res = firetv_push_canvas_card(
                "ambience",
                "Focus Ambience Engaged",
                "Bee Wearable detected elevated stress (86%). Smart lights dialed to 5500K daylight, Ring doorbell muted.",
                "/static/focus_mode.png"
            )
            # 4. Dispatch alert
            alert_res = dispatch_cross_device_alert("Focus Mode Activated", "Bee Wearable triggered ambient optimization.", "high")
            await self.broadcast_event("scenario_update", {
                "scenario": scenario_name,
                "message": "Bee Wearable stress trigger activated workspace focus mode."
            })
            return {
                "step1_ambience": ambience_res,
                "step2_firetv": firetv_res,
                "step3_alert": alert_res
            }

        else:
            return {"error": f"Unknown scenario: {scenario_name}"}

# Global singleton
state_manager = StateManager()

