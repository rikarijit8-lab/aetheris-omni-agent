# 📋 Aetheris Omni-Agent: Official Hackathon Friction Logs
> **Amazon Developer Hackathon: Build, Ship, Shape 2026**  
> *Submitted for the 10% Judging Bonus as designated in the Official Rules.*

---

### Friction Log #1: MCP Spec 2025-11-25 Streamable HTTP SSE Keepalive Disconnect
- **Specific Task Attempted**:  
  Implementing a resilient Server-Sent Events (SSE) stream over `POST /mcp` and `GET /mcp` following the MCP Spec 2025-11-25 over Streamable HTTP for real-time tool event broadcasting to Alexa+.
- **Steps Taken**:  
  1. Configured FastAPI `StreamingResponse` on `GET /mcp` with `media_type="text/event-stream"`.
  2. Initiated the connection with `notifications/stream_connected`.
  3. Streamed asynchronous tool call events from `asyncio.Queue`.
- **Expected Result**:  
  Persistent HTTP/2 or HTTP/1.1 stream maintaining long-lived connectivity without client socket timeouts.
- **Actual Result**:  
  Proxy servers, corporate firewalls, and client agents closed the connection abruptly after 15 to 30 seconds of inactivity without a standard TCP reset, triggering client reconnection loops.
- **Severity Rating**: **Important (High Developer Friction)**
- **Workaround Used**:  
  Implemented a non-blocking 15-second heartbeat loop (`yield ": ping\n\n"` or `: keepalive`) in the asynchronous generator wrapped in `asyncio.wait_for()`. Handled client disconnection gracefully via `request.is_disconnected()`.
- **Actionable Suggestion for Amazon MCP Team**:  
  The MCP 2025-11-25 Streamable HTTP specification should explicitly formalize mandatory ping/pong heartbeat frames (e.g., standardizing `ping` JSON-RPC notifications or SSE comments every 15 seconds) in the reference SDKs.

---

### Friction Log #2: AWS Bedrock Converse API Strict JSON Schema Validation
- **Specific Task Attempted**:  
  Passing MCP tool schemas directly to the AWS Bedrock Converse API (`toolConfig.tools[].toolSpec.inputSchema.json`) using Anthropic Claude 3.5 Sonnet (`anthropic.claude-3-5-sonnet-20241022-v2:0`).
- **Steps Taken**:  
  1. Exported MCP tools with draft 2020-12 JSON Schema (`type: "object"`, optional properties).
  2. Formatted tools into Bedrock Converse API `toolSpec` format.
  3. Called `bedrock_client.converse(..., toolConfig={"tools": tools})`.
- **Expected Result**:  
  Bedrock accepts JSON schema objects where `properties` is empty or optional properties omit default values.
- **Actual Result**:  
  Bedrock Converse API returned `ValidationException: Expected object with properties` whenever a tool took no required arguments (e.g., `ring_inspect_doorbell` or `bee_get_wearable_telemetry` with `{}`).
- **Severity Rating**: **Critical (Blocks Bedrock Agent Runtime)**
- **Workaround Used**:  
  Created an input schema transformer that ensures an empty or optional schema always includes a valid empty `properties: {}` dictionary and stripped unsupported JSON Schema keywords before sending payloads to AWS Bedrock.
- **Actionable Suggestion for AWS Bedrock Team**:  
  Update Bedrock's schema parser to accept zero-parameter tools natively without throwing `ValidationException`, matching the broader MCP standard where argument-free tools are common for sensors and telemetry.

---

### Friction Log #3: Ring Developer Simulator Webhook Testing & CORS
- **Specific Task Attempted**:  
  Simulating real-time Ring Video Doorbell motion events and two-way smart deadbolt actuation from a local developer environment.
- **Steps Taken**:  
  1. Set up simulated device callbacks on `http://localhost:8000/api/device/ring_doorbell/action`.
  2. Triggered motion events and unlocked the door for 60 seconds.
- **Expected Result**:  
  Ring simulator webhooks trigger local handlers cleanly or allow local sandbox test loops.
- **Actual Result**:  
  Connecting web simulators to external Ring webhooks required reverse tunneling (ngrok/Cloudflare), creating latency and certificate friction during hackathon rapid prototyping.
- **Severity Rating**: **Important**
- **Workaround Used**:  
  Built a local high-fidelity Ring Doorbell Pro simulator with bidirectional event playback, SVG snapshot rendering, and automated 60-second relock countdown timers embedded directly in the server.
- **Actionable Suggestion for Ring Developer Team**:  
  Provide a local CLI mock daemon (e.g., `ring-mock-cli`) that emits simulated WebRTC frames and webhook events locally over `ws://localhost` or `http://localhost` without requiring external tunneling.

---

### Friction Log #4: Bee Wearable AI Continuous Stream Segmentation
- **Specific Task Attempted**:  
  Ingesting continuous ambient audio notes and cognitive biometric stress indicators from the Bee Wearable AI to trigger proactive assistant interventions.
- **Steps Taken**:  
  1. Streamed telemetry snapshots containing heart rate, stress index, and spoken transcription snippets.
  2. Fed these ambient insights into the Alexa+ MCP reasoning loop.
- **Expected Result**:  
  Bee SDK provides built-in semantic threshold triggers (e.g., "fire event when stress > 75% for 3 minutes").
- **Actual Result**:  
  The developer has to manually parse raw continuous data streams and calculate rolling averages to avoid spamming the agent on transient biometric spikes.
- **Severity Rating**: **Important**
- **Workaround Used**:  
  Engineered an in-memory smoothing buffer in `state_manager.py` that computes rolling cognitive load before triggering an ambient workspace ambience shift or cross-device alert.
- **Actionable Suggestion for Bee Developer Team**:  
  Introduce an event-based "Cognitive State Trigger" webhook in the Bee Agent Skills framework that fires when specific biometric and semantic conditions are sustained.

---

### Friction Log #5: Fire TV / Vega OS Multimodal Web Canvas Rendering & Z-Index
- **Specific Task Attempted**:  
  Broadcasting interactive cards and ambient screen overlays from Alexa+ to the Fire TV / Vega OS screen while maintaining audio focus.
- **Steps Taken**:  
  1. Created a web-based ambient canvas responding to SSE updates.
  2. Dispatched visual alerts and calendar cards dynamically.
- **Expected Result**:  
  Cards render smoothly in 4K resolution with clear hierarchy and without flickering or UI jumps.
- **Actual Result**:  
  Rapid consecutive tool executions (e.g. Calendar update + 1-Click order confirmation) caused race conditions in DOM card re-renders if z-indexes and CSS transitions weren't isolated.
- **Severity Rating**: **Moderate**
- **Workaround Used**:  
  Designed dedicated MCP App container cards with decoupled DOM insertions, slide-up keyframe animations, and strict CSS grid isolation.
- **Actionable Suggestion for Fire TV & Vega OS Team**:  
  Provide an official React/Web SDK for Vega OS Ambient Canvas with built-in queueing and transition components for cross-device card pushes.

