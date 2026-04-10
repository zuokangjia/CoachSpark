from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.config import settings

_llm_instance = None
_embedder_instance = None

"""
Design: LLM Client Singleton
核心思想：get_llm() / get_embedder() 采用单例模式复用 ChatOpenAI 和 OpenAIEmbeddings 实例，
避免每次调用都创建新连接。模型、温度、超时等参数统一从 settings 读取，
实现配置与代码的解耦。
"""


def get_llm() -> ChatOpenAI:
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = ChatOpenAI(
            model=settings.openai_model,
            openai_api_key=settings.openai_api_key,
            openai_api_base=settings.openai_base_url,
            temperature=0.3,
            timeout=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
        )
    return _llm_instance


def get_embedder() -> OpenAIEmbeddings:
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.embedding_api_key,
            base_url=settings.embedding_base_url,
            timeout=settings.llm_timeout_seconds,
        )
    return _embedder_instance
