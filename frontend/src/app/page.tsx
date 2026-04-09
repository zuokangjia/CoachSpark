"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  DndContext,
  DragEndEvent,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { Plus, Loader2, Building2, Calendar, TrendingUp, AlertTriangle, Clock, FileText, AlertCircle, Target } from "lucide-react";
import { useCompanyStore } from "@/lib/store/company-store";
import { COLUMNS, cn } from "@/lib/utils";
import { companiesApi, dashboardApi } from "@/lib/api-client";
import { CompanyCard } from "./components/company-card";
import { AddCompanyModal } from "./components/add-company-modal";

interface DashboardStats {
  total_companies: number;
  applied: number;
  interviewing: number;
  rejected: number;
  total_interviews: number;
  top_weak_points: [string, number][];
  day3_metrics?: {
    prep_completion_rate: number;
    completed_prep_tasks: number;
    total_prep_tasks: number;
    recent_avg_score: number;
    previous_avg_score: number;
    score_improvement: number;
    scored_interviews: number;
  };
}

interface TodayBriefing {
  upcoming_interviews: Array<{
    company: string;
    position: string;
    round: number;
    date: string;
    days_until: number;
  }>;
  pending_results: Array<{
    company: string;
    round: number;
    expected_date: string;
    days_overdue: number;
  }>;
  unreviewed: Array<{
    company: string;
    round: number;
    interview_date: string;
    days_since: number;
  }>;
}

