"""
JSON parsing utilities for LLM outputs
Provides robust multi-layer parsing with fallbacks for various LLM output formats
"""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import AIMessage


def clean_llm_response(content: str) -> str:
    if not content:
        return ""
    content = re.sub(
        r"<start_of_thought>.*?</end_of_thought>",
        "",
        content,
        flags=re.DOTALL | re.IGNORECASE,
    )
    content = re.sub(r"<think>.*?", "", content, flags=re.DOTALL | re.IGNORECASE)
    return content.strip()


def extract_code_fence(content: str) -> str | None:
    if content.startswith("```"):
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
        if match:
            return match.group(1).strip()
    return None


def safe_parse_json(raw_output: Any, default_value: Any = None) -> Any:
    """
    安全解析 JSON，提供多层兜底策略

    Args:
        raw_output: LLM 的原始输出（可能是字符串、AIMessage 或已解析的对象）
        default_value: 解析失败时的默认返回值

    Returns:
        解析后的 Python 对象，或 default_value
    """
    if isinstance(raw_output, (dict, list)):
        return raw_output

    if isinstance(raw_output, AIMessage):
        text_content = raw_output.content
    elif isinstance(raw_output, str):
        text_content = raw_output
    else:
        return default_value

    text_content = clean_llm_response(text_content)

    try:
        return json.loads(text_content)
    except (json.JSONDecodeError, TypeError):
        pass

    cleaned = text_content.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        pass

    json_pattern = (
        r"(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}|\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\])"
    )
    matches = re.findall(json_pattern, cleaned, re.DOTALL)

    if matches:
        for match in matches:
            try:
                return json.loads(match)
            except (json.JSONDecodeError, TypeError):
                continue

    try:
        fixed = cleaned.replace("'", '"')
        fixed = re.sub(r",\s*([}\]])", r"\1", fixed)
        return json.loads(fixed)
    except (json.JSONDecodeError, TypeError):
        pass

    return default_value


def parse_feedback_text(content: str) -> dict[str, Any]:
    default_result = {
        "scores": {"completeness": 10, "accuracy": 10, "clarity": 10, "depth": 10},
        "total_score": 50,
        "feedback": content[:200] if content else "系统无法解析评估结果",
        "improvement_suggestions": ["请稍后重新提交获取完整评估"],
    }

    if not content:
        return default_result

    scores = {"completeness": 10, "accuracy": 10, "clarity": 10, "depth": 10}
    total_score = 50

    score_match = re.search(r"[综总]分[：:]\s*(\d+)", content)
    if score_match:
        total_score = max(0, min(100, int(score_match.group(1))))

    score_patterns = [
        (r"完整性[：:]\s*(\d+)", "completeness"),
        (r"准确[性度][：:]\s*(\d+)", "accuracy"),
        (r"逻辑[清晰度][：:]\s*(\d+)", "clarity"),
        (r"深度[与广度][：:]\s*(\d+)", "depth"),
    ]

    for pattern, key in score_patterns:
        match = re.search(pattern, content)
        if match:
            scores[key] = max(1, min(20, int(match.group(1))))

    return {
        "scores": scores,
        "total_score": total_score,
        "feedback": content[:200] if content else "系统无法解析评估结果",
        "improvement_suggestions": ["请稍后重新提交获取完整评估"],
    }


async def call_llm_with_retries(
    llm,
    prompt: str,
    max_retries: int = 2,
    parse_json: bool = True,
) -> tuple[Any | None, str]:
    """
    调用 LLM 并进行解析，支持重试

    Args:
        llm: LLM 实例
        prompt: 提示词
        max_retries: 最大重试次数
        parse_json: 是否解析为 JSON

    Returns:
        (解析结果或原始文本, 最后一个原始响应内容)
    """
    last_content = ""

    for attempt in range(max_retries + 1):
        try:
            response = await llm.ainvoke(prompt)
            content = response.content.strip() if response.content else ""
            last_content = content

            if not content:
                continue

            if parse_json:
                result = safe_parse_json(content)
                if result is not None:
                    return result, content

                if attempt < max_retries:
                    prompt = prompt + "\n\n请只返回 JSON，不要有其他文字。"
                    continue
            else:
                return content, content

        except Exception:
            if attempt < max_retries:
                continue

    return None, last_content
