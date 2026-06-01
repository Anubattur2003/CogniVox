import logging
from typing import Optional

from src.utils.config_loader import get_config, create_chat_model_from_config

# Configure a module-level logger so derived agents inherit consistent naming
logger = logging.getLogger("cogniVox")

class BaseAgent:
    """Base class for all agents.

    Provides unified configuration handling and LLM creation utilities so that
    concrete agents can focus on their specific reasoning logic.
    """

    def __init__(
        self,
        agent_name: str,
        model_name: Optional[str] = None,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: Optional[float] = None,
        base_url: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ):
        # Store basic identifiers
        self.agent_name = agent_name
        
        # Store system prompt if provided
        self.system_prompt = system_prompt

        # Configuration handles
        self.config = get_config()
        self.agent_config = self.config.get_agent_config(agent_name)

        # Runtime-level overrides (None means use config defaults)
        self.model_name = model_name
        self.provider = provider
        self.api_key = api_key
        self.temperature = temperature
        self.base_url = base_url
        self.kwargs = kwargs

        # Create an initial chat model instance
        self.llm = self._create_llm()

    def _create_llm(self):
        """Helper that delegates model construction to the config utility."""
        try:
            return create_chat_model_from_config(
                agent_name=self.agent_name,
                provider=self.provider,
                model=self.model_name,
                api_key=self.api_key,
                temperature=self.temperature,
                base_url=self.base_url,
                **self.kwargs,
            )
        except Exception as e:
            logger.error(f"Error creating LLM for {self.agent_name}: {str(e)}")
            raise

    def update_model(
        self,
        model_name: Optional[str] = None,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs,
    ):
        """Dynamically swap the underlying model/provider without reinstantiating the Agent."""
        if model_name is not None:
            self.model_name = model_name
        if provider is not None:
            self.provider = provider
        if api_key is not None:
            self.api_key = api_key

        self.kwargs.update(kwargs)
        self.llm = self._create_llm()
        logger.info(f"{self.agent_name} model updated to {self.model_name or 'default'} via provider {self.provider or 'default'}")
        return self

    def update_temperature(self, temperature: float):
        """Adjust sampling temperature and recreate the chat model."""
        self.temperature = temperature
        self.llm = self._create_llm()
        logger.info(f"{self.agent_name} temperature updated to {temperature}")
        return self 