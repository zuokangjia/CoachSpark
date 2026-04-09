import argparse
import statistics
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import settings


@dataclass
class ProbeResult:
    name: str
    ok: bool
    status_code: int | None
    duration_ms: float
    error: str = ""


def _measure_openrouter_once(timeout_seconds: int, raw_notes: str) -> ProbeResult:
    url = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": settings.openai_model,
        "temperature": 0,
        "messages": [
            {
                "role": "system",
                "content": '你是延迟探测助手。只返回严格JSON：{"ok":true,"brief":"..."}',
            },
            {
                "role": "user",
                "content": f"请将以下内容简述为一句话：{raw_notes[:600]}",
            },
        ],
        "response_format": {"type": "json_object"},
    }

    start = time.perf_counter()
    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            resp = client.post(url, headers=headers, json=payload)
        duration_ms = (time.perf_counter() - start) * 1000
        return ProbeResult(
            name="openrouter",
            ok=resp.status_code == 200,
            status_code=resp.status_code,
            duration_ms=duration_ms,
            error="" if resp.status_code == 200 else resp.text[:300],
        )
    except Exception as exc:
        duration_ms = (time.perf_counter() - start) * 1000
        return ProbeResult(
            name="openrouter",
            ok=False,
            status_code=None,
            duration_ms=duration_ms,
            error=str(exc),
        )


def _measure_review_api_once(
    api_base: str,
    timeout_seconds: int,
    raw_notes: str,
    company_id: str,
    round_num: int,
) -> ProbeResult:
    url = f"{api_base.rstrip('/')}/api/v2/review/analyze"
    payload = {
        "raw_notes": raw_notes,
        "company_name": "Latency Probe Inc",
        "position": "Backend Engineer",
        "round": round_num,
        "jd_key_points": ["系统设计", "数据库", "性能优化"],
        "company_id": company_id,
    }

    start = time.perf_counter()
    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            resp = client.post(url, json=payload)
        duration_ms = (time.perf_counter() - start) * 1000
        return ProbeResult(
            name="review_api",
            ok=resp.status_code == 200,
            status_code=resp.status_code,
            duration_ms=duration_ms,
            error="" if resp.status_code == 200 else resp.text[:500],
        )
    except Exception as exc:
        duration_ms = (time.perf_counter() - start) * 1000
        return ProbeResult(
            name="review_api",
            ok=False,
            status_code=None,
            duration_ms=duration_ms,
            error=str(exc),
        )


def _print_summary(name: str, results: list[ProbeResult]) -> None:
    durations = [r.duration_ms for r in results]
    success_count = sum(1 for r in results if r.ok)
    print(f"\n[{name}] success={success_count}/{len(results)}")
    print(
        "  min={:.1f}ms avg={:.1f}ms p50={:.1f}ms p95~={:.1f}ms max={:.1f}ms".format(
            min(durations),
            statistics.mean(durations),
            statistics.median(durations),
            sorted(durations)[max(0, int(len(durations) * 0.95) - 1)],
            max(durations),
        )
    )
    failed = [r for r in results if not r.ok]
    if failed:
        print("  failures:")
        for item in failed:
            print(
                f"    status={item.status_code} duration={item.duration_ms:.1f}ms error={item.error[:200]}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Probe OpenRouter vs /api/v2/review/analyze latency"
    )
    parser.add_argument("--api-base", default="http://localhost:8080")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--openrouter-timeout", type=int, default=70)
    parser.add_argument("--review-timeout", type=int, default=320)
    parser.add_argument("--company-id", default="")
    parser.add_argument("--round", type=int, default=1)
    parser.add_argument(
        "--notes",
        default=(
            "问题1：解释索引和B+树。回答一般。"
            "问题2：高并发下如何限流和缓存击穿。回答不完整。"
            "问题3：系统设计题，讲了分层，但缺少容量评估。"
        ),
    )
    args = parser.parse_args()

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is empty. Please configure backend/.env")

    print("=== Latency Probe ===")
    print(f"model={settings.openai_model}")
    print(f"openai_base_url={settings.openai_base_url}")
    print(f"api_base={args.api_base}")
    print(f"runs={args.runs}")

    openrouter_results: list[ProbeResult] = []
    review_results: list[ProbeResult] = []

    for i in range(args.runs):
        print(f"\nRun {i + 1}/{args.runs} ...")
        r1 = _measure_openrouter_once(args.openrouter_timeout, args.notes)
        openrouter_results.append(r1)
        print(
            f"  openrouter: ok={r1.ok} status={r1.status_code} duration={r1.duration_ms:.1f}ms"
        )

        r2 = _measure_review_api_once(
            args.api_base,
            args.review_timeout,
            args.notes,
            args.company_id,
            args.round,
        )
        review_results.append(r2)
        print(
            f"  review_api: ok={r2.ok} status={r2.status_code} duration={r2.duration_ms:.1f}ms"
        )

    _print_summary("openrouter", openrouter_results)
    _print_summary("review_api", review_results)

    openrouter_avg = statistics.mean([r.duration_ms for r in openrouter_results])
    review_avg = statistics.mean([r.duration_ms for r in review_results])
    overhead = review_avg - openrouter_avg
    print("\n[diagnosis]")
    print(f"  avg(review_api) - avg(openrouter) = {overhead:.1f}ms")
    print(
        "  If overhead is large, bottleneck is likely inside your review pipeline (graph + parsing + persistence)."
    )


if __name__ == "__main__":
    main()
