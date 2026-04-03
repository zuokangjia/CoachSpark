"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { ArrowLeft, Loader2, Check, Circle, Clock } from "lucide-react";
import { prepApi, companiesApi, profileApi } from "@/lib/api-client";

interface DailyTask {
  day: number;
  focus: string;
  priority: string;
  tasks: string[];
  total_minutes?: number;
  completed: boolean;
}

const priorityColors: Record<string, string> = {
  high: "bg-red-100 text-red-700",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-green-100 text-green-700",
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
  const [jdDirections, setJdDirections] = useState("");
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState<DailyTask[]>([]);
  const [completedTasks, setCompletedTasks] = useState<Set<string>>(new Set());

  useEffect(() => {
    const r = searchParams.get("round");
    if (r) setTargetRound(Number(r));
    loadExistingData();
  }, [id, searchParams]);

  async function loadExistingData() {
    try {
      const [chainRes, latestPlanRes, profileRes] = await Promise.all([
        companiesApi.getChain(id),
        prepApi.getLatest(id),
        profileApi.get(),
      ]);

      if (chainRes.data?.weak_point_tracking) {
        const persistentWp = Object.entries(chainRes.data.weak_point_tracking)
          .filter(([, d]: [string, any]) => d.is_persistent)
          .map(([wp]: [string, any]) => wp);
        if (persistentWp.length > 0) {
          setWeakPoints(persistentWp.join(", "));
        }
      }

      if (profileRes.data?.weak_points) {
        const decliningOrStable = Object.entries(profileRes.data.weak_points)
          .filter(([, d]: [string, any]) =>
            d.trend === "declining" || (d.trend === "stable" && d.avg_score < 6)
          )
          .map(([wp]: [string, any]) => wp);
        if (decliningOrStable.length > 0 && !weakPoints) {
          setWeakPoints(decliningOrStable.join(", "));
        }
      }

      if (latestPlanRes.data?.daily_tasks?.length > 0) {
        setPlan(latestPlanRes.data.daily_tasks);
        setCompletedTasks(new Set());
      }
    } catch {
      // data loading failure is non-blocking
    }
  }

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    if (!weakPoints.trim() && !jdDirections.trim()) {
      alert("请至少填写薄弱点或 JD 方向");
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
      setPlan(res.data.daily_tasks || []);
      setCompletedTasks(new Set());
    } catch {
      alert("生成失败，请重试");
    } finally {
      setLoading(false);
    }
  }

  function toggleTask(day: number, index: number) {
    const key = `${day}-${index}`;
    setCompletedTasks((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

  return (
    <div className="mx-auto max-w-3xl">
      <Link
        href={`/company/${id}`}
        className="mb-4 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700"
      >
        <ArrowLeft className="h-4 w-4" />
        返回公司详情
      </Link>

      <h1 className="mb-6 text-2xl font-bold text-slate-900">备战计划</h1>

      <form onSubmit={handleGenerate} className="mb-8 rounded-xl border border-slate-200 bg-white p-6">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              可用天数
            </label>
            <input
              type="number"
              min={1}
              max={60}
              value={daysAvailable}
              onChange={(e) => setDaysAvailable(Number(e.target.value))}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="mt-4">
          <label className="mb-1 block text-sm font-medium text-slate-700">
            薄弱点
          </label>
          <textarea
            value={weakPoints}
            onChange={(e) => setWeakPoints(e.target.value)}
            rows={3}
            placeholder="逗号分隔，例如：系统设计, 并发编程, 消息队列"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div className="mt-4">
          <label className="mb-1 block text-sm font-medium text-slate-700">
            JD 关键方向
          </label>
          <textarea
            value={jdDirections}
            onChange={(e) => setJdDirections(e.target.value)}
            rows={3}
            placeholder="岗位描述中的核心技术方向..."
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div className="mt-4 flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-lg bg-amber-500 px-6 py-2.5 text-sm font-medium text-white hover:bg-amber-600 disabled:opacity-50"
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            生成计划
          </button>
        </div>
      </form>

      {loading && (
        <div className="flex flex-col items-center justify-center py-16 text-slate-400">
          <Loader2 className="mb-3 h-8 w-8 animate-spin text-amber-500" />
          <p className="text-sm">AI 正在生成你的备战计划...</p>
        </div>
      )}

      {plan.length > 0 && (
        <div className="space-y-4">
          {plan.map((day) => (
            <div
              key={day.day}
              className="rounded-xl border border-slate-200 bg-white p-5"
            >
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-sm font-semibold text-white">
                    {day.day}
                  </span>
                  <h3 className="text-sm font-semibold text-slate-900">
                    {day.focus}
                  </h3>
                </div>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    priorityColors[day.priority] || "bg-slate-100 text-slate-600"
                  }`}
                >
                  {priorityLabels[day.priority] || day.priority}
                </span>
              </div>
              <ul className="space-y-2">
                {day.tasks.map((task, i) => {
                  const key = `${day.day}-${i}`;
                  const isCompleted = completedTasks.has(key);
                  const timeMatch = task.match(/\((\d+)\s*min\)/);
                  const displayTask = timeMatch ? task.replace(/\s*\(\d+\s*min\)/, "") : task;
                  const minutes = timeMatch ? parseInt(timeMatch[1], 10) : null;

                  return (
                    <li
                      key={i}
                      className={`flex items-start gap-2 rounded-md px-2 py-1.5 text-sm ${
                        isCompleted ? "text-slate-400 line-through" : "text-slate-700"
                      }`}
                    >
                      <button
                        onClick={() => toggleTask(day.day, i)}
                        className="mt-0.5 shrink-0"
                      >
                        {isCompleted ? (
                          <Check className="h-4 w-4 text-green-500" />
                        ) : (
                          <Circle className="h-4 w-4 text-slate-300" />
                        )}
                      </button>
                      <span className="flex-1">{displayTask}</span>
                      {minutes && (
                        <span className="flex shrink-0 items-center gap-0.5 text-xs text-slate-400">
                          <Clock className="h-3 w-3" />
                          {minutes}m
                        </span>
                      )}
                    </li>
                  );
                })}
              </ul>
              {day.total_minutes && (
                <div className="mt-3 flex items-center justify-end gap-1 text-xs text-slate-400">
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
