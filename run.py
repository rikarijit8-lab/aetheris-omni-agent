"""
Aetheris Omni-Agent: Standalone Runner Entrypoint
Launch with: python run.py
"""

import sys
import uvicorn

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 AETHERIS OMNI-AGENT RUNNER")
    print("📍 MCP Spec 2025-11-25 Endpoint: http://localhost:8000/mcp")
    print("🖥️  Alexa+ Web Simulator & Studio: http://localhost:8000")
    print("="*70 + "\n")
    uvicorn.run("mcp_server.server:app", host="0.0.0.0", port=8000, reload=False)

