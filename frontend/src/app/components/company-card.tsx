"use client";

import { useState, useRef, useEffect } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import Link from "next/link";
import { Calendar, Clock, MoreHorizontal, Pencil, Trash2, X, ArrowRight, Check, XCircle, Loader2, ChevronDown } from "lucide-react";
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

const statusColors: Record<string, string> = {
  applied: "bg-blue-100 text-blue-700",
  interviewing: "bg-amber-100 text-amber-700",
  passed: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
};

const statusLabels: Record<string, string> = {
  applied: "已投递",
  interviewing: "面试中",
  passed: "已通过",
  rejected: "被拒绝",
};

const allStatuses = ["applied", "interviewing", "passed", "rejected"] as const;

export function CompanyCard({ company, onStatusChanged, onDeleted, onSaved }: {
  company: Company;
  onStatusChanged?: () => void;
  onDeleted?: (id: string) => void;
  onSaved?: () => void;
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: company.id });

  const [showMenu, setShowMenu] = useState(false);
  const [showStatusDropdown, setShowStatusDropdown] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [showTransition, setShowTransition] = useState(false);
  const [transitioning, setTransitioning] = useState(false);
  const statusRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (statusRef.current && !statusRef.current.contains(e.target as Node)) {
        setShowStatusDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  async function handleDelete() {
    if (!confirm("确定删除 " + company.name + " 吗？此操作不可撤销。")) return;
    try {
      await companiesApi.delete(company.id);
      onDeleted?.(company.id);
    } catch {
      alert("删除失败");
    }
  }

  async function handleTransition(newStatus: string, offerData?: any) {
    setTransitioning(true);
    try {
      await companiesApi.transitionStatus(company.id, {
        new_status: newStatus,
        offer_data: offerData,
      });
      setShowTransition(false);
      onStatusChanged?.();
    } catch {
      alert("状态更新失败");
    } finally {
      setTransitioning(false);
    }
  }

  const canAdvance = company.status === "applied" || company.status === "interviewing";

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
        <div className="absolute right-2 top-2 z-10 flex items-center gap-1">
          {canAdvance && (
            <button
              onClick={(e) => { e.stopPropagation(); setShowTransition(true); }}
              className="inline-flex items-center gap-1 rounded-md bg-blue-600 px-2 py-1 text-[10px] font-medium text-white opacity-0 hover:bg-blue-700 group-hover:opacity-100"
              title="推进流程"
            >
              <ArrowRight className="h-3 w-3" />
              推进
            </button>
          )}
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

        <Link href={"/company/" + company.id}>
          <div {...attributes} {...listeners} className="cursor-grab active:cursor-grabbing">
            <div className="flex items-center gap-2 pr-20">
              <h3 className="text-sm font-semibold text-slate-900">{company.name}</h3>
              <div ref={statusRef} className="relative">
                <button
                  onClick={(e) => { e.stopPropagation(); setShowStatusDropdown(!showStatusDropdown); }}
                  className={cn("inline-flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-[10px] font-medium", statusColors[company.status] || "bg-slate-100 text-slate-600")}
                >
                  {statusLabels[company.status] || company.status}
                  <ChevronDown className="h-2.5 w-2.5" />
                </button>
                {showStatusDropdown && (
                  <div className="absolute left-0 z-30 mt-1 w-28 rounded-lg border border-slate-200 bg-white py-1 shadow-lg">
                    {allStatuses.map((s) => (
                      <div
                        key={s}
                        className={cn(
                          "flex items-center gap-2 px-3 py-1.5 text-xs",
                          company.status === s
                            ? "font-medium text-slate-900"
                            : "text-slate-400",
                        )}
                      >
                        <span className={cn("h-2 w-2 rounded-full", s === "applied" ? "bg-blue-500" : s === "interviewing" ? "bg-amber-500" : s === "passed" ? "bg-green-500" : "bg-red-500")} />
                        {statusLabels[s]}
                        {company.status === s && <Check className="ml-auto h-3 w-3 text-blue-600" />}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
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

      {showTransition && (
        <StatusTransitionModal
          company={company}
          onClose={() => setShowTransition(false)}
          onTransition={handleTransition}
          transitioning={transitioning}
        />
      )}
    </>
  );
}

function StatusTransitionModal({
  company,
  onClose,
  onTransition,
  transitioning,
}: {
  company: Company;
  onClose: () => void;
  onTransition: (status: string, offerData?: any) => void;
  transitioning: boolean;
}) {
  const isApplied = company.status === "applied";
  const [offerSalary, setOfferSalary] = useState("");
  const [offerDeadline, setOfferDeadline] = useState("");
  const [offerNotes, setOfferNotes] = useState("");

  function handlePassed() {
    onTransition("passed", {
      salary: offerSalary,
      deadline: offerDeadline || undefined,
      notes: offerNotes,
      offer_date: new Date().toISOString().split("T")[0],
    });
  }

  function handleRejected() {
    onTransition("rejected");
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-lg" onClick={(e) => e.stopPropagation()}>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">
            {isApplied ? "确认面试邀请" : "面试结果"}
          </h2>
          <button onClick={onClose} className="rounded-md p-1 text-slate-400 hover:bg-slate-100">
            <X className="h-4 w-4" />
          </button>
        </div>

        <p className="mb-4 text-sm text-slate-500">
          {isApplied
            ? company.name + " - " + company.position + " 是否已进入面试阶段？"
            : company.name + " - " + company.position + " 的面试结果如何？"}
        </p>

        {isApplied ? (
          <div className="flex gap-3">
            <button
              onClick={() => onTransition("interviewing")}
              disabled={transitioning}
              className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-lg bg-amber-500 px-4 py-3 text-sm font-medium text-white hover:bg-amber-600 disabled:opacity-50"
            >
              {transitioning ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
              进入面试
            </button>
            <button
              onClick={onClose}
              className="rounded-lg border border-slate-300 px-4 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              取消
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={handlePassed}
                disabled={transitioning}
                className="flex items-center justify-center gap-2 rounded-lg border-2 border-green-300 bg-green-50 px-4 py-4 text-sm font-medium text-green-700 hover:bg-green-100 disabled:opacity-50"
              >
                {transitioning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-5 w-5" />}
                通过
              </button>
              <button
                onClick={handleRejected}
                disabled={transitioning}
                className="flex items-center justify-center gap-2 rounded-lg border-2 border-red-300 bg-red-50 px-4 py-4 text-sm font-medium text-red-700 hover:bg-red-100 disabled:opacity-50"
              >
                {transitioning ? <Loader2 className="h-4 w-4 animate-spin" /> : <XCircle className="h-5 w-5" />}
                拒绝
              </button>
            </div>

            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-3">
              <p className="text-xs font-medium text-slate-600">Offer 信息（选填）</p>
              <div>
                <label className="mb-1 block text-xs text-slate-500">薪资</label>
                <input
                  type="text"
                  value={offerSalary}
                  onChange={(e) => setOfferSalary(e.target.value)}
                  placeholder="例如：25k x 16"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-slate-500">回复截止日期</label>
                <input
                  type="date"
                  value={offerDeadline}
                  onChange={(e) => setOfferDeadline(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-slate-500">备注</label>
                <input
                  type="text"
                  value={offerNotes}
                  onChange={(e) => setOfferNotes(e.target.value)}
                  placeholder="可选"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
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
