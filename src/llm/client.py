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
        self.model = config.get("llm.model", "llama3.2")
        self.api_key = config.get("llm.api_key", "")
        self.base_url = config.get("llm.base_url", "http://localhost:11434")
        self.active_model = self.model
        self.last_error = ""
        
        self._init_client()
    
    def _init_client(self):
        """Initialize the LLM client."""
        try:
            import litellm
            self.litellm = litellm
            
            # Configure based on provider
            if self.provider == "ollama":
                self.active_model = self._resolve_ollama_model()
                self.model_name = f"ollama/{self.active_model}"
                self.litellm.api_base = self.base_url
                logger.info(f"LLM initialized: Ollama ({self.active_model}) at {self.base_url}")
                
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

    def _get_ollama_models(self) -> List[str]:
        """Get locally available Ollama model names."""
        try:
            import requests

            url = f"{self.base_url.rstrip('/')}/api/tags"
            response = requests.get(url, timeout=3)
            response.raise_for_status()

            data = response.json()
            models = data.get("models", [])
            names = [model.get("name", "") for model in models if model.get("name")]
            return list(dict.fromkeys(names))
        except Exception as e:
            logger.warning(f"Could not query Ollama model list: {e}")
            return []

    def _resolve_ollama_model(self) -> str:
        """Resolve a usable local Ollama model, with fallback if configured model is missing."""
        available = self._get_ollama_models()
        preferred = self.model

        if preferred in available:
            return preferred

        preferred_base = preferred.split(":")[0]

        # If user configured base model without tag, prefer any installed tag variant.
        if ":" not in preferred:
            tagged_matches = [name for name in available if name.split(":")[0] == preferred]
            if tagged_matches:
                logger.warning(
                    f"Configured Ollama model '{preferred}' not found exactly. Using installed variant '{tagged_matches[0]}'."
                )
                return tagged_matches[0]

        # If user configured model with tag and base exists with other tags, pick closest base variant.
        base_matches = [name for name in available if name.split(":")[0] == preferred_base]
        if base_matches:
            logger.warning(
                f"Configured Ollama model '{preferred}' not found. Falling back to installed variant '{base_matches[0]}'."
            )
            return base_matches[0]

        fallback_order = ["llama3.2", "llama3.1", "qwen2.5", "phi3", "mistral", "llama3"]
        for candidate in fallback_order:
            exact_match = next((name for name in available if name == candidate), None)
            if exact_match:
                logger.warning(
                    f"Configured Ollama model '{preferred}' not found. Falling back to '{exact_match}'."
                )
                return exact_match

            tagged_match = next((name for name in available if name.split(":")[0] == candidate), None)
            if tagged_match:
                logger.warning(
                    f"Configured Ollama model '{preferred}' not found. Falling back to '{tagged_match}'."
                )
                return tagged_match

        if available:
            logger.warning(
                f"Configured Ollama model '{preferred}' not found. Falling back to first available model '{available[0]}'."
            )
            return available[0]

        return preferred
    
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
            self.last_error = "LiteLLM not available"
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
            error_text = str(e)

            if self.provider == "ollama" and "not found" in error_text.lower():
                fallback_model = self._resolve_ollama_model()
                if fallback_model and fallback_model != self.active_model:
                    logger.warning(f"Retrying with fallback Ollama model: {fallback_model}")
                    self.active_model = fallback_model
                    self.model_name = f"ollama/{fallback_model}"
                    try:
                        response = self.litellm.completion(
                            model=self.model_name,
                            messages=messages,
                            **kwargs
                        )
                        content = response.choices[0].message.content
                        logger.info(f"Received response with fallback model: {content[:100]}...")
                        self.last_error = ""
                        return content
                    except Exception as retry_error:
                        error_text = str(retry_error)

            self.last_error = error_text
            logger.error(f"Error in chat completion: {error_text}")

            if self.provider == "ollama" and "not found" in error_text.lower():
                return (
                    "Error: Ollama model not found. Install one with: "
                    "ollama pull llama3.2"
                )

            return f"Error: {error_text}"
    
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
