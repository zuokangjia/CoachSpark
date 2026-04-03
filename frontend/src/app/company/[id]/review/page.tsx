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
} from "lucide-react";
import { reviewApi } from "@/lib/api-client";
import { cn } from "@/lib/utils";

interface ReviewQuestion {
  question: string;
  your_answer_summary: string;
  score: number;
  assessment: string;
  improvement: string;
}

interface ReviewResult {
  questions?: ReviewQuestion[];
  weak_points?: string[];
  strong_points?: string[];
  next_round_prediction?: string[];
  interviewer_signals?: string[];
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
  good: "bg-green-100 text-green-700 border-green-200",
  ok: "bg-yellow-100 text-yellow-700 border-yellow-200",
  bad: "bg-red-100 text-red-700 border-red-200",
};

export default function ReviewPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const id = params.id as string;

  const [mode, setMode] = useState<"free" | "structured">("free");

  const [notes, setNotes] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [position, setPosition] = useState("");
  const [round, setRound] = useState(1);
  const [jdKeyPoints, setJdKeyPoints] = useState("");
  const [interviewDate, setInterviewDate] = useState("");
  const [interviewFormat, setInterviewFormat] = useState("");
  const [interviewerName, setInterviewerName] = useState("");
  const [existingInterviewId, setExistingInterviewId] = useState("");

  const [entries, setEntries] = useState<StructuredEntry[]>([
    { id: crypto.randomUUID(), question: "", answer: "", interviewerReaction: "", selfFeeling: "" },
  ]);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ReviewResult | null>(null);

  useEffect(() => {
    const iid = searchParams.get("interview_id");
    const r = searchParams.get("round");
    if (iid) setExistingInterviewId(iid);
    if (r) setRound(Number(r));
  }, [searchParams]);

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
    } catch {
      alert("分析失败，请重试");
    } finally {
      setLoading(false);
    }
  }

  function getScoreColor(score: number): string {
    if (score >= 8) return "bg-green-100 text-green-700";
    if (score >= 5) return "bg-yellow-100 text-yellow-700";
    return "bg-red-100 text-red-700";
  }

  function getScoreIcon(score: number) {
    if (score >= 8) return <CheckCircle className="h-4 w-4 text-green-600" />;
    if (score >= 5) return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
    return <XCircle className="h-4 w-4 text-red-600" />;
  }

  return (
    <div className="mx-auto max-w-4xl">
      <Link
        href={`/company/${id}`}
        className="mb-4 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700"
      >
        <ArrowLeft className="h-4 w-4" />
        返回公司详情
      </Link>

      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">面试复盘</h1>
        <div className="flex rounded-lg border border-slate-200 bg-white p-0.5">
          <button
            onClick={() => setMode("free")}
            className={cn(
              "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium",
              mode === "free"
                ? "bg-blue-100 text-blue-700"
                : "text-slate-500 hover:text-slate-700",
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
                ? "bg-blue-100 text-blue-700"
                : "text-slate-500 hover:text-slate-700",
            )}
          >
            <ListTodo className="h-3.5 w-3.5" />
            结构化模式
          </button>
        </div>
      </div>

      <form onSubmit={handleAnalyze} className="mb-8 rounded-xl border border-slate-200 bg-white p-6">
        {mode === "free" ? (
          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-slate-700">
              面试笔记 <span className="text-red-500">*</span>
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={8}
              placeholder="粘贴你的面试原始笔记..."
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />
          </div>
        ) : (
          <div className="space-y-4">
            {entries.map((entry, index) => (
              <div
                key={entry.id}
                className="rounded-lg border border-slate-200 bg-slate-50 p-4"
              >
                <div className="mb-3 flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-700">
                    问题 {index + 1}
                  </span>
                  <button
                    type="button"
                    onClick={() => removeEntry(entry.id)}
                    disabled={entries.length <= 1}
                    className="rounded-md p-1 text-slate-400 hover:bg-slate-200 hover:text-red-500 disabled:opacity-30"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>

                <div className="space-y-3">
                  <div>
                    <label className="mb-1 block text-xs font-medium text-slate-600">
                      面试官问了什么 <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={entry.question}
                      onChange={(e) => updateEntry(entry.id, "question", e.target.value)}
                      placeholder="例如：解释 React diff 算法"
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="mb-1 block text-xs font-medium text-slate-600">
                      你是怎么回答的 <span className="text-red-500">*</span>
                    </label>
                    <textarea
                      value={entry.answer}
                      onChange={(e) => updateEntry(entry.id, "answer", e.target.value)}
                      rows={3}
                      placeholder="尽可能回忆你的回答要点..."
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="mb-1 block text-xs font-medium text-slate-600">
                        面试官反应
                      </label>
                      <input
                        type="text"
                        value={entry.interviewerReaction}
                        onChange={(e) =>
                          updateEntry(entry.id, "interviewerReaction", e.target.value)
                        }
                        placeholder="例如：追问了细节 / 没有追问"
                        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs font-medium text-slate-600">
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
                                : "border-slate-200 bg-white text-slate-500",
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
              className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-dashed border-slate-300 py-3 text-sm text-slate-500 hover:border-blue-400 hover:text-blue-600"
            >
              <Plus className="h-4 w-4" />
              添加问题
            </button>
          </div>
        )}

        <div className="mt-4 grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">面试日期</label>
            <input
              type="date"
              value={interviewDate}
              onChange={(e) => setInterviewDate(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">面试形式</label>
            <select
              value={interviewFormat}
              onChange={(e) => setInterviewFormat(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            >
              <option value="">请选择</option>
              <option value="phone">电话</option>
              <option value="video">视频</option>
              <option value="onsite">现场</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">面试官</label>
            <input
              type="text"
              value={interviewerName}
              onChange={(e) => setInterviewerName(e.target.value)}
              placeholder="可选"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">轮次</label>
            <input
              type="number"
              min={1}
              value={round}
              onChange={(e) => setRound(Number(e.target.value))}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">JD 关键点</label>
            <input
              type="text"
              value={jdKeyPoints}
              onChange={(e) => setJdKeyPoints(e.target.value)}
              placeholder="逗号分隔，可选"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="mt-4 flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            AI 分析
          </button>
        </div>
      </form>

      {loading && (
        <div className="flex flex-col items-center justify-center py-16 text-slate-400">
          <Loader2 className="mb-3 h-8 w-8 animate-spin text-blue-500" />
          <p className="text-sm">AI 正在分析你的面试表现...</p>
          <p className="mt-1 text-xs text-slate-400">可能需要 30 秒以上</p>
        </div>
      )}

      {result && (
        <div className="space-y-6">
          {result.questions && result.questions.length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white p-6">
              <h2 className="mb-4 text-lg font-semibold text-slate-900">问题列表</h2>
              <div className="space-y-4">
                {result.questions.map((q, i) => (
                  <div key={i} className="rounded-lg border border-slate-100 bg-slate-50 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-sm font-medium text-slate-900">{q.question}</p>
                      <span
                        className={cn(
                          "flex shrink-0 items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold",
                          getScoreColor(q.score),
                        )}
                      >
                        {getScoreIcon(q.score)}
                        {q.score}/10
                      </span>
                    </div>
                    {q.your_answer_summary && (
                      <p className="mt-2 text-xs text-slate-500">{q.your_answer_summary}</p>
                    )}
                    <p className="mt-2 text-sm text-slate-600">{q.assessment}</p>
                    {q.improvement && (
                      <p className="mt-1 text-sm text-blue-600">💡 {q.improvement}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {result.weak_points && result.weak_points.length > 0 && (
              <div className="rounded-xl border border-red-200 bg-red-50/50 p-4">
                <h3 className="mb-2 text-sm font-semibold text-red-800">薄弱点</h3>
                <div className="flex flex-wrap gap-1.5">
                  {result.weak_points.map((point, i) => (
                    <span
                      key={i}
                      className="rounded-full bg-red-100 px-2.5 py-0.5 text-xs text-red-700"
                    >
                      {point}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {result.strong_points && result.strong_points.length > 0 && (
              <div className="rounded-xl border border-green-200 bg-green-50/50 p-4">
                <h3 className="mb-2 text-sm font-semibold text-green-800">优势</h3>
                <div className="flex flex-wrap gap-1.5">
                  {result.strong_points.map((point, i) => (
                    <span
                      key={i}
                      className="rounded-full bg-green-100 px-2.5 py-0.5 text-xs text-green-700"
                    >
                      {point}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {result.next_round_prediction && result.next_round_prediction.length > 0 && (
            <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-4">
              <h3 className="mb-2 text-sm font-semibold text-blue-800">下一轮预测</h3>
              <div className="flex flex-wrap gap-1.5">
                {result.next_round_prediction.map((pred, i) => (
                  <span
                    key={i}
                    className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs text-blue-700"
                  >
                    {pred}
                  </span>
                ))}
              </div>
            </div>
          )}

          {result.interviewer_signals && result.interviewer_signals.length > 0 && (
            <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-4">
              <h3 className="mb-2 text-sm font-semibold text-amber-800">面试官信号</h3>
              <div className="flex flex-wrap gap-1.5">
                {result.interviewer_signals.map((signal, i) => (
                  <span
                    key={i}
                    className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs text-amber-700"
                  >
                    {signal}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
