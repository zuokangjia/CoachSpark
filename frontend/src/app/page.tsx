"use client";

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
import { Plus, Loader2, Building2, Calendar, TrendingUp, AlertTriangle } from "lucide-react";
import { useCompanyStore } from "@/lib/store/company-store";
import { COLUMNS, cn } from "@/lib/utils";
import { companiesApi, dashboardApi } from "@/lib/api-client";
import { CompanyCard } from "./components/company-card";
import { AddCompanyModal } from "./components/add-company-modal";

interface DashboardStats {
  total_companies: number;
  applied: number;
  interviewing: number;
  closed: number;
  total_interviews: number;
  top_weak_points: [string, number][];
}

export default function DashboardPage() {
  const { companies, loading, fetchCompanies, moveCompany } = useCompanyStore();
  const [showModal, setShowModal] = useState(false);
  const [stats, setStats] = useState<DashboardStats | null>(null);

  useEffect(() => {
    fetchCompanies();
    loadStats();
  }, []);

  async function loadStats() {
    try {
      const res = await dashboardApi.stats();
      setStats(res.data);
    } catch {
      // stats load failure is non-blocking
    }
  }

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
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">投递看板</h1>
          <p className="mt-1 text-sm text-slate-500">
            管理你的所有投递和面试进度
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          添加公司
        </button>
      </div>

      {stats && (
        <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
          <StatCard
            icon={Building2}
            label="总投递"
            value={stats.total_companies}
            color="text-blue-600"
            bg="bg-blue-50"
          />
          <StatCard
            icon={Calendar}
            label="面试中"
            value={stats.interviewing}
            color="text-amber-600"
            bg="bg-amber-50"
          />
          <StatCard
            icon={TrendingUp}
            label="已完成"
            value={stats.closed}
            color="text-green-600"
            bg="bg-green-50"
          />
          <StatCard
            icon={AlertTriangle}
            label="面试总数"
            value={stats.total_interviews}
            color="text-purple-600"
            bg="bg-purple-50"
          />
        </div>
      )}

      {stats && stats.top_weak_points.length > 0 && (
        <div className="mb-6 rounded-xl border border-slate-200 bg-white p-4">
          <h3 className="mb-2 text-sm font-semibold text-slate-700">薄弱点 TOP 5</h3>
          <div className="flex flex-wrap gap-1.5">
            {stats.top_weak_points.map(([wp, count]) => (
              <span
                key={wp}
                className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2.5 py-1 text-xs text-red-700"
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
                  <h2 className="text-sm font-semibold text-slate-700">
                    {col.title}
                  </h2>
                  <span className="rounded-full bg-white/70 px-2 py-0.5 text-xs font-medium text-slate-500">
                    {colCompanies.length}
                  </span>
                </div>
                <SortableContext
                  items={colCompanies.map((c) => c.id)}
                  strategy={verticalListSortingStrategy}
                >
                  <div className="flex flex-col gap-2">
                    {colCompanies.map((company) => (
                      <CompanyCard key={company.id} company={company} />
                    ))}
                  </div>
                </SortableContext>
                {colCompanies.length === 0 && (
                  <div className="flex flex-1 items-center justify-center py-8 text-xs text-slate-400">
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
    <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-4">
      <div className={cn("flex h-10 w-10 items-center justify-center rounded-lg", bg)}>
        <Icon className={cn("h-5 w-5", color)} />
      </div>
      <div>
        <p className="text-xs text-slate-500">{label}</p>
        <p className="text-lg font-semibold text-slate-900">{value}</p>
      </div>
    </div>
  );
}
