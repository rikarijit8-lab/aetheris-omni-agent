# 📝 Official Hackathon Product Feedback
> **Build, Ship, Shape: Amazon Developer Hackathon 2026**  
> *Track: Alexa+ (Primary Track) | Mini-Challenges: AWS Builder & Open Source*

---

### 1. Which developer tools, APIs, and SDKs did you use and for what?
- **Model Context Protocol (MCP Spec 2025-11-25)**: Implemented self-hosted Streamable HTTP and SSE protocol endpoints (`POST /mcp`, `GET /mcp`) to power real-time tool discovery (`tools/list`), tool invocation (`tools/call`), resource streaming (`resources/list`, `resources/read`), and prompt workflows (`prompts/list`) for Alexa+.
- **AWS Bedrock & AgentCore (Mini-Challenge)**: Utilized AWS Boto3 SDK (`bedrock-runtime`) with Anthropic Claude 3.5 Sonnet (`anthropic.claude-3-5-sonnet-20241022-v2:0`) and Amazon Nova for multi-turn conversational reasoning, dynamic tool selection, and proactive agent decision-making.
- **Ring Developer Platform & APIs**: Integrated Ring Video Doorbell live feed telemetry, courier object detection, and smart access deadbolt actuation with a 60-second temporary courier pass.
- **Bee Wearable AI Platform**: Ingested continuous ambient audio context, speech transcription memos, and biometric cognitive stress metrics (0-100% index) for on-wrist coaching and ambient home triggering.
- **Fire TV & Vega OS Multimodal Web Technologies**: Built an ambient visual canvas engine displaying dynamic MCP App cards, calendar conflict resolutions, and Amazon 1-Click receipts on the living room display.
- **FastAPI & Uvicorn**: Provided high-performance asynchronous HTTP/2 and SSE server orchestration.

---

### 2. What worked well?
- **MCP Spec 2025-11-25 Standard**: The schema structure for tools (`inputSchema` using JSON Schema) is remarkably clean and standardized. It allows seamless interoperability between Alexa+ and external backend tools.
- **AWS Bedrock Converse API**: The Converse API is leagues ahead of legacy Bedrock invocation patterns. The unified interface for system prompts, messages, and `toolConfig` makes orchestrating agentic tool loops intuitive and fast.
- **Fast Multimodal Feedback Loop**: The combination of voice output (SpeechSynthesis), visual UI cards (MCP Apps), and real-time telemetry updates provided an unprecedented level of immersion during testing.

---

### 3. What needs work?
- **Bedrock Tool Schema Edge Cases**: As documented in our Friction Logs, AWS Bedrock Converse API throws strict `ValidationException` when a tool takes no parameters unless an explicit empty `properties: {}` dictionary is present. Aligning this with MCP defaults will save countless hours for developers.
- **Streamable HTTP SSE Standardization**: Guidance on keepalive mechanisms (e.g. heartbeat ping frames) in the MCP 2025-11-25 documentation could be more prominent to prevent aggressive proxy disconnections.
- **Cross-Device Device Simulator Sandboxes**: Having an unified Amazon Developer CLI that launches local sandboxes for Echo Show, Ring, Bee, and Fire TV in a single terminal command would be revolutionary for the developer ecosystem.

---

### 4. How was your onboarding experience (getting from zero to hello world)?
- The onboarding experience was smooth. The documentation provided for MCP at `modelcontextprotocol.io` and the Amazon developer portals gave a clear foundational understanding.
- Going from "zero to hello world" on a local MCP server took under 30 minutes. The primary learning curve was bridging cross-device state between the reactive voice agent and the proactive ambient background processes.

---

### 5. Would you build with these devices and services again?
- **YES, absolutely!**  
- **Why**: Connecting Alexa+, Ring, Bee, and Fire TV together through an open standard like MCP is the holy grail of ambient computing. Instead of isolated smart home gadgets requiring manual app switching, the devices form a cohesive, proactive collective intelligence that genuinely assists human life without being intrusive.

---

### 6. Track & Mini-Challenge Declarations
- **Primary Track**: **Alexa+**  
  *Implementation*: Self-hosted MCP Server implementing MCP spec 2025-11-25 over Streamable HTTP with an accompanying simulated Alexa+ multi-modal web experience.
- **Mini-Challenge 1**: **AWS Builder**  
  *Implementation*: Integrated AWS Bedrock runtime client (`boto3`) with Anthropic Claude 3.5 Sonnet / Amazon Nova for multi-turn autonomous tool orchestration, coupled with AgentCore event routing patterns and dual-mode resilient execution.
- **Mini-Challenge 2**: **Open Source**  
  *Implementation*: Fully open-sourced under the MIT License on GitHub with complete architecture documentation, reproducible test suites, and clean commit history.
