"use client";

import { useState } from "react";
import { ArrowRight, Check, X, XCircle, Loader2 } from "lucide-react";
import { companiesApi } from "@/lib/api-client";

interface Company {
  id: string;
  name: string;
  position: string;
  status: string;
}

interface StatusTransitionModalProps {
  company: Company;
  onClose: () => void;
  onTransitioned?: () => void;
}

export function StatusTransitionModal({ company, onClose, onTransitioned }: StatusTransitionModalProps) {
  const isApplied = company.status === "applied";
  const [offerSalary, setOfferSalary] = useState("");
  const [offerDeadline, setOfferDeadline] = useState("");
  const [offerNotes, setOfferNotes] = useState("");
  const [transitioning, setTransitioning] = useState(false);

  async function handleTransition(newStatus: string, offerData?: any) {
    setTransitioning(true);
    try {
      await companiesApi.transitionStatus(company.id, {
        new_status: newStatus,
        offer_data: offerData,
      });
      onTransitioned?.();
      onClose();
    } catch {
      alert("状态更新失败");
    } finally {
      setTransitioning(false);
    }
  }

  function handlePassed() {
    handleTransition("passed", {
      salary: offerSalary,
      deadline: offerDeadline || undefined,
      notes: offerNotes,
      offer_date: new Date().toISOString().split("T")[0],
    });
  }

  function handleRejected() {
    handleTransition("rejected");
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
              onClick={() => handleTransition("interviewing")}
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
