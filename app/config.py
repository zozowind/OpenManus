import threading
import tomllib
from pathlib import Path
from typing import Dict, List, Optional, Any, Set

from pydantic import BaseModel, Field


def get_project_root() -> Path:
    """Get the project root directory"""
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = get_project_root()
WORKSPACE_ROOT = PROJECT_ROOT / "workspace"


class LLMSettings(BaseModel):
    model: str = Field(..., description="Model name")
    base_url: str = Field(..., description="API base URL")
    api_key: str = Field(..., description="API key")
    max_tokens: int = Field(4096, description="Maximum number of tokens per request")
    temperature: float = Field(1.0, description="Sampling temperature")
    api_type: str = Field(..., description="AzureOpenai or Openai")
    api_version: str = Field(..., description="Azure Openai version if AzureOpenai")


class BaseToolSettings(BaseModel):
    """Base configuration for all tools"""
    name: str = Field(..., description="Tool name")


class ToolSettings(BaseToolSettings):
    """Tool specific configuration that can contain any additional settings"""
    config: Dict[str, Any] = Field(default_factory=dict, description="Tool specific configuration")


class ToolConfig(BaseModel):
    """Global tool configuration"""
    tools: Dict[str, ToolSettings] = Field(default_factory=dict, description="Tool specific configurations")


class AgentSettings(BaseModel):
    """Base configuration for all agents"""
    available_tools: List[str] = Field(default_factory=list, description="List of tools available to this agent")
    system_prompt: Optional[str] = Field(None, description="System prompt for the agent")
    next_step_prompt: Optional[str] = Field(None, description="Next step prompt for the agent")
    max_steps: Optional[int] = Field(None, description="Maximum number of steps for the agent")
    config: Dict[str, Any] = Field(default_factory=dict, description="Additional agent-specific configuration")


class AgentConfig(BaseModel):
    """Global agent configuration"""
    agents: Dict[str, AgentSettings] = Field(default_factory=dict, description="Agent specific configurations")


class AppConfig(BaseModel):
    llm: Dict[str, LLMSettings]
    tool: ToolConfig
    agent: AgentConfig


class Config:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._config = None
                    self._load_initial_config()
                    self._initialized = True

    @staticmethod
    def _get_config_path() -> Path:
        root = PROJECT_ROOT
        config_path = root / "config" / "config.toml"
        if config_path.exists():
            return config_path
        example_path = root / "config" / "config.example.toml"
        if example_path.exists():
            return example_path
        raise FileNotFoundError("No configuration file found in config directory")

    def _load_config(self) -> dict:
        config_path = self._get_config_path()
        with config_path.open("rb") as f:
            return tomllib.load(f)

    def _load_initial_config(self):
        raw_config = self._load_config()
        
        # Load LLM configurations
        base_llm = raw_config.get("llm", {})
        llm_overrides = {
            k: v for k, v in raw_config.get("llm", {}).items() if isinstance(v, dict)
        }

        default_settings = {
            "model": base_llm.get("model"),
            "base_url": base_llm.get("base_url"),
            "api_key": base_llm.get("api_key"),
            "max_tokens": base_llm.get("max_tokens", 4096),
            "temperature": base_llm.get("temperature", 1.0),
            "api_type": base_llm.get("api_type", ""),
            "api_version": base_llm.get("api_version", ""),
        }

        # Load tool configurations
        tool_config = raw_config.get("tool", {})   
        tools_config = {}
        raw_tools_config = tool_config.get("tools", {})
        for tool_name, tool_settings in raw_tools_config.items():
            tool_settings = tool_settings or {}
            tools_config[tool_name] = ToolSettings(
                name=tool_name,
                config=tool_settings.get("config", {})
            )

        # Load agent configurations
        agent_config = raw_config.get("agent", {})
        agents_config = {}
        raw_agents_config = agent_config.get("agents", {})
        for agent_name, agent_settings in raw_agents_config.items():
            agent_settings = agent_settings or {}
            agents_config[agent_name] = AgentSettings(
                available_tools=agent_settings.get("available_tools", []),
                system_prompt=agent_settings.get("system_prompt"),
                next_step_prompt=agent_settings.get("next_step_prompt"),
                max_steps=agent_settings.get("max_steps"),
                config=agent_settings.get("config", {})
            )

        config_dict = {
            "llm": {
                "default": default_settings,
                **{
                    name: {**default_settings, **override_config}
                    for name, override_config in llm_overrides.items()
                },
            },
            "tool": {
                "tools": tools_config
            },
            "agent": {
                "agents": agents_config
            }
        }

        self._config = AppConfig(**config_dict)

    @property
    def llm(self) -> Dict[str, LLMSettings]:
        return self._config.llm

    @property
    def tool(self) -> ToolConfig:
        return self._config.tool

    @property
    def agent(self) -> AgentConfig:
        return self._config.agent

    def get_tool_config(self, tool_name: str) -> Optional[ToolSettings]:
        """Get configuration for a specific tool"""
        return self.tool.tools.get(tool_name)

    def get_agent_config(self, agent_name: str) -> Optional[AgentSettings]:
        """Get configuration for a specific agent"""
        return self.agent.agents.get(agent_name)


config = Config()
