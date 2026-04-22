"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { practiceApi } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import {
  ArrowLeft,
  Loader2,
  Target,
  Zap,
  GraduationCap,
  History,
  Trophy,
  Clock,
  ChevronRight,
  Play,
  BookOpen,
  MessageSquare,
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

const difficultyLabels = ["", "入门", "简单", "中等", "困难", "极难"];
const difficultyColors = ["", "text-green-500", "text-emerald-500", "text-yellow-500", "text-orange-500", "text-red-500"];

export default function PracticePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [recentSessions, setRecentSessions] = useState<DrillHistoryItem[]>([]);

  const loadRecentSessions = useCallback(async () => {
    setLoading(true);
    try {
      const res: any = await practiceApi.getDrillHistory(20, 0);
      const items = res.data?.items || [];
      setRecentSessions(items.slice(0, 5));
    } catch (err) {
      console.error("Failed to load recent sessions:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRecentSessions();
  }, [loadRecentSessions]);

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}秒`;
    const mins = Math.floor(seconds / 60);
    return `${mins}分钟`;
  };

  const formatDate = (isoString: string | null) => {
    if (!isoString) return "";
    const date = new Date(isoString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = diff / (1000 * 60 * 60);
    if (hours < 1) return "刚刚";
    if (hours < 24) return `${Math.floor(hours)}小时前`;
    const days = Math.floor(hours / 24);
    if (days === 1) return "昨天";
    if (days < 7) return `${days}天前`;
    return date.toLocaleDateString("zh-CN", { month: "short", day: "numeric" });
  };

  const getScoreColor = (score: number | null) => {
    if (score === null) return "text-text-muted";
    if (score >= 70) return "text-green-500";
    if (score >= 50) return "text-yellow-500";
    return "text-red-500";
  };

  const getStatusBadge = (status: string) => {
    if (status === "completed") {
      return <span className="text-xs text-green-500">已完成</span>;
    }
    return <span className="text-xs text-orange-500">进行中</span>;
  };

  return (
    <div className="mx-auto max-w-4xl">
      <Link href="/" className="mb-4 inline-flex items-center gap-1 text-sm text-text-secondary hover:text-text-primary">
        <ArrowLeft className="h-4 w-4" />
        返回看板
      </Link>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
          <GraduationCap className="h-6 w-6 text-brand" />
          专项练习
        </h1>
        <p className="mt-1 text-sm text-text-secondary">基于知识库的 AI 生成练习</p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <div className="md:col-span-2 space-y-6">
          <div className="rounded-xl border border-border bg-surface p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
                <History className="h-5 w-5 text-text-muted" />
                最近练习
              </h2>
              <Link
                href="/practice/drills/history"
                className="text-sm text-brand hover:text-brand-hover"
              >
                查看全部
              </Link>
            </div>

            {loading ? (
              <div className="flex h-32 items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-text-muted" />
              </div>
            ) : recentSessions.length === 0 ? (
              <div className="flex h-32 flex-col items-center justify-center text-sm text-text-muted">
                <Trophy className="mb-2 h-8 w-8" />
                暂无练习记录
                <p className="text-xs mt-1">开始你的第一次专项练习吧</p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentSessions.map((session) => (
                  <Link
                    key={session.id}
                    href={`/practice/drills/session/${session.id}`}
                    className="flex items-center justify-between p-3 rounded-lg border border-border bg-surface-muted hover:border-brand/60 transition-colors"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium text-text-primary">
                          {session.drill_name}
                        </span>
                        {getStatusBadge(session.status)}
                      </div>
                      <div className="flex items-center gap-3 text-xs text-text-muted">
                        <span className="flex items-center gap-1">
                          <Target className="h-3 w-3" />
                          {session.drill_topic}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {formatDate(session.completed_at || session.started_at)}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {session.average_score !== null ? (
                        <div className={cn("text-xl font-bold", getScoreColor(session.average_score))}>
                          {session.average_score}
                        </div>
                      ) : (
                        <div className="text-sm text-text-muted">
                          {session.answered_count}/{session.total_questions}
                        </div>
                      )}
                      <ChevronRight className="h-4 w-4 text-text-muted" />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-xl border border-brand/30 bg-brand/5 p-6">
            <div className="flex items-center gap-2 mb-3">
              <Zap className="h-5 w-5 text-brand" />
              <h3 className="text-base font-semibold text-text-primary">AI 生成练习</h3>
            </div>
            <p className="text-sm text-text-secondary mb-4">
              基于知识库自动生成针对性练习题
            </p>
            <Link
              href="/practice/drill"
              className="flex items-center justify-center gap-2 w-full rounded-lg bg-brand py-3 text-sm font-medium text-text-inverse hover:bg-brand-hover"
            >
              <Sparkles className="h-4 w-4" />
              开始生成
            </Link>
          </div>

          

          <div className="rounded-xl border border-border bg-surface p-6">
            <div className="flex items-center gap-2 mb-3">
              <BookOpen className="h-5 w-5 text-text-muted" />
              <h3 className="text-base font-semibold text-text-primary">知识库</h3>
            </div>
            <p className="text-sm text-text-secondary mb-4">
              管理知识条目，用于生成练习题
            </p>
            <Link
              href="/practice/knowledge"
              className="flex items-center justify-center gap-2 w-full rounded-lg border border-border py-3 text-sm font-medium text-text-primary hover:bg-surface-muted"
            >
              管理知识
            </Link>
          </div>

          <div className="rounded-xl border border-border bg-surface p-6">
            <div className="flex items-center gap-2 mb-3">
              <MessageSquare className="h-5 w-5 text-text-muted" />
              <h3 className="text-base font-semibold text-text-primary">八股专项</h3>
            </div>
            <p className="text-sm text-text-secondary mb-4">
              固定面试题型的标准答案框架
            </p>
            <Link
              href="/practice/eight-part"
              className="flex items-center justify-center gap-2 w-full rounded-lg border border-border py-3 text-sm font-medium text-text-primary hover:bg-surface-muted"
            >
              开始练习
            </Link>
          </div>

          <div className="rounded-xl border border-border bg-surface p-6">
            <div className="flex items-center gap-2 mb-3">
              <History className="h-5 w-5 text-text-muted" />
              <h3 className="text-base font-semibold text-text-primary">练习记录</h3>
            </div>
            <p className="text-sm text-text-secondary mb-4">
              查看所有练习历史和成绩
            </p>
            <Link
              href="/practice/drills/history"
              className="flex items-center justify-center gap-2 w-full rounded-lg border border-border py-3 text-sm font-medium text-text-primary hover:bg-surface-muted"
            >
              查看记录
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

function Sparkles(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z" />
    </svg>
  );
}