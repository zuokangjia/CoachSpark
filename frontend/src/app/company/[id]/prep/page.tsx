"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import {
  ArrowLeft,
  Loader2,
  Check,
  Circle,
  Clock,
  Zap,
  Info,
  Plus,
  Trash2,
  Pencil,
  GripVertical,
  Calendar,
  XCircle,
} from "lucide-react";
import { prepApi, companiesApi, profileApi } from "@/lib/api-client";
import { cn } from "@/lib/utils";

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
  const [editingDay, setEditingDay] = useState<number | null>(null);
  const [editingTasks, setEditingTasks] = useState<string[]>([]);
  const [addingTaskDay, setAddingTaskDay] = useState<number | null>(null);
  const [newTaskText, setNewTaskText] = useState("");

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

  // 判断上下文来源
  const hasReviewContext = searchParams.get("weak_points") !== null;
  const hasAutoWeakPoints = autoWeakPoints.length > 0;
  const hasAnyWeakPoints = weakPoints.trim().length > 0 || hasAutoWeakPoints;

  return (
    <div className="mx-auto max-w-3xl">
      <Link
        href={`/company/${id}`}
        className="mb-4 inline-flex items-center gap-1 text-sm text-text-muted hover:text-text-secondary"
      >
        <ArrowLeft className="h-4 w-4" />
        返回公司详情
      </Link>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-text-primary">备战计划</h1>
        <p className="mt-1 text-sm text-text-secondary">
          第 {targetRound} 轮面试准备
          {hasReviewContext && (
            <span className="ml-2 inline-flex items-center gap-1 rounded-full bg-brand-subtle px-2 py-0.5 text-xs text-brand-text">
              <Zap className="h-3 w-3" />
              基于复盘生成
            </span>
          )}
        </p>
      </div>

      {/* 生成配置区 - 有计划时折叠 */}
      {plan.length === 0 && (
        <form onSubmit={handleGenerate} className="mb-8 rounded-xl border border-border bg-surface p-6">
          {/* 目标轮次 */}
          <div className="mb-5">
            <label className="mb-2 block text-sm font-medium text-text-secondary">
              目标轮次
            </label>
            <div className="flex gap-3">
              {[1, 2, 3, 4, 5].map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => setTargetRound(r)}
                  className={cn(
                    "h-10 w-10 rounded-lg border text-sm font-medium transition-colors",
                    targetRound === r
                      ? "border-brand bg-brand text-text-inverse"
                      : "border-border bg-surface text-text-secondary hover:border-brand hover:text-brand"
                  )}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          {/* 薄弱点 - 核心输入 */}
          <div className="mb-5">
            <div className="mb-2 flex items-center justify-between">
              <label className="text-sm font-medium text-text-secondary">
                薄弱点 <span className="text-error">*</span>
              </label>
              {!hasAnyWeakPoints && (
                <span className="text-xs text-text-muted">输入你想针对性提高的方向</span>
              )}
            </div>

            {/* 自动检测的薄弱点 chips */}
            {hasAutoWeakPoints && (
              <div className="mb-2 flex flex-wrap gap-1.5">
                {autoWeakPoints.map((wp, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => {
                      setAutoWeakPoints(autoWeakPoints.filter((_, idx) => idx !== i));
                      const newList = autoWeakPoints.filter((_, idx) => idx !== i);
                      setWeakPoints(newList.join(", "));
                    }}
                    className="inline-flex items-center gap-1 rounded-full bg-error-bg px-2.5 py-1 text-xs text-error-text hover:bg-error/20"
                  >
                    {wp}
                    <XCircle className="h-3 w-3" />
                  </button>
                ))}
              </div>
            )}

            <textarea
              value={weakPoints}
              onChange={(e) => setWeakPoints(e.target.value)}
              rows={2}
              placeholder="系统设计, 并发编程, 数据库优化..."
              className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted"
            />
          </div>

          {/* JD 方向 - 次要输入 */}
          <div className="mb-5">
            <div className="mb-2 flex items-center justify-between">
              <label className="text-sm font-medium text-text-secondary">
                岗位重点方向
              </label>
              {hasJd ? (
                <span className="flex items-center gap-1 text-xs text-brand-text">
                  <Info className="h-3 w-3" />
                  已从 JD 提取
                </span>
              ) : (
                <span className="text-xs text-text-muted">可选</span>
              )}
            </div>
            <textarea
              value={jdDirections}
              onChange={(e) => setJdDirections(e.target.value)}
              rows={2}
              placeholder={hasJd ? "已在公司 JD 中提取，可补充..." : "核心技术栈、业务场景..."}
              className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted"
            />
          </div>

          {/* 可用天数 */}
          <div className="mb-5">
            <label className="mb-2 block text-sm font-medium text-text-secondary">
              准备时间
            </label>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min={3}
                max={14}
                value={daysAvailable}
                onChange={(e) => setDaysAvailable(Number(e.target.value))}
                className="flex-1"
              />
              <span className="w-16 rounded-lg border border-border bg-surface px-3 py-1.5 text-center text-sm text-text-primary">
                {daysAvailable} 天
              </span>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={loading || !hasAnyWeakPoints}
              className="inline-flex items-center gap-1.5 rounded-lg bg-brand px-6 py-2.5 text-sm font-medium text-text-inverse hover:bg-brand-hover disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              生成备战计划
            </button>
          </div>
        </form>
      )}

      {/* 有计划时显示快捷操作 */}
      {plan.length > 0 && (
        <div className="mb-6 flex gap-3">
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              handleGenerate(e as any);
            }}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-surface px-4 py-2 text-sm font-medium text-text-secondary hover:bg-surface-muted disabled:opacity-50"
          >
            <Loader2 className={cn("h-4 w-4", loading ? "animate-spin" : "")} />
            重新生成
          </button>
          <Link
            href={`/company/${id}`}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-surface px-4 py-2 text-sm font-medium text-text-secondary hover:bg-surface-muted"
          >
            返回公司
          </Link>
        </div>
      )}

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
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-text-muted" />
                    <h3 className="text-sm font-semibold text-text-primary">
                      {day.focus}
                    </h3>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      priorityColors[day.priority] || "bg-surface-muted text-text-secondary"
                    }`}
                  >
                    {priorityLabels[day.priority] || day.priority}
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      setEditingDay(day.day);
                      setEditingTasks([...day.tasks]);
                    }}
                    className="rounded-md p-1.5 text-text-muted hover:bg-surface-muted hover:text-text-primary"
                  >
                    <Pencil className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {editingDay === day.day ? (
                // 编辑模式
                <div className="space-y-2">
                  {editingTasks.map((task, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <GripVertical className="h-4 w-4 shrink-0 cursor-grab text-text-muted" />
                      <input
                        type="text"
                        value={task}
                        onChange={(e) => {
                          const updated = [...editingTasks];
                          updated[i] = e.target.value;
                          setEditingTasks(updated);
                        }}
                        className="flex-1 rounded-lg border border-input-border bg-input-bg px-3 py-1.5 text-sm text-text-primary outline-none focus:border-input-focus"
                      />
                      <button
                        type="button"
                        onClick={() => {
                          const updated = editingTasks.filter((_, idx) => idx !== i);
                          setEditingTasks(updated);
                        }}
                        className="rounded-md p-1 text-text-muted hover:text-error"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                  <div className="flex gap-2 pt-2">
                    <button
                      type="button"
                      onClick={() => {
                        setEditingDay(null);
                        setEditingTasks([]);
                      }}
                      className="flex-1 rounded-lg border border-border px-3 py-1.5 text-xs text-text-secondary hover:bg-surface-muted"
                    >
                      取消
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        const updatedPlan = plan.map((d) =>
                          d.day === day.day ? { ...d, tasks: editingTasks.filter(Boolean) } : d
                        );
                        setPlan(updatedPlan);
                        setEditingDay(null);
                        setEditingTasks([]);
                      }}
                      className="flex-1 rounded-lg bg-brand px-3 py-1.5 text-xs font-medium text-text-inverse hover:bg-brand-hover"
                    >
                      保存
                    </button>
                  </div>
                </div>
              ) : (
                // 查看模式
                <>
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
                          className={cn(
                            "flex items-start gap-2 rounded-md px-2 py-1.5 text-sm",
                            isCompleted ? "text-text-muted line-through" : "text-text-secondary"
                          )}
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
                  {addingTaskDay === day.day ? (
                    <div className="mt-3 flex gap-2">
                      <input
                        type="text"
                        value={newTaskText}
                        onChange={(e) => setNewTaskText(e.target.value)}
                        placeholder="输入新任务..."
                        className="flex-1 rounded-lg border border-input-border bg-input-bg px-3 py-1.5 text-sm text-text-primary outline-none focus:border-input-focus"
                        autoFocus
                        onKeyDown={(e) => {
                          if (e.key === "Enter" && newTaskText.trim()) {
                            const updatedPlan = plan.map((d) =>
                              d.day === day.day
                                ? { ...d, tasks: [...d.tasks, newTaskText.trim()] }
                                : d
                            );
                            setPlan(updatedPlan);
                            setAddingTaskDay(null);
                            setNewTaskText("");
                          }
                          if (e.key === "Escape") {
                            setAddingTaskDay(null);
                            setNewTaskText("");
                          }
                        }}
                      />
                      <button
                        type="button"
                        onClick={() => {
                          if (newTaskText.trim()) {
                            const updatedPlan = plan.map((d) =>
                              d.day === day.day
                                ? { ...d, tasks: [...d.tasks, newTaskText.trim()] }
                                : d
                            );
                            setPlan(updatedPlan);
                          }
                          setAddingTaskDay(null);
                          setNewTaskText("");
                        }}
                        className="rounded-lg bg-brand px-3 py-1.5 text-sm font-medium text-text-inverse hover:bg-brand-hover"
                      >
                        添加
                      </button>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setAddingTaskDay(day.day)}
                      className="mt-3 flex w-full items-center justify-center gap-1 rounded-lg border border-dashed border-border py-2 text-xs text-text-muted hover:border-brand hover:text-brand"
                    >
                      <Plus className="h-4 w-4" />
                      添加任务
                    </button>
                  )}
                </>
              )}

              {day.total_minutes && !editingDay && (
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
