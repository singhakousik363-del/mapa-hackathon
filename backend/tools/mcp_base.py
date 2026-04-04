from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass

@dataclass
class ToolResult:
    success: bool
    data: Any
    message: str
    tool_name: str

class MCPTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...
    @property
    @abstractmethod
    def description(self) -> str: ...
    @property
    @abstractmethod
    def schema(self) -> dict: ...
    @abstractmethod
    async def call(self, params: dict) -> ToolResult: ...

class MCPRegistry:
    def __init__(self):
        self._tools: dict[str, MCPTool] = {}
    def register(self, tool: MCPTool) -> None:
        self._tools[tool.name] = tool
    def get(self, name: str) -> MCPTool | None:
        return self._tools.get(name)
    def list_tools(self) -> list[dict]:
        return [{"name": t.name, "description": t.description} for t in self._tools.values()]
    def tool_manifest(self) -> str:
        lines = ["Available MCP tools:"]
        for t in self._tools.values():
            lines.append(f"  - {t.name}: {t.description}")
        return "\n".join(lines)
