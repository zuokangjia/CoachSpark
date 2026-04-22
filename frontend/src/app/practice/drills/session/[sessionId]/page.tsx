"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useParams } from "next/navigation";
import { practiceApi } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import {
  ArrowLeft,
  Loader2,
  Clock,
  CheckCircle,
  XCircle,
  ChevronRight,
  Trophy,
  Target,
} from "lucide-react";

const difficultyLabels = ["", "入门", "简单", "中等", "困难", "极难"];
const difficultyColors = ["", "text-green-500", "text-emerald-500", "text-yellow-500", "text-orange-500", "text-red-500"];

type Question = {
  id: string;
  title: string;
  content: string;
  difficulty: number;
  knowledge_points: string[];
  hints: string[];
};

type SessionState = {
  session_id: string;
  drill_id: string;
  drill_name: string;
  total_questions: number;
  current_question_index: number;
  current_question: Question | null;
};

export default function DrillSessionPage() {
  const router = useRouter();
  const params = useParams();
  const sessionId = params.sessionId as string;

  const [loading, setLoading] = useState(true);
  const [session, setSession] = useState<SessionState | null>(null);
  const [answer, setAnswer] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [completed, setCompleted] = useState(false);
  const [sessionResult, setSessionResult] = useState<any>(null);
  const [startTime, setStartTime] = useState<number>(Date.now());

  const loadSession = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const resultRes: any = await practiceApi.getDrillSessionResult(sessionId);
      if (resultRes.data?.status === "completed") {
        setCompleted(true);
        setSessionResult(resultRes.data);
        setLoading(false);
        return;
      }

      const drillId = resultRes.data?.drill_id;
      if (drillId) {
        const startRes: any = await practiceApi.startDrillSession(drillId);
        setSession(startRes.data);
        setStartTime(Date.now());
      }
    } catch (err) {
      console.error("Failed to load session:", err);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    loadSession();
  }, [loadSession]);

  const submitAnswer = async () => {
    if (!session || !answer.trim() || submitting) return;

    setSubmitting(true);
    const timeSpent = Math.floor((Date.now() - startTime) / 1000);

    try {
      const res: any = await practiceApi.submitDrillAnswer(session.session_id, {
        answer: answer.trim(),
        time_spent_seconds: timeSpent,
      });

      setResult(res.data);
      setAnswer("");

      if (res.data?.is_complete) {
        setCompleted(true);
        const resultRes: any = await practiceApi.getDrillSessionResult(session.session_id);
        setSessionResult(resultRes.data);
      } else if (res.data?.next_question) {
        setSession((prev) =>
          prev
            ? {
                ...prev,
                current_question_index: res.data.question_index + 1,
                current_question: res.data.next_question,
              }
            : null
        );
        setStartTime(Date.now());
      }
    } catch (err) {
      console.error("Failed to submit answer:", err);
      alert("提交失败，请重试");
    } finally {
      setSubmitting(false);
    }
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}秒`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}分${secs}秒`;
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-text-muted" />
      </div>
    );
  }

  if (completed && sessionResult) {
    return (
      <div className="mx-auto max-w-3xl">
        <div className="mb-6 flex items-center gap-2">
          <Link
            href="/practice"
            className="inline-flex items-center gap-1 text-sm text-text-secondary hover:text-text-primary"
          >
            <ArrowLeft className="h-4 w-4" />
            返回练习
          </Link>
        </div>

        <div className="rounded-xl border border-border bg-surface p-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-brand-subtle">
            <Trophy className="h-8 w-8 text-brand" />
          </div>
          <h1 className="text-2xl font-bold text-text-primary">练习完成！</h1>
          <p className="mt-2 text-text-secondary">{sessionResult.drill_name}</p>

          <div className="mt-6 grid grid-cols-3 gap-4">
            <div className="rounded-lg bg-surface-muted p-4">
              <div className="text-2xl font-bold text-text-primary">{sessionResult.average_score || 0}</div>
              <div className="text-xs text-text-muted">平均分</div>
            </div>
            <div className="rounded-lg bg-surface-muted p-4">
              <div className="text-2xl font-bold text-text-primary">{sessionResult.answered_count || 0}</div>
              <div className="text-xs text-text-muted">完成题数</div>
            </div>
            <div className="rounded-lg bg-surface-muted p-4">
              <div className="text-2xl font-bold text-text-primary">
                {formatDuration(sessionResult.total_time_spent_seconds || 0)}
              </div>
              <div className="text-xs text-text-muted">总用时</div>
            </div>
          </div>

          <div className="mt-8 flex items-center justify-center gap-3">
            <Link
              href="/practice/drill"
              className="rounded-lg bg-brand px-6 py-2.5 text-sm font-medium text-text-inverse hover:bg-brand-hover"
            >
              继续练习
            </Link>
            <Link
              href="/practice/drills/history"
              className="rounded-lg border border-border px-6 py-2.5 text-sm text-text-secondary hover:bg-surface-secondary"
            >
              查看记录
            </Link>
          </div>
        </div>

        {sessionResult.answers && sessionResult.answers.length > 0 && (
          <div className="mt-6 space-y-3">
            <h3 className="text-lg font-semibold text-text-primary">答题详情</h3>
            {sessionResult.answers.map((ans: any, idx: number) => (
              <div
                key={idx}
                className={cn(
                  "rounded-xl border p-4",
                  ans.score === null || ans.status === "pending"
                    ? "border-blue-200 bg-blue-50/50"
                    : ans.score >= 70
                    ? "border-green-200 bg-green-50/50"
                    : ans.score >= 50
                    ? "border-yellow-200 bg-yellow-50/50"
                    : "border-red-200 bg-red-50/50"
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-text-primary">题目 #{ans.question_index + 1}</span>
                  {ans.score === null || ans.status === "pending" ? (
                    <span className="flex items-center gap-1 text-sm text-blue-600">
                      <Loader2 className="h-3 w-3 animate-spin" />
                      评估中...
                    </span>
                  ) : (
                    <span
                      className={cn(
                        "text-sm font-bold",
                        ans.score >= 70 ? "text-green-600" : ans.score >= 50 ? "text-yellow-600" : "text-red-600"
                      )}
                    >
                      {ans.score} 分
                    </span>
                  )}
                </div>
                <p className="mt-2 text-sm text-text-secondary">{ans.feedback}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  if (!session || !session.current_question) {
    return (
      <div className="mx-auto max-w-3xl">
        <div className="flex h-64 flex-col items-center justify-center text-sm text-text-muted">
          <Target className="mb-2 h-8 w-8" />
          会话已结束或无效
          <Link href="/practice" className="mt-2 text-brand hover:text-brand-hover">
            返回练习 →
          </Link>
        </div>
      </div>
    );
  }

  const question = session.current_question;
  const progress = (session.current_question_index / session.total_questions) * 100;

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <Link
            href="/practice"
            className="inline-flex items-center gap-1 text-sm text-text-secondary hover:text-text-primary"
          >
            <ArrowLeft className="h-4 w-4" />
            退出练习
          </Link>
          <div className="text-sm text-text-secondary">
            {session.current_question_index + 1} / {session.total_questions}
          </div>
        </div>

        <div className="mt-3 h-2 w-full rounded-full bg-surface-muted overflow-hidden">
          <div
            className="h-full bg-brand transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="rounded-xl border border-border bg-surface p-6">
        <div className="mb-4 flex items-center gap-2">
          <span className={cn("text-sm font-medium", difficultyColors[question.difficulty])}>
            {difficultyLabels[question.difficulty]}
          </span>
        </div>

        <h2 className="text-xl font-semibold text-text-primary mb-4">{question.title}</h2>
        <p className="text-text-secondary whitespace-pre-wrap">{question.content}</p>

        {question.hints && question.hints.length > 0 && (
          <div className="mt-4 rounded-lg bg-surface-muted p-3">
            <div className="text-xs text-text-muted mb-1">提示</div>
            <ul className="text-sm text-text-secondary space-y-1">
              {question.hints.map((hint, i) => (
                <li key={i}>• {hint}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="mt-6 rounded-xl border border-border bg-surface p-6">
        <label className="block text-sm font-medium text-text-primary mb-2">
          你的答案
        </label>
        <textarea
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          placeholder="在此输入你的回答..."
          className="w-full min-h-[150px] rounded-lg border border-input-border bg-input-bg px-4 py-3 text-sm text-text-primary outline-none focus:border-input-focus placeholder:text-text-muted resize-y"
        />
        <div className="mt-4 flex items-center justify-between">
          <div className="text-xs text-text-muted">
            已用时: {formatDuration(Math.floor((Date.now() - startTime) / 1000))}
          </div>
          <button
            onClick={submitAnswer}
            disabled={!answer.trim() || submitting}
            className="rounded-lg bg-brand px-6 py-2 text-sm font-medium text-text-inverse hover:bg-brand-hover disabled:opacity-50 flex items-center gap-2"
          >
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                提交中...
              </>
            ) : session.current_question_index + 1 >= session.total_questions ? (
              <>
                完成练习
                <CheckCircle className="h-4 w-4" />
              </>
            ) : (
              <>
                下一题
                <ChevronRight className="h-4 w-4" />
              </>
            )}
          </button>
        </div>
      </div>

      {result && (
        <div className={cn(
          "mt-4 rounded-xl border p-4",
          result.feedback?.includes("后台评估") || result.score === 0
            ? "border-blue-200 bg-blue-50"
            : result.score >= 70
            ? "border-green-200 bg-green-50"
            : result.score >= 50
            ? "border-yellow-200 bg-yellow-50"
            : "border-red-200 bg-red-50"
        )}>
          <div className="flex items-center gap-2">
            {result.feedback?.includes("后台评估") || result.score === 0 ? (
              <>
                <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
                <span className="font-medium text-text-primary">答案已提交</span>
              </>
            ) : result.score >= 70 ? (
              <>
                <CheckCircle className="h-5 w-5 text-green-500" />
                <span className="font-medium text-text-primary">得分: {result.score} 分</span>
              </>
            ) : (
              <>
                <XCircle className="h-5 w-5 text-red-500" />
                <span className="font-medium text-text-primary">得分: {result.score} 分</span>
              </>
            )}
          </div>
          <p className="mt-2 text-sm text-text-secondary">{result.feedback}</p>
          {(result.feedback?.includes("后台评估") || result.score === 0) && (
            <p className="mt-1 text-xs text-blue-600">
              评估完成后可在练习记录中查看详细结果
            </p>
          )}
        </div>
      )}
    </div>
  );
}