export default function DashboardPage() {
  const { companies, loading, error, fetchCompanies, moveCompany, removeCompany, clearError } = useCompanyStore();
  const [showModal, setShowModal] = useState(false);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [todayBrief, setTodayBrief] = useState<TodayBriefing | null>(null);

  async function loadStats() {
    try {
      const res = await dashboardApi.stats();
      setStats(res.data);
    } catch {
      // stats load failure is non-blocking
    }
  }

  async function loadTodayBrief() {
    try {
      const res = await dashboardApi.today();
      setTodayBrief(res.data);
    } catch {
      // non-blocking
    }
  }

  useEffect(() => {
    fetchCompanies();
    const timer = window.setTimeout(() => {
      void loadStats();
      void loadTodayBrief();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [fetchCompanies]);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 8 },
    }),
  );

  async function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const newStatus = over.id as string;
    if (!COLUMNS.some((c) => c.id === newStatus)) return;

    const companyId = active.id as string;
    moveCompany(companyId, newStatus);

    try {
      await companiesApi.update(companyId, { status: newStatus });
      loadStats();
    } catch {
      alert("更新状态失败");
      fetchCompanies();
    }
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-text-muted" />
      </div>
    );
  }

  return (
    <div>
      {error && (
        <div className="mb-4 rounded-lg border border-error/50 bg-error-bg px-4 py-3 text-sm text-error-text flex items-center justify-between">
          <span>{error}</span>
          <button onClick={clearError} className="text-error-text hover:text-error font-medium">✕</button>
        </div>
      )}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-text-primary">投递看板</h1>
          <p className="mt-1 text-sm text-text-secondary">
            管理你的所有投递和面试进度
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/match"
            className="inline-flex items-center gap-1.5 rounded-lg border border-brand/30 bg-brand-subtle px-4 py-2 text-sm font-medium text-brand-text hover:bg-brand-subtle/80"
          >
            <Target className="h-4 w-4" />
            岗位匹配
          </Link>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-text-inverse hover:bg-brand-hover"
          >
            <Plus className="h-4 w-4" />
            添加流程
          </button>
        </div>
      </div>

      {todayBrief && (
        <TodayBriefingCard briefing={todayBrief} />
      )}

      {stats && (
        <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
          <StatCard
            icon={Building2}
            label="总投递"
            value={stats.total_companies}
            color="text-info-text"
            bg="bg-info-bg"
          />
          <StatCard
            icon={Calendar}
            label="面试中"
            value={stats.interviewing}
            color="text-warning-text"
            bg="bg-warning-bg"
          />
          <StatCard
            icon={TrendingUp}
            label="已完成"
            value={stats.rejected}
            color="text-success-text"
            bg="bg-success-bg"
          />
          <StatCard
            icon={AlertTriangle}
            label="面试总数"
            value={stats.total_interviews}
            color="text-brand-text"
            bg="bg-brand-subtle"
          />
        </div>
      )}

      {stats?.day3_metrics && (
        <div className="mb-6 grid grid-cols-1 gap-3 md:grid-cols-2">
          <div className="rounded-xl border border-border bg-surface p-4">
            <div className="mb-1 text-xs text-text-secondary">Day3 备战完成率</div>
            <div className="flex items-end justify-between">
              <div className="text-2xl font-semibold text-text-primary">
                {stats.day3_metrics.prep_completion_rate}%
              </div>
              <div className="text-xs text-text-muted">
                {stats.day3_metrics.completed_prep_tasks}/{stats.day3_metrics.total_prep_tasks} tasks
              </div>
            </div>
            <div className="mt-2 h-2 rounded-full bg-surface-muted">
              <div
                className="h-2 rounded-full bg-brand transition-all"
                style={{ width: `${Math.min(100, Math.max(0, stats.day3_metrics.prep_completion_rate))}%` }}
              />
            </div>
          </div>

          <div className="rounded-xl border border-border bg-surface p-4">
            <div className="mb-1 text-xs text-text-secondary">Day3 复盘改善率</div>
            <div className="flex items-end justify-between">
              <div
                className={cn(
                  "text-2xl font-semibold",
                  stats.day3_metrics.score_improvement >= 0 ? "text-success-text" : "text-error-text",
                )}
              >
                {stats.day3_metrics.score_improvement >= 0 ? "+" : ""}
                {stats.day3_metrics.score_improvement}
              </div>
              <div className="text-xs text-text-muted">
                近3轮 {stats.day3_metrics.recent_avg_score} / 前3轮 {stats.day3_metrics.previous_avg_score}
              </div>
            </div>
          </div>
        </div>
      )}

      {stats && stats.top_weak_points.length > 0 && (
        <div className="mb-6 rounded-xl border border-border bg-surface p-4">
          <h3 className="mb-2 text-sm font-semibold text-text-secondary">薄弱点 TOP 5</h3>
          <div className="flex flex-wrap gap-1.5">
            {stats.top_weak_points.map(([wp, count]) => (
              <span
                key={wp}
                className="inline-flex items-center gap-1 rounded-full bg-error-bg px-2.5 py-1 text-xs text-error-text"
              >
                {wp}
                <span className="font-semibold">{count}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {COLUMNS.map((col) => {
            const colCompanies = companies.filter((c) => c.status === col.id);
            return (
              <div
                key={col.id}
                className={cn(
                  "flex min-h-[200px] flex-col rounded-xl border p-3",
                  col.color,
                )}
              >
                <div className="mb-3 flex items-center justify-between px-1">
                  <h2 className="text-sm font-semibold text-text-secondary">
                    {col.title}
                  </h2>
                  <span className="rounded-full bg-surface-muted/70 px-2 py-0.5 text-xs font-medium text-text-muted">
                    {colCompanies.length}
                  </span>
                </div>
                <SortableContext
                  items={colCompanies.map((c) => c.id)}
                  strategy={verticalListSortingStrategy}
                >
                  <div className="flex flex-col gap-2">
                    {colCompanies.map((company) => (
                      <CompanyCard
                        key={company.id}
                        company={company}
                        onStatusChanged={() => {
                          fetchCompanies();
                          loadStats();
                        }}
                        onDeleted={(id) => {
                          removeCompany(id);
                          loadStats();
                        }}
                        onSaved={() => {
                          fetchCompanies();
                          loadStats();
                        }}
                      />
                    ))}
                  </div>
                </SortableContext>
                {colCompanies.length === 0 && (
                  <div className="flex flex-1 items-center justify-center py-8 text-xs text-text-muted">
                    暂无投递
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </DndContext>

      {showModal && <AddCompanyModal onClose={() => setShowModal(false)} onAdded={() => { fetchCompanies(); loadStats(); }} />}
    </div>
  );
}

function TodayBriefingCard({ briefing }: { briefing: TodayBriefing }) {
  const hasItems =
    briefing.upcoming_interviews.length > 0 ||
    briefing.pending_results.length > 0 ||
    briefing.unreviewed.length > 0;

  if (!hasItems) return null;

  return (
    <div className="mb-6 rounded-xl border border-border bg-surface p-5 shadow-sm">
      <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-text-primary">
        <Clock className="h-4 w-4 text-brand" />
        今日提醒
      </h2>
      <div className="space-y-2">
        {briefing.upcoming_interviews.map((iv, i) => (
          <div
            key={`up-${i}`}
            className="flex items-center gap-2 rounded-lg bg-surface px-3 py-2 text-sm text-text-secondary"
          >
            <span
              className={cn(
                "rounded-full px-2 py-0.5 text-xs font-medium",
                iv.days_until === 0
                  ? "bg-error-bg text-error-text"
                  : iv.days_until <= 2
                    ? "bg-warning-bg text-warning-text"
                    : "bg-info-bg text-info-text",
              )}
            >
              {iv.days_until === 0
                ? "今天"
                : iv.days_until === 1
                  ? "明天"
                  : `${iv.days_until} 天后`}
            </span>
            <span>
              {iv.company} · {iv.position} · 第 {iv.round} 轮
            </span>
          </div>
        ))}
        {briefing.pending_results.map((pr, i) => (
          <div
            key={`pr-${i}`}
            className="flex items-center gap-2 rounded-lg bg-surface px-3 py-2 text-sm text-text-secondary"
          >
            <AlertCircle className="h-4 w-4 shrink-0 text-warning" />
            <span>
              {pr.company} 第 {pr.round} 轮结果已逾期 {pr.days_overdue} 天
            </span>
          </div>
        ))}
        {briefing.unreviewed.map((ur, i) => (
          <div
            key={`ur-${i}`}
            className="flex items-center gap-2 rounded-lg bg-surface px-3 py-2 text-sm text-text-secondary"
          >
            <FileText className="h-4 w-4 shrink-0 text-text-muted" />
            <span className="text-text-muted">
              {ur.company} 第 {ur.round} 轮面试已过 {ur.days_since} 天未复盘
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  color,
  bg,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number;
  color: string;
  bg: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-border bg-surface p-4">
      <div className={cn("flex h-10 w-10 items-center justify-center rounded-lg", bg)}>
        <Icon className={cn("h-5 w-5", color)} />
      </div>
      <div>
        <p className="text-xs text-text-secondary">{label}</p>
        <p className="text-lg font-semibold text-text-primary">{value}</p>
      </div>
    </div>
  );
}
