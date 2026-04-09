"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { ArrowLeft, Loader2, Check, Circle, Clock, Zap, Info } from "lucide-react";
import { prepApi, companiesApi, profileApi } from "@/lib/api-client";

interface DailyTask {
  day: number;
  focus: string;
  priority: string;
  tasks: string[];
  total_minutes?: number;
  completed_task_indexes?: number[];
  completed: boolean;
}

type WeakPointTrend = { trend?: string; avg_score?: number };
type WeakPointTrackingInfo = { is_persistent?: boolean };

function normalizePlan(raw: unknown[]): DailyTask[] {
  if (!Array.isArray(raw)) return [];

  const list: DailyTask[] = [];
  for (let i = 0; i < raw.length; i += 1) {
    const item = raw[i];
    if (!item || typeof item !== "object") continue;
    const record = item as Record<string, unknown>;

    const day = Number.isInteger(record.day) ? (record.day as number) : i + 1;
    const focus = typeof record.focus === "string" && record.focus.trim()
      ? record.focus.trim()
      : `第 ${day} 天重点`;
    const priority = typeof record.priority === "string" ? record.priority : "medium";
    const tasks = Array.isArray(record.tasks)
      ? record.tasks.map((t) => String(t).trim()).filter(Boolean).slice(0, 5)
      : [];
    const completed = Boolean(record.completed);
    const totalMinutes = typeof record.total_minutes === "number" ? record.total_minutes : undefined;
    const completedIndexes = Array.isArray(record.completed_task_indexes)
      ? record.completed_task_indexes
        .map((idx) => Number(idx))
        .filter((idx) => Number.isInteger(idx) && idx >= 0 && idx < tasks.length)
      : [];

    if (tasks.length === 0) continue;
    list.push({
      day,
      focus,
      priority,
      tasks,
      completed,
      completed_task_indexes: completedIndexes,
      total_minutes: totalMinutes,
    });
  }

  return list.sort((a, b) => a.day - b.day);
}

const priorityColors: Record<string, string> = {
  high: "bg-error-bg text-error-text",
  medium: "bg-warning-bg text-warning-text",
  low: "bg-success-bg text-success-text",
};

const priorityLabels: Record<string, string> = {
  high: "高",
  medium: "中",
  low: "低",
};

