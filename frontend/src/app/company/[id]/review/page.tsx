"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import {
  ArrowLeft,
  Loader2,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Plus,
  Trash2,
  FileText,
  ListTodo,
  Pencil,
  TrendingUp,
  TrendingDown,
  Minus,
  Target,
  Lightbulb,
  MessageSquare,
  BookOpen,
} from "lucide-react";
import { reviewApi, interviewsApi, companiesApi } from "@/lib/api-client";
import { cn } from "@/lib/utils";

interface ReviewQuestion {
  question: string;
  your_answer_summary: string;
  score: number;
  assessment: string;
  improvement: string;
}

interface StructuredEntry {
  id: string;
  question: string;
  answer: string;
  interviewerReaction: string;
  selfFeeling: "good" | "ok" | "bad" | "";
}

const reactionLabels: Record<string, string> = {
  good: "满意",
  ok: "一般",
  bad: "不满意",
};

const reactionColors: Record<string, string> = {
  good: "bg-success-bg text-success-text border-success",
  ok: "bg-warning-bg text-warning-text border-warning",
  bad: "bg-error-bg text-error-text border-error",
};

export default function ReviewPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const id = params.id as string;

  const [mode, setMode] = useState<"free" | "structured">("free");
  const [viewMode, setViewMode] = useState<"form" | "result">("form");

  const [notes, setNotes] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [position, setPosition] = useState("");
  const [round, setRound] = useState(1);
  const [jdKeyPoints, setJdKeyPoints] = useState("");
  const [interviewDate, setInterviewDate] = useState("");
  const [interviewFormat, setInterviewFormat] = useState("");
  const [interviewerName, setInterviewerName] = useState("");
  const [existingInterviewId, setExistingInterviewId] = useState("");
  const [hasExistingReview, setHasExistingReview] = useState(false);

  const [entries, setEntries] = useState<StructuredEntry[]>([
    { id: crypto.randomUUID(), question: "", answer: "", interviewerReaction: "", selfFeeling: "" },
  ]);

  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [result, setResult] = useState<any>(null);
  const [saved, setSaved] = useState(false);
  const [persona, setPersona] = useState<any>(null);

  useEffect(() => {
    const iid = searchParams.get("interview_id");
    const r = searchParams.get("round");
    if (r) setRound(Number(r));
    if (iid) {
      setExistingInterviewId(iid);
      interviewsApi.get(id, iid).then((res) => {
        const iv = res.data;
        if (iv.interview_date) setInterviewDate(iv.interview_date);
        if (iv.format) setInterviewFormat(iv.format);
        if (iv.interviewer) setInterviewerName(iv.interviewer);
        if (iv.raw_notes) setNotes(iv.raw_notes);
        if (iv.round) setRound(iv.round);

        if (iv.ai_analysis && Object.keys(iv.ai_analysis).length > 0) {
          setResult(iv.ai_analysis);
          setHasExistingReview(true);
          setViewMode("result");
        }
      }).catch(() => {}).finally(() => setFetching(false));
    } else {
      setFetching(false);
    }

    // 加载当前画像（轻量显示用）
    personaV2Api.latest().then((res) => {
      setPersona(res.data);
    }).catch(() => {});
  }, [searchParams, id]);

  function addEntry() {
    setEntries([
      ...entries,
      { id: crypto.randomUUID(), question: "", answer: "", interviewerReaction: "", selfFeeling: "" },
    ]);
  }

  function removeEntry(entryId: string) {
    if (entries.length <= 1) return;
    setEntries(entries.filter((e) => e.id !== entryId));
  }

  function updateEntry(entryId: string, field: keyof StructuredEntry, value: string) {
    setEntries(
      entries.map((e) => (e.id === entryId ? { ...e, [field]: value } : e)),
    );
  }

  function buildRawNotes(): string {
    const parts: string[] = [];
    for (const entry of entries) {
      if (!entry.question.trim()) continue;
      parts.push(`[问题] ${entry.question}`);
      if (entry.answer.trim()) parts.push(`[我的回答] ${entry.answer}`);
      if (entry.interviewerReaction.trim())
        parts.push(`[面试官反应] ${entry.interviewerReaction}`);
      if (entry.selfFeeling)
        parts.push(`[自我感觉] ${reactionLabels[entry.selfFeeling] || entry.selfFeeling}`);
      parts.push("");
    }
    return parts.join("\n");
  }

  async function handleAnalyze(e: React.FormEvent) {
    e.preventDefault();

    const rawNotes = mode === "structured" ? buildRawNotes() : notes;
    if (!rawNotes.trim()) {
      alert(mode === "structured" ? "请至少填写一个问题" : "请填写面试笔记");
      return;
    }

    setLoading(true);
    try {
      const payload: Record<string, unknown> = {
        raw_notes: rawNotes.trim(),
        round,
        company_id: id,
      };
      if (companyName.trim()) payload.company_name = companyName.trim();
      if (position.trim()) payload.position = position.trim();
      if (jdKeyPoints.trim()) {
        payload.jd_key_points = jdKeyPoints
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean);
      }
      if (interviewDate) payload.interview_date = interviewDate;
      if (interviewFormat) payload.interview_format = interviewFormat;
      if (interviewerName.trim()) payload.interviewer = interviewerName.trim();
      if (existingInterviewId) payload.interview_id = existingInterviewId;

      const res = await reviewApi.analyze(payload);
      setResult(res.data);
      setSaved(true);
      setViewMode("result");
      setHasExistingReview(true);
    } catch {
      alert("分析失败，请重试");
    } finally {
      setLoading(false);
    }
  }

  function getScoreColor(score: number): string {
    if (score >= 8) return "bg-success-bg text-success-text";
    if (score >= 5) return "bg-warning-bg text-warning-text";
    return "bg-error-bg text-error-text";
  }

  function getScoreIcon(score: number) {
    if (score >= 8) return <CheckCircle className="h-4 w-4 text-success" />;
    if (score >= 5) return <AlertTriangle className="h-4 w-4 text-warning" />;
    return <XCircle className="h-4 w-4 text-error" />;
  }

  function getScoreLabel(score: number): string {
    if (score >= 9) return "优秀";
    if (score >= 8) return "良好";
    if (score >= 6) return "合格";
    if (score >= 4) return "不足";
    return "薄弱";
  }

  function getScoreBarWidth(score: number): string {
    return `${score * 10}%`;
  }

  if (fetching) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-text-muted" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl">
      <Link
        href={`/company/${id}`}
        className="mb-4 inline-flex items-center gap-1 text-sm text-text-secondary hover:text-text-primary"
      >
        <ArrowLeft className="h-4 w-4" />
        返回公司详情
      </Link>

      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">
            {hasExistingReview ? "复盘结果" : "面试复盘"}
          </h1>
          <p className="mt-1 text-sm text-text-secondary">
            第 {round} 轮面试{hasExistingReview ? "分析结果" : "记录与分析"}
          </p>
        </div>

        {viewMode === "form" && persona && (
          <PersonaMiniCard persona={persona} />
        )}
        {hasExistingReview && viewMode === "result" && (
          <button
            onClick={() => setViewMode("form")}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-sm font-medium text-text-secondary hover:bg-surface-secondary"
          >
            <Pencil className="h-4 w-4" />
            编辑复盘
          </button>
        )}
        {viewMode === "form" && (
          <div className="flex rounded-lg border border-border bg-surface p-0.5">
            <button
              onClick={() => setMode("free")}
              className={cn(
                "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium",
                mode === "free"
                  ? "bg-info-bg text-info-text"
                  : "text-text-secondary hover:text-text-primary",
              )}
            >
              <FileText className="h-3.5 w-3.5" />
              自由模式
            </button>
            <button
              onClick={() => setMode("structured")}
              className={cn(
                "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium",
                mode === "structured"
                  ? "bg-info-bg text-info-text"
                  : "text-text-secondary hover:text-text-primary",
              )}
            >
              <ListTodo className="h-3.5 w-3.5" />
              结构化模式
            </button>
          </div>
        )}
      </div>

      {viewMode === "form" && (
        <form onSubmit={handleAnalyze} className="mb-8 rounded-xl border border-border bg-surface p-6">
          {mode === "free" ? (
            <div className="mb-4">
              <label className="mb-1 block text-sm font-medium text-text-secondary">
                面试笔记 <span className="text-error">*</span>
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={8}
                placeholder="粘贴你的面试原始笔记..."
                className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted"
              />
            </div>
          ) : (
            <div className="space-y-4">
              {entries.map((entry, index) => (
                <div
                  key={entry.id}
                  className="rounded-lg border border-border bg-surface/50 p-4"
                >
                  <div className="mb-3 flex items-center justify-between">
                    <span className="text-sm font-medium text-text-primary">
                      问题 {index + 1}
                    </span>
                    <button
                      type="button"
                      onClick={() => removeEntry(entry.id)}
                      disabled={entries.length <= 1}
                      className="rounded-md p-1 text-text-muted hover:bg-surface-muted hover:text-error disabled:opacity-30"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <label className="mb-1 block text-xs font-medium text-text-secondary">
                        面试官问了什么 <span className="text-error">*</span>
                      </label>
                      <input
                        type="text"
                        value={entry.question}
                        onChange={(e) => updateEntry(entry.id, "question", e.target.value)}
                        placeholder="例如：解释 React diff 算法"
                        className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted"
                      />
                    </div>

                    <div>
                      <label className="mb-1 block text-xs font-medium text-text-secondary">
                        你是怎么回答的 <span className="text-error">*</span>
                      </label>
                      <textarea
                        value={entry.answer}
                        onChange={(e) => updateEntry(entry.id, "answer", e.target.value)}
                        rows={3}
                        placeholder="尽可能回忆你的回答要点..."
                        className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="mb-1 block text-xs font-medium text-text-secondary">
                          面试官反应
                        </label>
                        <input
                          type="text"
                          value={entry.interviewerReaction}
                          onChange={(e) =>
                            updateEntry(entry.id, "interviewerReaction", e.target.value)
                          }
                          placeholder="例如：追问了细节 / 没有追问"
                          className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted"
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-xs font-medium text-text-secondary">
                          自我感觉
                        </label>
                        <div className="flex gap-2">
                          {(["good", "ok", "bad"] as const).map((feeling) => (
                            <button
                              key={feeling}
                              type="button"
                              onClick={() => updateEntry(entry.id, "selfFeeling", feeling)}
                              className={cn(
                                "flex-1 rounded-lg border px-3 py-2 text-xs font-medium",
                                entry.selfFeeling === feeling
                                  ? reactionColors[feeling]
                                  : "border-border bg-surface text-text-secondary",
                              )}
                            >
                              {reactionLabels[feeling]}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}

              <button
                type="button"
                onClick={addEntry}
                className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-dashed border-border py-3 text-sm text-text-secondary hover:border-brand hover:text-brand"
              >
                <Plus className="h-4 w-4" />
                添加问题
              </button>
            </div>
          )}

          <div className="mt-4 grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-text-secondary">面试日期</label>
              <input
                type="date"
                value={interviewDate}
                onChange={(e) => setInterviewDate(e.target.value)}
                className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-text-secondary">面试形式</label>
              <select
                value={interviewFormat}
                onChange={(e) => setInterviewFormat(e.target.value)}
                className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus"
              >
                <option value="">请选择</option>
                <option value="phone">电话</option>
                <option value="video">视频</option>
                <option value="onsite">现场</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-text-secondary">面试官</label>
              <input
                type="text"
                value={interviewerName}
                onChange={(e) => setInterviewerName(e.target.value)}
                placeholder="可选"
                className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-text-secondary">轮次</label>
              <input
                type="number"
                min={1}
                value={round}
                onChange={(e) => setRound(Number(e.target.value))}
                className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-text-secondary">JD 关键点</label>
              <input
                type="text"
                value={jdKeyPoints}
                onChange={(e) => setJdKeyPoints(e.target.value)}
                placeholder="逗号分隔，可选"
                className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted"
              />
            </div>
          </div>

          <div className="mt-4 flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center gap-1.5 rounded-lg bg-brand px-6 py-2.5 text-sm font-medium text-text-inverse hover:bg-brand-hover disabled:opacity-50"
            >
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              {hasExistingReview ? "重新分析" : "AI 分析"}
            </button>
          </div>
        </form>
      )}

      {loading && (
        <div className="flex flex-col items-center justify-center py-16 text-text-muted">
          <Loader2 className="mb-3 h-8 w-8 animate-spin text-brand" />
          <p className="text-sm">AI 正在分析你的面试表现...</p>
          <p className="mt-1 text-xs text-text-muted">可能需要 30 秒以上</p>
        </div>
      )}

      {viewMode === "result" && result && (
        <div className="space-y-6">
          <ReviewResultDisplay
            result={result}
            companyId={id}
            round={round}
            saved={saved}
          />
          <DimensionImpactCard
            changes={(result as any).dimension_changes || []}
            persona={(result as any).persona_snapshot}
          />
        </div>
      )}
    </div>
  );
}

function ReviewResultDisplay({
  result,
  companyId,
  round,
  saved,
}: {
  result: any;
  companyId: string;
  round: number;
  saved: boolean;
}) {
  const questions = result.questions || [];
  const weakPoints = result.weak_points || [];
  const strongPoints = result.strong_points || [];
  const predictions = result.next_round_prediction || [];
  const signals = result.interviewer_signals || [];

  const avgScore = questions.length > 0
    ? (questions.reduce((sum: number, q: any) => sum + (q.score || 0), 0) / questions.length).toFixed(1)
    : "—";

  function getScoreColor(score: number): string {
    if (score >= 8) return "bg-success-bg text-success-text";
    if (score >= 5) return "bg-warning-bg text-warning-text";
    return "bg-error-bg text-error-text";
  }

  function getScoreIcon(score: number) {
    if (score >= 8) return <CheckCircle className="h-4 w-4 text-success" />;
    if (score >= 5) return <AlertTriangle className="h-4 w-4 text-warning" />;
    return <XCircle className="h-4 w-4 text-error" />;
  }

  function getScoreBarColor(score: number): string {
    if (score >= 8) return "bg-success";
    if (score >= 5) return "bg-warning";
    return "bg-error";
  }

  return (
    <>
      <div className="rounded-xl border border-border bg-surface p-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-text-primary">第 {round} 轮面试分析</h2>
            <p className="mt-1 text-sm text-text-secondary">AI 对你的面试表现进行了全面评估</p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-text-primary">{avgScore}</div>
            <div className="text-xs text-text-secondary">平均分 / 10</div>
          </div>
        </div>

        {questions.length > 0 && (
          <div className="space-y-4">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-text-secondary">
              <MessageSquare className="h-4 w-4" />
              问题详情 ({questions.length} 题)
            </h3>
            {questions.map((q: any, i: number) => (
              <div key={i} className="rounded-lg border border-border bg-surface/50 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-text-muted">Q{i + 1}</span>
                      <p className="text-sm font-medium text-text-primary">{q.question}</p>
                    </div>
                    {q.your_answer_summary && (
                      <p className="mt-2 text-xs text-text-secondary">
                        <span className="font-medium">你的回答：</span>
                        {q.your_answer_summary}
                      </p>
                    )}
                    <p className="mt-2 text-sm text-text-secondary">{q.assessment}</p>
                    {q.improvement && (
                      <div className="mt-2 flex items-start gap-1.5 rounded-md bg-info-bg p-2 text-sm text-info-text">
                        <Lightbulb className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                        <span>{q.improvement}</span>
                      </div>
                    )}
                  </div>
                  <div className="flex shrink-0 flex-col items-center gap-1">
                    <span className={cn("flex items-center gap-1 rounded-full px-2.5 py-1 text-sm font-semibold", getScoreColor(q.score))}>
                      {getScoreIcon(q.score)}
                      {q.score}
                    </span>
                    <span className="text-[10px] text-text-muted">{getScoreLabel(q.score)}</span>
                    <div className="mt-1 h-1.5 w-16 rounded-full bg-surface-muted">
                      <div
                        className={cn("h-full rounded-full transition-all", getScoreBarColor(q.score))}
                        style={{ width: `${q.score * 10}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {weakPoints.length > 0 && (
          <div className="rounded-xl border border-error/30 bg-error-bg p-5">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-error-text">
              <XCircle className="h-4 w-4" />
              薄弱点 ({weakPoints.length})
            </h3>
            <div className="space-y-2">
              {weakPoints.map((point: string, i: number) => (
                <div key={i} className="flex items-center gap-2 rounded-md bg-surface px-3 py-2 text-sm">
                  <TrendingDown className="h-3.5 w-3.5 shrink-0 text-error" />
                  <span className="text-error-text">{point}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {strongPoints.length > 0 && (
          <div className="rounded-xl border border-success/30 bg-success-bg p-5">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-success-text">
              <CheckCircle className="h-4 w-4" />
              优势 ({strongPoints.length})
            </h3>
            <div className="space-y-2">
              {strongPoints.map((point: string, i: number) => (
                <div key={i} className="flex items-center gap-2 rounded-md bg-surface px-3 py-2 text-sm">
                  <TrendingUp className="h-3.5 w-3.5 shrink-0 text-success" />
                  <span className="text-success-text">{point}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {predictions.length > 0 && (
        <div className="rounded-xl border border-info/30 bg-info-bg p-5">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-info-text">
            <Target className="h-4 w-4" />
            下一轮预测
          </h3>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
            {predictions.map((pred: string, i: number) => (
              <div key={i} className="flex items-center gap-2 rounded-md bg-surface px-3 py-2 text-sm text-info-text">
                <BookOpen className="h-3.5 w-3.5 shrink-0" />
                {pred}
              </div>
            ))}
          </div>
        </div>
      )}

      {signals.length > 0 && (
        <div className="rounded-xl border border-warning/30 bg-warning-bg p-5">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-warning-text">
            <AlertTriangle className="h-4 w-4" />
            面试官信号
          </h3>
          <div className="space-y-2">
            {signals.map((signal: string, i: number) => (
              <div key={i} className="flex items-start gap-2 rounded-md bg-surface px-3 py-2 text-sm text-warning-text">
                <MessageSquare className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                {signal}
              </div>
            ))}
          </div>
        </div>
      )}

      {saved && (
        <div className="rounded-xl border border-success/30 bg-success-bg p-4 text-center">
          <CheckCircle className="mx-auto mb-2 h-6 w-6 text-success" />
          <p className="text-sm font-medium text-success-text">复盘已保存</p>
          <div className="mt-3 flex justify-center gap-2">
            <Link
              href={`/company/${companyId}`}
              className="inline-flex items-center gap-1.5 rounded-lg border border-success px-4 py-2 text-sm font-medium text-success-text hover:bg-success-bg/80"
            >
              返回公司详情
            </Link>
            <Link
              href={`/company/${companyId}/prep?round=${round + 1}&weak_points=${encodeURIComponent((weakPoints || []).join(","))}`}
              className="inline-flex items-center gap-1.5 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-text-inverse hover:bg-brand-hover"
            >
              <Lightbulb className="h-4 w-4" />
              生成备战计划
            </Link>
          </div>
        </div>
      )}
    </>
  );
}

function getScoreLabel(score: number): string {
  if (score >= 9) return "优秀";
  if (score >= 8) return "良好";
  if (score >= 6) return "合格";
  if (score >= 4) return "不足";
  return "薄弱";
}

// ---------------------------------------------------------------------------
// Components: Persona Mini Card & Dimension Impact
// ---------------------------------------------------------------------------

function PersonaMiniCard({ persona }: { persona: any }) {
  const dimensions = persona?.dimensions || [];
  const topWeak = persona?.key_weaknesses || [];
  const topStrong = persona?.key_strengths || [];

  return (
    <div className="rounded-xl border border-border bg-surface p-4 text-xs">
      <div className="mb-2 flex items-center gap-1.5">
        <TrendingUp className="h-3.5 w-3.5 text-brand" />
        <span className="font-medium text-text-primary">当前画像</span>
      </div>

      {dimensions.length > 0 ? (
        <div className="space-y-1.5">
          {topWeak.slice(0, 2).map((wp: string, i: number) => (
            <div key={i} className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-error" />
              <span className="text-text-secondary">{wp}</span>
            </div>
          ))}
          {topStrong.slice(0, 1).map((sp: string, i: number) => (
            <div key={i} className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-success" />
              <span className="text-text-secondary">{sp}</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-text-muted">暂无画像数据</p>
      )}
    </div>
  );
}

function DimensionImpactCard({ changes, persona }: { changes: any[]; persona: any }) {
  if (!changes || changes.length === 0) return null;

  return (
    <div className="rounded-xl border border-brand/30 bg-brand-subtle p-5">
      <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-brand-text">
        <TrendingUp className="h-4 w-4" />
        本次复盘对画像的影响
      </h3>
      <div className="space-y-2">
        {changes.map((change: any, i: number) => {
          const delta = change.delta > 0 ? `+${change.delta}` : `${change.delta}`;
          const deltaColor = change.delta > 0 ? "text-success" : change.delta < 0 ? "text-error" : "text-text-muted";
          return (
            <div key={i} className="flex items-center justify-between rounded-md bg-surface px-3 py-2">
              <span className="text-sm text-text-primary">{change.dimension}</span>
              <div className="flex items-center gap-2">
                <span className="text-xs text-text-muted">{change.before} → {change.after}</span>
                <span className={`text-xs font-medium ${deltaColor}`}>{delta}</span>
                <span className="text-xs text-text-muted">({change.trend})</span>
              </div>
            </div>
          );
        })}
      </div>
      {persona?.headline && (
        <p className="mt-3 text-xs text-text-secondary">{persona.headline}</p>
      )}
    </div>
  );
}
