"""
LLM Client - Unified interface for multiple LLM providers.
Supports OpenAI, Anthropic, Google, and Ollama via LiteLLM.
"""
import logging
from typing import List, Dict, Any, Optional
from src.core.config import config

logger = logging.getLogger("LLM")


class LLMClient:
    """Unified LLM client using LiteLLM."""
    
    def __init__(self):
        """Initialize LLM client."""
        self.provider = config.get("llm.provider", "ollama")
        self.model = config.get("llm.model", "llama3.2-vision")
        self.api_key = config.get("llm.api_key", "")
        self.base_url = config.get("llm.base_url", "http://localhost:11434")
        
        self._init_client()
    
    def _init_client(self):
        """Initialize the LLM client."""
        try:
            import litellm
            self.litellm = litellm
            
            # Configure based on provider
            if self.provider == "ollama":
                self.model_name = f"ollama/{self.model}"
                self.litellm.api_base = self.base_url
                logger.info(f"LLM initialized: Ollama ({self.model}) at {self.base_url}")
                
            elif self.provider == "openai":
                self.model_name = self.model or "gpt-4o"
                if self.api_key:
                    self.litellm.openai_key = self.api_key
                logger.info(f"LLM initialized: OpenAI ({self.model_name})")
                
            elif self.provider == "anthropic":
                self.model_name = self.model or "claude-3-5-sonnet-20241022"
                if self.api_key:
                    self.litellm.anthropic_key = self.api_key
                logger.info(f"LLM initialized: Anthropic ({self.model_name})")
                
            elif self.provider == "google":
                self.model_name = f"gemini/{self.model or 'gemini-1.5-pro'}"
                if self.api_key:
                    self.litellm.gemini_key = self.api_key
                logger.info(f"LLM initialized: Google ({self.model_name})")
            
            else:
                logger.warning(f"Unknown provider: {self.provider}, defaulting to Ollama")
                self.model_name = f"ollama/{self.model}"
                
        except ImportError:
            logger.error("litellm not installed. Install with: pip install litellm")
            self.litellm = None
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Send a chat completion request.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters for the API
            
        Returns:
            Response text from the model
        """
        if not self.litellm:
            logger.error("LiteLLM not available")
            return ""
        
        try:
            logger.info(f"Sending chat request to {self.provider}")
            
            response = self.litellm.completion(
                model=self.model_name,
                messages=messages,
                **kwargs
            )
            
            content = response.choices[0].message.content
            logger.info(f"Received response: {content[:100]}...")
            
            return content
            
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            return f"Error: {str(e)}"
    
    def simple_prompt(self, prompt: str, system_message: Optional[str] = None) -> str:
        """
        Send a simple prompt to the model.
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            
        Returns:
            Response text
        """
        messages = []
        
        if system_message:
            messages.append({
                "role": "system",
                "content": system_message
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        return self.chat(messages)
    
    def is_available(self) -> bool:
        """Check if LLM client is available."""
        return self.litellm is not None


# Global LLM client instance
llm_client = LLMClient()