export default function PrepPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const id = params.id as string;

  const [daysAvailable, setDaysAvailable] = useState(7);
  const [targetRound, setTargetRound] = useState(1);
  const [weakPoints, setWeakPoints] = useState("");
  const [autoWeakPoints, setAutoWeakPoints] = useState<string[]>([]);
  const [jdDirections, setJdDirections] = useState("");
  const [hasJd, setHasJd] = useState(false);
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState<DailyTask[]>([]);
  const [prepPlanId, setPrepPlanId] = useState("");
  const [completedTasks, setCompletedTasks] = useState<Set<string>>(new Set());

  const loadExistingData = useCallback(async () => {
    try {
      const [companyRes, chainRes, latestPlanRes, profileRes] = await Promise.all([
        companiesApi.get(id),
        companiesApi.getChain(id),
        prepApi.getLatest(id),
        profileApi.get(),
      ]);

      if (companyRes.data?.jd_text && companyRes.data.jd_text.length > 10) {
        setHasJd(true);
      }

      const allWeakPoints = new Set<string>();
      if (chainRes.data?.weak_point_tracking) {
        const tracking = chainRes.data.weak_point_tracking as Record<string, WeakPointTrackingInfo>;
        const persistentWp = Object.entries(tracking)
          .filter(([, info]) => Boolean(info?.is_persistent))
          .map(([wp]) => wp);
        persistentWp.forEach((wp) => allWeakPoints.add(wp));
        setAutoWeakPoints(persistentWp);
      }

      if (Array.isArray(profileRes.data?.dimensions)) {
        const dimensions = profileRes.data.dimensions as Array<{
          dimension: string;
          trend?: string;
          level?: number;
        }>;
        const decliningOrStable = dimensions
          .filter((info) =>
            info?.trend === "down" || (info?.trend === "stable" && (info?.level ?? 5) <= 3)
          )
          .map((info) => info.dimension)
          .filter(Boolean);
        decliningOrStable.forEach((wp) => allWeakPoints.add(wp));
        if (allWeakPoints.size > 0) {
          setWeakPoints((prev) =>
            prev.trim().length > 0 ? prev : Array.from(allWeakPoints).join(", "),
          );
        }
      }

      if (latestPlanRes.data?.daily_tasks?.length > 0) {
        setPrepPlanId(String(latestPlanRes.data.prep_plan_id || ""));
        const normalized = normalizePlan(latestPlanRes.data.daily_tasks);
        setPlan(normalized);
        const initialCompleted = new Set<string>();
        for (const day of normalized) {
          if (Array.isArray(day.completed_task_indexes)) {
            day.completed_task_indexes.forEach((idx) => {
              if (Number.isInteger(idx) && idx >= 0 && idx < day.tasks.length) {
                initialCompleted.add(`${day.day}-${idx}`);
              }
            });
          }
        }
        setCompletedTasks(initialCompleted);
      }
    } catch {
      // data loading failure is non-blocking
    }
  }, [id]);

  useEffect(() => {
    const r = searchParams.get("round");
    if (r) setTargetRound(Number(r));
    const wp = searchParams.get("weak_points");
    if (wp) {
      const normalizedFromQuery = wp
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean)
        .join(", ");
      if (normalizedFromQuery) {
        setWeakPoints((prev) => (prev.trim().length > 0 ? prev : normalizedFromQuery));
      }
    }
    loadExistingData();
  }, [searchParams, loadExistingData]);

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    if (!weakPoints.trim() && !jdDirections.trim() && !hasJd) {
      alert("请至少填写薄弱点，或确保公司已填写 JD");
      return;
    }

    setLoading(true);
    try {
      const payload: Record<string, unknown> = {
        company_id: id,
        target_round: targetRound,
        days_available: daysAvailable,
      };
      if (weakPoints.trim()) {
        payload.weak_points = weakPoints.split(",").map((s) => s.trim()).filter(Boolean);
      }
      if (jdDirections.trim()) {
        payload.jd_directions = jdDirections.split(",").map((s) => s.trim()).filter(Boolean);
      }

      const res = await prepApi.generate(payload);
      setPrepPlanId(String(res.data.prep_plan_id || ""));
      const normalized = normalizePlan(res.data.daily_tasks || []);
      setPlan(normalized);
      setCompletedTasks(new Set());
    } catch {
      alert("生成失败，请重试");
    } finally {
      setLoading(false);
    }
  }

  async function toggleTask(day: number, index: number) {
    const key = `${day}-${index}`;
    let nextCompleted = false;
    setCompletedTasks((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
        nextCompleted = false;
      } else {
        next.add(key);
        nextCompleted = true;
      }
      return next;
    });

    if (!prepPlanId) {
      return;
    }

    try {
      await prepApi.updateTaskCompletion(prepPlanId, {
        day,
        task_index: index,
        completed: nextCompleted,
      });
    } catch {
      setCompletedTasks((prev) => {
        const reverted = new Set(prev);
        if (nextCompleted) {
          reverted.delete(key);
        } else {
          reverted.add(key);
        }
        return reverted;
      });
      alert("任务状态保存失败，请重试");
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <Link
        href={`/company/${id}`}
        className="mb-4 inline-flex items-center gap-1 text-sm text-text-muted hover:text-text-secondary"
      >
        <ArrowLeft className="h-4 w-4" />
        返回公司详情
      </Link>

      <h1 className="mb-6 text-2xl font-bold text-text-primary">备战计划</h1>

      <form onSubmit={handleGenerate} className="mb-8 rounded-xl border border-border bg-surface p-6">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium text-text-secondary">
              可用天数
            </label>
            <input
              type="number"
              min={1}
              max={60}
              value={daysAvailable}
              onChange={(e) => setDaysAvailable(Number(e.target.value))}
              className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus"
            />
          </div>
        </div>

        <div className="mt-4">
          <label className="mb-1 block text-sm font-medium text-text-secondary">
            薄弱点
          </label>
          {autoWeakPoints.length > 0 && (
            <div className="mb-2 flex items-center gap-1.5 rounded-md bg-brand-subtle px-3 py-1.5 text-xs text-brand-text">
              <Zap className="h-3 w-3" />
              已自动填充 {autoWeakPoints.length} 个跨轮次薄弱点
            </div>
          )}
          <textarea
            value={weakPoints}
            onChange={(e) => setWeakPoints(e.target.value)}
            rows={3}
            placeholder="逗号分隔，例如：系统设计, 并发编程, 消息队列"
            className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted"
          />
        </div>

        <div className="mt-4">
          <div className="mb-1 flex items-center justify-between">
            <label className="text-sm font-medium text-text-secondary">
              JD 关键方向
            </label>
            {hasJd && (
              <span className="flex items-center gap-1 text-[10px] text-brand-text">
                <Info className="h-3 w-3" />
                AI 将自动从 JD 提取
              </span>
            )}
          </div>
          <textarea
            value={jdDirections}
            onChange={(e) => setJdDirections(e.target.value)}
            rows={3}
            placeholder={hasJd ? "留空将自动从岗位描述提取，也可手动补充..." : "岗位描述中的核心技术方向..."}
            className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted"
          />
        </div>

        <div className="mt-4 flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand px-6 py-2.5 text-sm font-medium text-text-inverse hover:bg-brand-hover disabled:opacity-50"
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            生成计划
          </button>
        </div>
      </form>

      {loading && (
        <div className="flex flex-col items-center justify-center py-16 text-text-muted">
          <Loader2 className="mb-3 h-8 w-8 animate-spin text-brand" />
          <p className="text-sm">AI 正在生成你的备战计划...</p>
        </div>
      )}

      {plan.length > 0 && (
        <div className="space-y-4">
          {plan.map((day) => (
            <div
              key={day.day}
              className="rounded-xl border border-border bg-surface p-5"
            >
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand text-sm font-semibold text-text-inverse">
                    {day.day}
                  </span>
                  <h3 className="text-sm font-semibold text-text-primary">
                    {day.focus}
                  </h3>
                </div>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    priorityColors[day.priority] || "bg-surface-muted text-text-secondary"
                  }`}
                >
                  {priorityLabels[day.priority] || day.priority}
                </span>
              </div>
              <ul className="space-y-2">
                {day.tasks.map((task, i) => {
                  const key = `${day.day}-${i}`;
                  const isCompleted = completedTasks.has(key);
                  const timeMatch = task.match(/\((\d+)\s*(分钟|min)\)/i);
                  const displayTask = timeMatch ? task.replace(/\s*\(\d+\s*(分钟|min)\)/i, "") : task;
                  const minutes = timeMatch ? parseInt(timeMatch[1], 10) : null;

                  return (
                    <li
                      key={i}
                      className={`flex items-start gap-2 rounded-md px-2 py-1.5 text-sm ${
                        isCompleted ? "text-text-muted line-through" : "text-text-secondary"
                      }`}
                    >
                      <button
                        type="button"
                        onClick={() => toggleTask(day.day, i)}
                        className="mt-0.5 shrink-0"
                      >
                        {isCompleted ? (
                          <Check className="h-4 w-4 text-success" />
                        ) : (
                          <Circle className="h-4 w-4 text-text-muted" />
                        )}
                      </button>
                      <span className="flex-1">{displayTask}</span>
                      {minutes && (
                        <span className="flex shrink-0 items-center gap-0.5 text-xs text-text-muted">
                          <Clock className="h-3 w-3" />
                          {minutes}m
                        </span>
                      )}
                    </li>
                  );
                })}
              </ul>
              {day.total_minutes && (
                <div className="mt-3 flex items-center justify-end gap-1 text-xs text-text-muted">
                  <Clock className="h-3 w-3" />
                  总计约 {day.total_minutes} 分钟
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
