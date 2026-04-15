"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { practiceApi } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import {
  ArrowLeft,
  Loader2,
  Send,
  Lightbulb,
  ChevronDown,
  ChevronUp,
  CheckCircle,
  XCircle,
  TrendingUp,
  TrendingDown,
} from "lucide-react";

type Question = {
  id: string;
  category_id: string;
  category_name: string;
  title: string;
  content: string;
  difficulty: number;
  knowledge_points: string[];
  company_tags: string[];
  question_type: string;
  options: string[] | null;
  hints: string[];
};

type SubmitResult = {
  performance_id: string;
  score: number;
  feedback: string;
  evaluation_details: {
    scores: {
      completeness: number;
      accuracy: number;
      clarity: number;
      depth: number;
    };
    total_score: number;
    feedback: string;
    improvement_suggestions: string[];
  };
  dimension_changes: {
    dimension: string;
    before: number;
    after: number;
    delta: number;
  }[];
};

const difficultyLabels = ["", "入门", "简单", "中等", "困难", "极难"];
const difficultyColors = ["", "text-green-500", "text-emerald-500", "text-yellow-500", "text-orange-500", "text-red-500"];

export default function QuestionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const questionId = params.id as string;

  const [loading, setLoading] = useState(true);
  const [question, setQuestion] = useState<Question | null>(null);
  const [answer, setAnswer] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<SubmitResult | null>(null);
  const [showHints, setShowHints] = useState(false);
  const [startTime] = useState(Date.now());

  const loadQuestion = useCallback(async () => {
    setLoading(true);
    try {
      const res: any = await practiceApi.get(questionId);
      setQuestion(res.data || null);
    } catch {
      setQuestion(null);
    } finally {
      setLoading(false);
    }
  }, [questionId]);

  useEffect(() => {
    loadQuestion();
  }, [loadQuestion]);

  async function handleSubmit() {
    if (!answer.trim()) return;
    setSubmitting(true);
    try {
      const timeSpent = Math.round((Date.now() - startTime) / 1000);
      const res: any = await practiceApi.submit(questionId, {
        submitted_answer: answer,
        time_spent_seconds: timeSpent,
      });
      setResult(res.data || null);
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl">
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-text-muted" />
        </div>
      </div>
    );
  }

  if (!question) {
    return (
      <div className="mx-auto max-w-3xl">
        <Link href="/practice" className="mb-4 inline-flex items-center gap-1 text-sm text-text-secondary hover:text-text-primary">
          <ArrowLeft className="h-4 w-4" />
          返回题库
        </Link>
        <div className="flex h-32 items-center justify-center text-sm text-text-muted">
          题目不存在
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl">
      <Link href="/practice" className="mb-4 inline-flex items-center gap-1 text-sm text-text-secondary hover:text-text-primary">
        <ArrowLeft className="h-4 w-4" />
        返回题库
      </Link>

      {/* 题目信息 */}
      <div className="rounded-xl border border-border bg-surface p-6">
        <div className="flex items-center gap-2 mb-3">
          <span className={cn("text-sm font-medium", difficultyColors[question.difficulty])}>
            {difficultyLabels[question.difficulty]}
          </span>
          <span className="text-xs text-text-muted">·</span>
          <span className="text-sm text-text-secondary">{question.category_name}</span>
        </div>
        <h1 className="text-xl font-bold text-text-primary">{question.title}</h1>
        <p className="mt-4 text-text-secondary whitespace-pre-wrap">{question.content}</p>

        {/* 知识点 */}
        {question.knowledge_points.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {question.knowledge_points.map((kp, idx) => (
              <span key={`${kp}-${idx}`} className="inline-flex items-center gap-1 rounded-full bg-surface-muted px-3 py-1 text-sm text-text-secondary">
                <Lightbulb className="h-3 w-3" />
                {kp}
              </span>
            ))}
          </div>
        )}

        {/* 提示 */}
        {question.hints.length > 0 && (
          <div className="mt-4">
            <button
              type="button"
              onClick={() => setShowHints(!showHints)}
              className="flex items-center gap-1 text-sm text-text-muted hover:text-text-secondary"
            >
              {showHints ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              {showHints ? "收起提示" : "查看提示"}
            </button>
            {showHints && (
              <div className="mt-2 space-y-1">
                {question.hints.map((hint, idx) => (
                  <div key={`hint-${idx}`} className="rounded-md bg-surface-muted px-3 py-2 text-sm text-text-secondary">
                    {hint}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 答案提交或结果 */}
      {!result ? (
        <div className="mt-4 rounded-xl border border-border bg-surface p-6">
          <label className="mb-2 block text-sm font-medium text-text-primary">你的回答</label>
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            rows={8}
            placeholder="请输入你的回答..."
            className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted"
          />
          <div className="mt-4 flex justify-end">
            <button
              type="button"
              onClick={handleSubmit}
              disabled={submitting || !answer.trim()}
              className="inline-flex items-center gap-2 rounded-lg bg-brand px-6 py-2.5 text-sm font-medium text-text-inverse hover:bg-brand-hover disabled:opacity-50"
            >
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              {submitting ? "评估中..." : "提交答案"}
            </button>
          </div>
        </div>
      ) : (
        <div className="mt-4 space-y-4">
          {/* 评分 */}
          <div className="rounded-xl border border-border bg-surface p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={cn(
                  "text-4xl font-bold",
                  result.score >= 70 ? "text-success" : result.score >= 40 ? "text-warning" : "text-error"
                )}>
                  {result.score}
                </div>
                <div className="text-sm text-text-muted">/ 100</div>
              </div>
              <div className={cn(
                "inline-flex items-center gap-1 rounded-full px-3 py-1 text-sm font-medium",
                result.score >= 70 ? "bg-success/20 text-success" : result.score >= 40 ? "bg-warning/20 text-warning" : "bg-error/20 text-error"
              )}>
                {result.score >= 70 ? <CheckCircle className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                {result.score >= 70 ? "表现良好" : result.score >= 40 ? "需要改进" : "差距较大"}
              </div>
            </div>

            {/* 维度评分 */}
            <div className="mt-4 grid grid-cols-2 gap-3">
              {Object.entries(result.evaluation_details.scores).map(([key, value]) => (
                <div key={key} className="rounded-lg bg-surface-muted p-3">
                  <div className="text-xs text-text-muted capitalize">
                    {key === "completeness" ? "完整性" :
                     key === "accuracy" ? "准确性" :
                     key === "clarity" ? "清晰度" : "深度"}
                  </div>
                  <div className="mt-1 text-lg font-semibold text-text-primary">{value}/20</div>
                </div>
              ))}
            </div>
          </div>

          {/* 反馈 */}
          <div className="rounded-xl border border-border bg-surface p-6">
            <h3 className="text-sm font-medium text-text-primary mb-2">详细反馈</h3>
            <p className="text-sm text-text-secondary whitespace-pre-wrap">{result.feedback}</p>

            {result.evaluation_details.improvement_suggestions.length > 0 && (
              <div className="mt-4">
                <h4 className="text-xs font-medium text-text-muted mb-2">改进建议</h4>
                <div className="space-y-1">
                  {result.evaluation_details.improvement_suggestions.map((s, idx) => (
                    <div key={`s-${idx}`} className="flex items-start gap-2 text-sm text-text-secondary">
                      <span className="text-brand">•</span>
                      {s}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* 维度变化 */}
          {result.dimension_changes.length > 0 && (
            <div className="rounded-xl border border-border bg-surface p-6">
              <h3 className="text-sm font-medium text-text-primary mb-3">画像变化</h3>
              <div className="space-y-2">
                {result.dimension_changes.map((change) => (
                  <div key={change.dimension} className="flex items-center justify-between rounded-lg bg-surface-muted p-3">
                    <span className="text-sm text-text-primary">{change.dimension}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-text-muted">Lv.{change.before}</span>
                      {change.delta > 0 ? (
                        <TrendingUp className="h-4 w-4 text-success" />
                      ) : change.delta < 0 ? (
                        <TrendingDown className="h-4 w-4 text-error" />
                      ) : null}
                      <span className={cn(
                        "text-sm font-medium",
                        change.delta > 0 ? "text-success" : change.delta < 0 ? "text-error" : "text-text-muted"
                      )}>
                        {change.delta > 0 ? "+" : ""}{change.delta}
                      </span>
                      <span className="text-sm text-text-muted">→ Lv.{change.after}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 操作按钮 */}
          <div className="flex justify-between">
            <button
              type="button"
              onClick={() => router.push("/practice")}
              className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text-secondary hover:bg-surface-muted"
            >
              返回题库
            </button>
            <button
              type="button"
              onClick={() => {
                setAnswer("");
                setResult(null);
                setShowHints(false);
              }}
              className="rounded-lg bg-brand px-4 py-2 text-sm font-medium text-text-inverse hover:bg-brand-hover"
            >
              再练一道
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
