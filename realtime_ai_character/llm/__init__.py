import os
from functools import cache

from dotenv import load_dotenv
from langchain.chat_models.base import BaseChatModel

from realtime_ai_character.llm.base import LLM


load_dotenv()


def get_llm(model="gpt-4o") -> LLM:
    model = os.getenv("LLM_MODEL_USE", model)

    if model.startswith("gpt"):
        from realtime_ai_character.llm.openai_llm import OpenaiLlm

        return OpenaiLlm(model=model)
    elif model.startswith("claude"):
        from realtime_ai_character.llm.anthropic_llm import AnthropicLlm

        return AnthropicLlm(model=model)
    elif "localhost" in model:
        # Currently use llama2-wrapper to run local llama models
        local_llm_url = os.getenv("LOCAL_LLM_URL", "")
        if local_llm_url:
            from realtime_ai_character.llm.local_llm import LocalLlm

            return LocalLlm(url=local_llm_url)
        else:
            raise ValueError("LOCAL_LLM_URL not set")
    elif "llama" in model:
        # Currently use Anyscale to support llama models
        from realtime_ai_character.llm.anyscale_llm import AnysacleLlm

        return AnysacleLlm(model=model)
    else:
        raise ValueError(f"Invalid llm model: {model}")


def get_chat_model(model="gpt-4o") -> BaseChatModel:
    model = os.getenv("LLM_MODEL_USE", model)

    if model.startswith("gpt"):
        from realtime_ai_character.llm.openai_llm import OpenaiLlm

        return OpenaiLlm(model=model).chat_open_ai
    elif model.startswith("claude"):
        from realtime_ai_character.llm.anthropic_llm import AnthropicLlm

        return AnthropicLlm(model=model).chat_anthropic
    elif "localhost" in model:
        # Currently use llama2-wrapper to run local llama models
        local_llm_url = os.getenv("LOCAL_LLM_URL", "")
        if local_llm_url:
            from realtime_ai_character.llm.local_llm import LocalLlm

            return LocalLlm(url=local_llm_url).chat_open_ai
        else:
            raise ValueError("LOCAL_LLM_URL not set")
    elif "llama" in model:
        # Currently use Anyscale to support llama models
        from realtime_ai_character.llm.anyscale_llm import AnysacleLlm

        return AnysacleLlm(model=model).chat_open_ai
    else:
        raise ValueError(f"Invalid llm model: {model}")


@cache
def get_chat_model_from_env() -> BaseChatModel:
    """GPT-4 has the best performance while generating system prompt."""

    if os.getenv("OPENAI_API_KEY"):
        return get_chat_model(model="gpt-4o")
    elif os.getenv("LOCAL_LLM_URL"):
        return get_chat_model(model="localhost")

    raise ValueError("No llm api key found in env")
