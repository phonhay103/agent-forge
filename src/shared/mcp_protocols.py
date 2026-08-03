from typing import Protocol, Any, List
from mcp import ClientSession
from mcp.types import Tool

class MCPToolWrapper:
    """
    Wrapper class around native mcp.types.Tool.
    Provides Pythonic snake_case properties and shields the core from camelCase fields.
    """
    def __init__(self, tool: Tool):
        self._tool = tool

    @property
    def name(self) -> str:
        return self._tool.name

    @property
    def description(self) -> str:
        return self._tool.description

    @property
    def input_schema(self) -> dict:
        # Gracefully handle input schema access
        return getattr(self._tool, "inputSchema", {}) or {}

    @property
    def output_schema(self) -> dict:
        # Gracefully handle output schema access
        return getattr(self._tool, "outputSchema", {}) or {}

class MCPSessionProtocol(Protocol):
    """
    Protocol for MCP Client Session using wrapped tool types.
    """
    async def list_tools(self, *args: Any, **kwargs: Any) -> List[MCPToolWrapper]:
        ...

    async def call_tool(self, name: str, arguments: dict, *args: Any, **kwargs: Any) -> Any:
        ...

class MCPClient:
    """
    Client wrapper around native mcp.ClientSession.
    Ensures a clean interface delegation without exposing unnecessary session internals.
    """
    def __init__(self, session: ClientSession):
        self._session = session

    async def list_tools(self, *args: Any, **kwargs: Any) -> List[MCPToolWrapper]:
        result = await self._session.list_tools(*args, **kwargs)
        if result and getattr(result, "tools", None):
            return [MCPToolWrapper(t) for t in result.tools]
        return []

    async def call_tool(self, name: str, arguments: dict, *args: Any, **kwargs: Any) -> Any:
        return await self._session.call_tool(name, arguments, *args, **kwargs)
