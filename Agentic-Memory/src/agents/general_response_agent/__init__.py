"""
General Response Agent

This agent provides direct, concise answers without complex reasoning chains.
Optimized for quick, straightforward responses to user queries.
"""

from .agent import GeneralResponseAgent
from .prompt import GENERAL_RESPONSE_PROMPT

__all__ = ["GeneralResponseAgent", "GENERAL_RESPONSE_PROMPT"] 