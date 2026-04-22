"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { practiceApi } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import {
  ArrowLeft,
  Loader2,
  CheckCircle,
  Clock,
  Calendar,
  ChevronRight,
  Target,
  Award,
} from "lucide-react";

type DrillHistoryItem = {
  id: string;
  drill_id: string;
  drill_name: string;
  drill_topic: string;
  status: string;
  total_questions: number;
  answered_count: number;
  average_score: number | null;
  total_time_spent_seconds: number;
  completed_at: string | null;
  started_at: string;
};

export default function DrillHistoryPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [history, setHistory] = useState<DrillHistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const limit = 20;

  const loadHistory = useCallback(async () => {
    setLoading(true);
    try {
      const res: any = await practiceApi.getDrillHistory(limit, offset);
      setHistory(res.data?.items || []);
      setTotal(res.data?.total || 0);
    } catch (err) {
      console.error("Failed to load drill history:", err);
    } finally {
      setLoading(false);
    }
  }, [offset]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}秒`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}分${secs}秒`;
  };

  const formatDate = (isoString: string | null) => {
    if (!isoString) return "";
    const date = new Date(isoString);
    return date.toLocaleString("zh-CN", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getScoreColor = (score: number | null) => {
    if (score === null) return "text-text-muted";
    if (score >= 70) return "text-green-500";
    if (score >= 50) return "text-yellow-500";
    return "text-red-500";
  };

  const getScoreBg = (score: number | null) => {
    if (score === null) return "bg-surface-muted";
    if (score >= 70) return "bg-green-500/10";
    if (score >= 50) return "bg-yellow-500/10";
    return "bg-red-500/10";
  };

  return (
    <div className="mx-auto max-w-4xl">
      <Link href="/practice" className="mb-4 inline-flex items-center gap-1 text-sm text-text-secondary hover:text-text-primary">
        <ArrowLeft className="h-4 w-4" />
        返回练习
      </Link>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
          <Award className="h-6 w-6 text-brand" />
          练习记录
        </h1>
        <p className="mt-1 text-sm text-text-secondary">AI 生成练习的历史记录</p>
      </div>

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-text-muted" />
        </div>
      ) : history.length === 0 ? (
        <div className="flex h-32 flex-col items-center justify-center text-sm text-text-muted">
          <Calendar className="mb-2 h-8 w-8" />
          暂无练习记录
          <Link
            href="/practice/drill"
            className="mt-2 text-brand hover:text-brand-hover"
          >
            去练习 →
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {history.map((item) => (
            <Link
              key={item.id}
              href={`/practice/drills/session/${item.id}`}
              className="block rounded-xl border border-border bg-surface p-4 hover:border-brand/60"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center gap-1 rounded-full bg-brand-subtle px-2 py-0.5 text-xs text-brand-text">
                      <Target className="h-3 w-3" />
                      {item.drill_topic}
                    </span>
                    <span className="text-xs text-text-muted">{formatDate(item.completed_at || item.started_at)}</span>
                    {item.status === "completed" ? (
                      <span className="text-xs text-green-500">已完成</span>
                    ) : (
                      <span className="text-xs text-text-muted">已放弃</span>
                    )}
                  </div>
                  <h3 className="mt-1 text-base font-medium text-text-primary">
                    {item.drill_name}
                  </h3>
                  <div className="mt-2 flex items-center gap-4 text-xs text-text-muted">
                    <span className="flex items-center gap-1">
                      <CheckCircle className="h-3 w-3" />
                      {item.answered_count} / {item.total_questions} 题
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatDuration(item.total_time_spent_seconds)}
                    </span>
                  </div>
                </div>

                <div className="flex shrink-0 items-center gap-3">
                  <div className={cn("text-right rounded-lg px-3 py-2", getScoreBg(item.average_score))}>
                    <div className={cn("text-2xl font-bold", getScoreColor(item.average_score))}>
                      {item.average_score ?? "-"}
                    </div>
                    <div className="text-xs text-text-muted">平均分</div>
                  </div>
                  <ChevronRight className="h-5 w-5 text-text-muted" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}

      {!loading && history.length > 0 && total > limit && (
        <div className="mt-6 flex items-center justify-center gap-4">
          <button
            onClick={() => setOffset(Math.max(0, offset - limit))}
            disabled={offset === 0}
            className="rounded-lg border border-border bg-surface px-4 py-2 text-sm text-text-primary disabled:opacity-50 hover:bg-surface-secondary"
          >
            上一页
          </button>
          <span className="text-sm text-text-secondary">
            {offset + 1} - {Math.min(offset + limit, total)} / {total}
          </span>
          <button
            onClick={() => setOffset(offset + limit)}
            disabled={offset + limit >= total}
            className="rounded-lg border border-border bg-surface px-4 py-2 text-sm text-text-primary disabled:opacity-50 hover:bg-surface-secondary"
          >
            下一页
          </button>
        </div>
      )}
    </div>
  );
}
