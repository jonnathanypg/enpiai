"""
LLM Service (SkillAdapter) - Unified gateway for multiple LLM providers.
Wraps OpenAI, Anthropic, and Google Gemini behind a single interface.

Migration Path: This adapter is designed to be swapped with private/decentralized
models in the future. No direct AI API calls should be made outside this service.
"""
import logging
from flask import current_app

logger = logging.getLogger(__name__)


class LLMService:
    """
    SkillAdapter — Unified LLM interface.
    Usage:
        llm = LLMService()
        response = llm.generate("Hello!", provider='openai', model='gpt-4')
    """

    def __init__(self):
        self._openai_client = None
        self._anthropic_client = None
        self._gemini_model = None

    # --- Lazy initialization ---
    def _get_openai(self):
        if self._openai_client is None:
            try:
                import openai
                api_key = current_app.config.get('OPENAI_API_KEY', '')
                if api_key:
                    self._openai_client = openai.OpenAI(api_key=api_key)
                else:
                    logger.warning("OpenAI API key not configured")
            except ImportError:
                logger.error("openai package not installed")
        return self._openai_client

    def _get_anthropic(self):
        if self._anthropic_client is None:
            try:
                import anthropic
                api_key = current_app.config.get('ANTHROPIC_API_KEY', '')
                if api_key:
                    self._anthropic_client = anthropic.Anthropic(api_key=api_key)
                else:
                    logger.warning("Anthropic API key not configured")
            except ImportError:
                logger.error("anthropic package not installed")
        return self._anthropic_client

    def _get_gemini(self, model_name='gemini-pro'):
        if self._gemini_model is None:
            try:
                import google.generativeai as genai
                api_key = current_app.config.get('GOOGLE_AI_API_KEY', '')
                if api_key:
                    genai.configure(api_key=api_key)
                    self._gemini_model = genai.GenerativeModel(model_name)
                else:
                    logger.warning("Google AI API key not configured")
            except ImportError:
                logger.error("google-generativeai package not installed")
        return self._gemini_model

    # --- Failover Order ---
    FAILOVER_ORDER = ['openai', 'gemini', 'anthropic']

    # --- Main API ---
    def generate(self, prompt, provider=None, model=None, system_prompt=None,
                 messages=None, temperature=1.0, max_tokens=2000):
        """
        Generate a response from an LLM provider.
        If the primary provider fails AND failover is enabled in PlatformConfig,
        automatically tries the next available one.

        Args:
            prompt: The user message/prompt
            provider: 'openai', 'anthropic', or 'gemini' (defaults to config)
            model: Model name (defaults to config)
            system_prompt: Optional system message
            messages: Optional full message history (overrides prompt)
            temperature: Creativity (0.0-1.0)
            max_tokens: Max response length

        Returns:
            str: The generated response text
        """
        primary_provider = provider or current_app.config.get('DEFAULT_LLM_PROVIDER', 'openai')
        primary_model = model or current_app.config.get('DEFAULT_LLM_MODEL', 'gpt-5-nano')

        # --- Phase 11: Check global failover toggle ---
        failover_enabled = True  # Default: enabled
        try:
            from models.platform_config import PlatformConfig
            config = PlatformConfig.get_config()
            failover_enabled = config.enable_failover
        except Exception:
            pass  # If config table doesn't exist yet, default to enabled

        if failover_enabled:
            providers_to_try = [primary_provider] + [p for p in self.FAILOVER_ORDER if p != primary_provider]
        else:
            providers_to_try = [primary_provider]

        last_error = None
        for p in providers_to_try:
            try:
                m = primary_model if p == primary_provider else self._default_model_for(p)
                if p == 'openai':
                    return self._generate_openai(prompt, m, system_prompt, messages, temperature, max_tokens)
                elif p == 'anthropic':
                    return self._generate_anthropic(prompt, m, system_prompt, messages, temperature, max_tokens)
                elif p == 'gemini':
                    return self._generate_gemini(prompt, m, system_prompt, messages, temperature, max_tokens)
            except Exception as e:
                last_error = e
                logger.warning(f"LLM failover: {p}/{m} failed ({e}), trying next...")
                continue

        logger.error(f"All LLM providers failed. Last error: {last_error}")
        raise RuntimeError(f"All LLM providers exhausted. Last error: {last_error}")

    def _default_model_for(self, provider: str) -> str:
        """Return a sensible default model for failover targets."""
        defaults = {
            'openai': 'gpt-5-nano',
            'anthropic': 'claude-3-5-sonnet-20241022',
            'gemini': 'gemini-1.5-flash',
        }
        return defaults.get(provider, 'gpt-5-nano')

    def _generate_openai(self, prompt, model, system_prompt, messages, temperature, max_tokens):
        """Generate using OpenAI API"""
        client = self._get_openai()
        if not client:
            raise RuntimeError("OpenAI client not available")

        # OpenAI O1/O3 and potentially custom 'gpt-5' placeholders
        # require max_completion_tokens instead of max_tokens.
        # They also often don't support temperature or system roles (preferring developer).
        model_lower = model.lower()
        is_o_model = any(m in model_lower for m in ['o1', 'o3', 'gpt-5'])

        if messages is None:
            messages = []
            if system_prompt:
                role = "developer" if is_o_model else "system"
                messages.append({"role": role, "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

        kwargs = {
            "model": model,
            "messages": messages,
        }

        if is_o_model:
            kwargs["max_completion_tokens"] = max_tokens
            # O-series models usually don't support temperature or only allow 1.0.
            # We omit it to use the model's default "reasoning" behavior.
        else:
            kwargs["max_tokens"] = max_tokens
            kwargs["temperature"] = temperature

        response = client.chat.completions.create(**kwargs)
        
        # Log essential metadata for debugging empty responses
        usage = getattr(response, 'usage', None)
        finish_reason = response.choices[0].finish_reason if response.choices else "unknown"
        content = response.choices[0].message.content if response.choices else None
        
        logger.info(f"OpenAI response: model={model}, finish_reason={finish_reason}, usage={usage}")
        
        if not content and is_o_model:
            logger.warning(f"O-model returned empty content. This usually means the reasoning budget consumed all tokens or the prompt was filtered.")
            
        return content or ""

    def _generate_anthropic(self, prompt, model, system_prompt, messages, temperature, max_tokens):
        """Generate using Anthropic API"""
        client = self._get_anthropic()
        if not client:
            raise RuntimeError("Anthropic client not available")

        if messages is None:
            messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": model or "claude-3-sonnet-20240229",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = client.messages.create(**kwargs)
        return response.content[0].text

    def _generate_gemini(self, prompt, model, system_prompt, messages, temperature, max_tokens):
        """Generate using Google Gemini API"""
        gemini = self._get_gemini(model or 'gemini-pro')
        if not gemini:
            raise RuntimeError("Gemini model not available")

        full_prompt = ""
        if system_prompt:
            full_prompt += f"{system_prompt}\n\n"
        full_prompt += prompt

        response = gemini.generate_content(
            full_prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
        )
        return response.text

    def get_embedding(self, text, model="text-embedding-3-small"):
        """Get text embedding using OpenAI (used for RAG)"""
        client = self._get_openai()
        if not client:
            raise RuntimeError("OpenAI client not available for embeddings")

        response = client.embeddings.create(
            input=text,
            model=model
        )
        return response.data[0].embedding


# Singleton instance
llm_service = LLMService()
