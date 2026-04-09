"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Loader2,
  Target,
  CheckCircle,
  XCircle,
  Lightbulb,
  Building2,
  Plus,
  FileText,
  User,
  Zap,
} from "lucide-react";
import { matchApi, companiesApi, resumeApi } from "@/lib/api-client";
import { cn } from "@/lib/utils";

export default function MatchPage() {
  const router = useRouter();
  const [jdText, setJdText] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [position, setPosition] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [useStoredResume, setUseStoredResume] = useState(true);
  const [hasResume, setHasResume] = useState(false);
  const [resumeLoading, setResumeLoading] = useState(true);

  useEffect(() => {
    const pending = sessionStorage.getItem("pending_company");
    if (pending) {
      try {
        const data = JSON.parse(pending);
        if (data.name) setCompanyName(data.name);
        if (data.position) setPosition(data.position);
        if (data.jd_text) setJdText(data.jd_text);
        sessionStorage.removeItem("pending_company");
      } catch {}
    }

    resumeApi.get()
      .then((res) => {
        const d = res.data;
        setHasResume(!!(d.full_name || d.skills?.length || d.work_experience?.length));
      })
      .catch(() => setHasResume(false))
      .finally(() => setResumeLoading(false));
  }, []);

  async function handleAnalyze(e: React.FormEvent) {
    e.preventDefault();
    if (!jdText.trim()) {
      setError("请粘贴岗位描述");
      return;
    }

    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const payload: any = {
        jd_text: jdText.trim(),
        use_stored_resume: useStoredResume && hasResume,
      };
      if (!useStoredResume || !hasResume) {
        setError("请先在「个人简历」页面填写你的简历信息，或在下方手动粘贴简历");
        setLoading(false);
        return;
      }
      const res = await matchApi.analyze(payload);
      setResult(res.data);
    } catch {
      setError("分析失败，请重试");
    } finally {
      setLoading(false);
    }
  }

  async function handleAddToBoard() {
    if (!companyName.trim() || !position.trim()) {
      setError("请填写公司名和岗位名");
      return;
    }
    try {
      await companiesApi.create({
        name: companyName.trim(),
        position: position.trim(),
        jd_text: jdText.trim(),
        status: "applied",
      });
      router.push("/");
    } catch {
      setError("添加失败");
    }
  }

  return (
    <div className="mx-auto max-w-4xl">
      <Link
        href="/"
        className="mb-4 inline-flex items-center gap-1 text-sm text-text-secondary hover:text-text-primary"
      >
        <ArrowLeft className="h-4 w-4" />
        返回看板
      </Link>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-text-primary">岗位匹配分析</h1>
        <p className="mt-1 text-sm text-text-secondary">
          粘贴岗位描述，AI 将基于你的简历分析匹配度、优势和差距
        </p>
      </div>

      <form onSubmit={handleAnalyze} className="mb-8 rounded-xl border border-border bg-surface p-6">
        {error && (
          <div className="mb-4 rounded-lg border border-error/50 bg-error-bg px-4 py-3 text-sm text-error-text">
            {error}
          </div>
        )}
        <div className="mb-4 flex items-center gap-2 rounded-lg bg-brand-subtle px-4 py-3 text-sm text-brand-text">
          <User className="h-4 w-4 shrink-0" />
          {resumeLoading ? (
            <span>正在加载简历信息...</span>
          ) : hasResume ? (
            <span>已关联你的简历，将自动用于匹配分析</span>
          ) : (
            <span>
              尚未填写简历，请先前往{" "}
              <Link href="/profile" className="font-medium underline">
                个人简历
              </Link>{" "}
              页面填写
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium text-text-secondary">公司名</label>
            <input
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="例如：字节跳动"
              className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-text-secondary">岗位名</label>
            <input
              value={position}
              onChange={(e) => setPosition(e.target.value)}
              placeholder="例如：前端开发工程师"
              className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted"
            />
          </div>
        </div>

        <div className="mt-4">
          <label className="mb-1 block text-sm font-medium text-text-secondary">
            岗位描述 (JD) <span className="text-error">*</span>
          </label>
          <textarea
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            rows={8}
            placeholder="粘贴完整的岗位描述..."
            className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted"
          />
        </div>

        <div className="mt-4 flex items-center justify-between">
          <label className="flex items-center gap-2 text-sm text-text-secondary">
            <input
              type="checkbox"
              checked={useStoredResume}
              onChange={(e) => setUseStoredResume(e.target.checked)}
              disabled={!hasResume}
              className="h-4 w-4 rounded border-input-border text-brand focus:ring-brand"
            />
            使用我的简历进行匹配分析
          </label>
          <button
            type="submit"
            disabled={loading || !hasResume}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand px-6 py-2.5 text-sm font-medium text-text-inverse hover:bg-brand-hover disabled:opacity-50"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
            AI 分析
          </button>
        </div>
      </form>

      {loading && (
        <div className="flex flex-col items-center justify-center py-16 text-text-muted">
          <Loader2 className="mb-3 h-8 w-8 animate-spin text-brand" />
          <p className="text-sm">AI 正在分析岗位匹配度...</p>
          <p className="mt-1 text-xs text-text-muted">可能需要 30 秒以上</p>
        </div>
      )}

      {result && (
        <div className="space-y-6">
          <MatchScoreCard
            matchPercentage={result.match_percentage}
            strengths={result.strengths || []}
            gaps={result.gaps || []}
            suggestions={result.suggestions || []}
          />

          <div className="flex items-center justify-end gap-3 rounded-xl border border-border bg-surface p-4">
            <div className="flex-1">
              <p className="text-sm text-text-secondary">
                觉得合适？添加到投递看板开始追踪
              </p>
            </div>
            <button
              onClick={handleAddToBoard}
              className="inline-flex items-center gap-1.5 rounded-lg bg-brand px-5 py-2.5 text-sm font-medium text-text-inverse hover:bg-brand-hover"
            >
              <Plus className="h-4 w-4" />
              添加到看板
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function MatchScoreCard({ matchPercentage, strengths, gaps, suggestions }: {
  matchPercentage: number;
  strengths: string[];
  gaps: string[];
  suggestions: string[];
}) {
  const scoreColor = matchPercentage >= 70
    ? "text-success"
    : matchPercentage >= 40
      ? "text-warning"
      : "text-error";
  const scoreBg = matchPercentage >= 70
    ? "from-success to-success-text"
    : matchPercentage >= 40
      ? "from-warning to-warning-text"
      : "from-error to-error-text";
  const scoreLabel = matchPercentage >= 80
    ? "高度匹配"
    : matchPercentage >= 60
      ? "较为匹配"
      : matchPercentage >= 40
        ? "部分匹配"
        : "匹配度低";

  return (
    <>
      <div className="rounded-xl border border-border bg-surface p-6">
        <div className="mb-6 flex items-center gap-6">
          <div className="relative flex h-24 w-24 shrink-0 items-center justify-center">
            <svg className="h-24 w-24 -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="42" fill="none" stroke="var(--border)" strokeWidth="8" />
              <circle
                cx="50"
                cy="50"
                r="42"
                fill="none"
                stroke="url(#scoreGradient)"
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={`${matchPercentage * 2.64} ${264 - matchPercentage * 2.64}`}
              />
              <defs>
                <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor={matchPercentage >= 70 ? "var(--success)" : matchPercentage >= 40 ? "var(--warning)" : "var(--error)"} />
                  <stop offset="100%" stopColor={matchPercentage >= 70 ? "var(--success-text)" : matchPercentage >= 40 ? "var(--warning-text)" : "var(--error-text)"} />
                </linearGradient>
              </defs>
            </svg>
            <div className="absolute flex flex-col items-center">
              <span className={cn("text-2xl font-bold", scoreColor)}>{matchPercentage}</span>
              <span className="text-[10px] text-text-muted">/ 100</span>
            </div>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-text-primary">匹配分析结果</h2>
            <p className={cn("mt-1 text-sm font-medium", scoreColor)}>{scoreLabel}</p>
            <p className="mt-1 text-xs text-text-secondary">
              基于你的简历与岗位要求的综合对比
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {strengths.length > 0 && (
          <div className="rounded-xl border border-success/30 bg-success-bg p-5">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-success-text">
              <CheckCircle className="h-4 w-4" />
              你的优势 ({strengths.length})
            </h3>
            <div className="space-y-2">
              {strengths.map((s, i) => (
                <div key={i} className="flex items-start gap-2 rounded-md bg-surface px-3 py-2 text-sm text-success-text">
                  <CheckCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-success" />
                  <span>{s}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {gaps.length > 0 && (
          <div className="rounded-xl border border-error/30 bg-error-bg p-5">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-error-text">
              <XCircle className="h-4 w-4" />
              你的差距 ({gaps.length})
            </h3>
            <div className="space-y-2">
              {gaps.map((g, i) => (
                <div key={i} className="flex items-start gap-2 rounded-md bg-surface px-3 py-2 text-sm text-error-text">
                  <XCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-error" />
                  <span>{g}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {suggestions.length > 0 && (
        <div className="rounded-xl border border-info/30 bg-info-bg p-5">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-info-text">
            <Lightbulb className="h-4 w-4" />
            投递建议 ({suggestions.length})
          </h3>
          <div className="space-y-2">
            {suggestions.map((s, i) => (
              <div key={i} className="flex items-start gap-2 rounded-md bg-surface px-3 py-2 text-sm text-info-text">
                <Lightbulb className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                <span>{s}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
