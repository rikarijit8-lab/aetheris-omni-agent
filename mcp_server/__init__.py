"""
Aetheris Omni-Agent MCP Package
Amazon Developer Hackathon (Alexa+, Ring, Bee, Fire TV & AWS Bedrock)
"""

from .server import app
from .tools import MCP_TOOL_DEFINITIONS, execute_tool
from .orchestrator_aws import agent_orchestrator
from .state_manager import state_manager

__all__ = ["app", "MCP_TOOL_DEFINITIONS", "execute_tool", "agent_orchestrator", "state_manager"]
