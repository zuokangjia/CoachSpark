"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
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
import { Plus, Loader2 } from "lucide-react";
import { useCompanyStore } from "@/lib/store/company-store";
import { COLUMNS, cn } from "@/lib/utils";
import { companiesApi } from "@/lib/api-client";
import { CompanyCard } from "./components/company-card";
import { AddCompanyModal } from "./components/add-company-modal";

export default function DashboardPage() {
  const { companies, loading, fetchCompanies, moveCompany } = useCompanyStore();
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    fetchCompanies();
  }, []);

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
    } catch {
      alert("Failed to update status");
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
          Add Company
        </button>
      </div>

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

      {showModal && <AddCompanyModal onClose={() => setShowModal(false)} />}
    </div>
  );
}
