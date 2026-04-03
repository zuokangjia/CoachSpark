"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, DollarSign, Clock, XCircle, CheckCircle, Trash2, Calendar } from "lucide-react";
import { offersApi } from "@/lib/api-client";
import { formatDate, cn } from "@/lib/utils";

interface Offer {
  id: string;
  company_id: string;
  company_name: string;
  position: string;
  salary: string | null;
  benefits: string | null;
  offer_date: string | null;
  deadline: string | null;
  status: string;
  notes: string | null;
  created_at: string;
}

const statusConfig: Record<string, { label: string; color: string; icon: typeof CheckCircle }> = {
  pending: { label: "待回复", color: "bg-amber-100 text-amber-700", icon: Clock },
  accepted: { label: "已接受", color: "bg-green-100 text-green-700", icon: CheckCircle },
  declined: { label: "已拒绝", color: "bg-red-100 text-red-700", icon: XCircle },
};

export default function OffersPage() {
  const [offers, setOffers] = useState<Offer[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadOffers();
  }, []);

  async function loadOffers() {
    try {
      const res = await offersApi.list();
      setOffers(res.data);
    } catch {
      // non-blocking
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("确定删除此 Offer 记录吗？")) return;
    try {
      await offersApi.delete(id);
      setOffers((prev) => prev.filter((o) => o.id !== id));
    } catch {
      alert("删除失败");
    }
  }

  async function handleStatusChange(id: string, newStatus: string) {
    try {
      await offersApi.update(id, { status: newStatus });
      setOffers((prev) => prev.map((o) => (o.id === id ? { ...o, status: newStatus } : o)));
    } catch {
      alert("更新失败");
    }
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600" />
      </div>
    );
  }

  return (
    <div>
      <Link
        href="/"
        className="mb-4 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700"
      >
        <ArrowLeft className="h-4 w-4" />
        返回看板
      </Link>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Offer 池</h1>
        <p className="mt-1 text-sm text-slate-500">管理你收到的所有 Offer</p>
      </div>

      {offers.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-xl border border-slate-200 bg-white py-16 text-slate-400">
          <DollarSign className="mb-3 h-10 w-10 text-slate-300" />
          <p className="text-sm">暂无 Offer</p>
          <p className="mt-1 text-xs">通过面试后将自动进入 Offer 池</p>
        </div>
      ) : (
        <div className="space-y-4">
          {offers.map((offer) => {
            const status = statusConfig[offer.status] || statusConfig.pending;
            const StatusIcon = status.icon;
            return (
              <div
                key={offer.id}
                className="rounded-xl border border-slate-200 bg-white p-5"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-lg font-semibold text-slate-900">{offer.company_name}</h2>
                      <span className={cn("rounded-full px-2.5 py-0.5 text-xs font-medium", status.color)}>
                        <StatusIcon className="mr-1 inline h-3 w-3" />
                        {status.label}
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-slate-500">{offer.position}</p>
                  </div>
                  <button
                    onClick={() => handleDelete(offer.id)}
                    className="rounded-md p-1 text-slate-400 hover:bg-slate-100 hover:text-red-500"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
                  {offer.salary && (
                    <div className="flex items-center gap-2 text-slate-600">
                      <DollarSign className="h-4 w-4 text-slate-400" />
                      <span>{offer.salary}</span>
                    </div>
                  )}
                  {offer.offer_date && (
                    <div className="flex items-center gap-2 text-slate-600">
                      <Calendar className="h-4 w-4 text-slate-400" />
                      <span>Offer 日期: {formatDate(offer.offer_date)}</span>
                    </div>
                  )}
                  {offer.deadline && (
                    <div className="flex items-center gap-2 text-slate-600">
                      <Clock className="h-4 w-4 text-slate-400" />
                      <span>截止: {formatDate(offer.deadline)}</span>
                    </div>
                  )}
                </div>

                {offer.notes && (
                  <p className="mt-3 text-sm text-slate-500">{offer.notes}</p>
                )}

                {offer.status === "pending" && (
                  <div className="mt-4 flex gap-2">
                    <button
                      onClick={() => handleStatusChange(offer.id, "accepted")}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
                    >
                      <CheckCircle className="h-4 w-4" />
                      接受
                    </button>
                    <button
                      onClick={() => handleStatusChange(offer.id, "declined")}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50"
                    >
                      <XCircle className="h-4 w-4" />
                      拒绝
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
