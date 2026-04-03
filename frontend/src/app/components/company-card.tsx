"use client";

import { useState } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import Link from "next/link";
import { Calendar, Clock, MoreHorizontal, Pencil, Trash2, X } from "lucide-react";
import { formatDate, cn } from "@/lib/utils";
import { companiesApi } from "@/lib/api-client";

interface Company {
  id: string;
  name: string;
  position: string;
  status: string;
  applied_date: string | null;
  next_event_date: string | null;
  next_event_type: string | null;
  notes: string | null;
  jd_text: string | null;
}

export function CompanyCard({ company, onDeleted, onSaved }: { company: Company; onDeleted?: (id: string) => void; onSaved?: () => void }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: company.id });

  const [showMenu, setShowMenu] = useState(false);
  const [showEdit, setShowEdit] = useState(false);

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  async function handleDelete() {
    if (!confirm(`确定删除 ${company.name} 吗？此操作不可撤销。`)) return;
    try {
      await companiesApi.delete(company.id);
      onDeleted?.(company.id);
    } catch {
      alert("删除失败");
    }
  }

  return (
    <>
      <div
        ref={setNodeRef}
        style={style}
        className={cn(
          "group relative rounded-lg border border-slate-200 bg-white p-3 transition-colors",
          "hover:border-slate-300 hover:shadow-sm",
          isDragging && "opacity-50",
        )}
      >
        <div className="absolute right-2 top-2 z-10">
          <button
            onClick={(e) => { e.stopPropagation(); setShowMenu(!showMenu); }}
            className="rounded p-0.5 text-slate-400 opacity-0 hover:bg-slate-100 hover:text-slate-600 group-hover:opacity-100"
          >
            <MoreHorizontal className="h-4 w-4" />
          </button>
          {showMenu && (
            <div className="absolute right-0 z-20 mt-1 w-32 rounded-lg border border-slate-200 bg-white py-1 shadow-lg">
              <button
                onClick={(e) => { e.stopPropagation(); setShowMenu(false); setShowEdit(true); }}
                className="flex w-full items-center gap-2 px-3 py-1.5 text-left text-xs text-slate-600 hover:bg-slate-50"
              >
                <Pencil className="h-3 w-3" />
                编辑
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); setShowMenu(false); handleDelete(); }}
                className="flex w-full items-center gap-2 px-3 py-1.5 text-left text-xs text-red-600 hover:bg-red-50"
              >
                <Trash2 className="h-3 w-3" />
                删除
              </button>
            </div>
          )}
        </div>

        <Link href={`/company/${company.id}`}>
          <div {...attributes} {...listeners} className="cursor-grab active:cursor-grabbing">
            <h3 className="pr-6 text-sm font-semibold text-slate-900">{company.name}</h3>
            <p className="mt-0.5 text-xs text-slate-500">{company.position}</p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {company.applied_date && (
                <span className="inline-flex items-center gap-1 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-600">
                  <Calendar className="h-3 w-3" />
                  {formatDate(company.applied_date)}
                </span>
              )}
              {company.next_event_date && (
                <span className="inline-flex items-center gap-1 rounded bg-blue-50 px-1.5 py-0.5 text-[10px] text-blue-700">
                  <Clock className="h-3 w-3" />
                  {company.next_event_type || "事件"} · {formatDate(company.next_event_date)}
                </span>
              )}
            </div>
          </div>
        </Link>
      </div>

      {showEdit && (
        <EditCompanyModal
          company={company}
          onClose={() => setShowEdit(false)}
          onSaved={() => { setShowEdit(false); onSaved?.(); }}
        />
      )}
    </>
  );
}

function EditCompanyModal({
  company,
  onClose,
  onSaved,
}: {
  company: Company;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [name, setName] = useState(company.name);
  const [position, setPosition] = useState(company.position);
  const [jdText, setJdText] = useState(company.jd_text || "");
  const [notes, setNotes] = useState(company.notes || "");
  const [appliedDate, setAppliedDate] = useState(company.applied_date || "");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() || !position.trim()) {
      alert("请填写公司名和岗位名");
      return;
    }
    setSubmitting(true);
    try {
      const payload: Record<string, unknown> = { name: name.trim(), position: position.trim() };
      if (jdText.trim()) payload.jd_text = jdText.trim();
      if (notes.trim()) payload.notes = notes.trim();
      if (appliedDate) payload.applied_date = appliedDate;
      await companiesApi.update(company.id, payload);
      onSaved();
    } catch {
      alert("更新失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-lg" onClick={(e) => e.stopPropagation()}>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">编辑公司</h2>
          <button onClick={onClose} className="rounded-md p-1 text-slate-400 hover:bg-slate-100">
            <X className="h-4 w-4" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">公司名</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">岗位名</label>
            <input type="text" value={position} onChange={(e) => setPosition(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">岗位描述</label>
            <textarea value={jdText} onChange={(e) => setJdText(e.target.value)} rows={3} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">备注</label>
            <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">投递日期</label>
            <input type="date" value={appliedDate} onChange={(e) => setAppliedDate(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">取消</button>
            <button type="submit" disabled={submitting} className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">保存</button>
          </div>
        </form>
      </div>
    </div>
  );
}
