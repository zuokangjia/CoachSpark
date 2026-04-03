from langchain_openai import ChatOpenAI

from app.config import settings

_llm_instance = None


def get_llm() -> ChatOpenAI:
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = ChatOpenAI(
            model=settings.openai_model,
            openai_api_key=settings.openai_api_key,
            openai_api_base=settings.openai_base_url,
            temperature=0.3,
        )
    return _llm_instance
