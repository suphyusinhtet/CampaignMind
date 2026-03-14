# agents/base_agent.py
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from config.agent_config import get_agent_config, get_model_client
from typing import Optional


class CampaignMindAgent:
    """
    Base class for all CampaignMind AI agents.
    Wraps AutoGen's AssistantAgent with CampaignMind-specific configuration.
    """
    
    def __init__(self, agent_name: str, model_client: Optional[OpenAIChatCompletionClient] = None):
        """
        Initialize a CampaignMind agent.
        
        Args:
            agent_name: Name from AGENT_CONFIGS (e.g., 'brief_analyzer', 'trend_agent')
            model_client: Optional custom model client. If None, uses config default.
        """
        # Load agent configuration
        self.config = get_agent_config(agent_name)
        self.agent_name = agent_name
        
        # Get or create model client
        if model_client is None:
            model_client = get_model_client(self.config["model"])
        
        # Create the AutoGen AssistantAgent
        self.agent = AssistantAgent(
            name=self.config["name"],
            model_client=model_client,
            description=self.config["description"],
            system_message=self.config["system_message"],
        )
    
    def get_agent(self) -> AssistantAgent:
        """Get the underlying AutoGen agent."""
        return self.agent
    
    def __repr__(self) -> str:
        return f"CampaignMindAgent({self.config['name']}, model={self.config['model']})"