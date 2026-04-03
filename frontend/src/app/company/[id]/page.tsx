"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Plus, FileText, Lightbulb, Loader2, Calendar, Video, Phone, MapPin, X } from "lucide-react";
import { companiesApi, interviewsApi } from "@/lib/api-client";
import { formatDate, cn } from "@/lib/utils";

interface Interview {
  id: string;
  round: number;
  interview_date: string | null;
  format: string | null;
  interviewer: string | null;
  raw_notes: string | null;
}

interface Company {
  id: string;
  name: string;
  position: string;
  status: string;
  applied_date: string | null;
  next_event_date: string | null;
  next_event_type: string | null;
  notes: string | null;
}

const statusColors: Record<string, string> = {
  applied: "bg-blue-100 text-blue-700",
  interviewing: "bg-amber-100 text-amber-700",
  closed: "bg-slate-100 text-slate-600",
};

const statusLabels: Record<string, string> = {
  applied: "已投递",
  interviewing: "面试中",
  closed: "已结束",
};

const formatIcons: Record<string, typeof Phone> = {
  phone: Phone,
  video: Video,
  onsite: MapPin,
};

export default function CompanyDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [company, setCompany] = useState<Company | null>(null);
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddInterview, setShowAddInterview] = useState(false);

  useEffect(() => {
    loadCompany();
  }, [id]);

  async function loadCompany() {
    setLoading(true);
    try {
      const [companyRes, interviewsRes] = await Promise.all([
        companiesApi.get(id),
        interviewsApi.list(id),
      ]);
      setCompany(companyRes.data);
      setInterviews(interviewsRes.data.sort((a: Interview, b: Interview) => a.round - b.round));
    } catch {
      alert("加载失败");
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
      </div>
    );
  }

  if (!company) return null;

  return (
    <div>
      <Link
        href="/"
        className="mb-4 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700"
      >
        <ArrowLeft className="h-4 w-4" />
        返回看板
      </Link>

      <div className="mb-6 rounded-xl border border-slate-200 bg-white p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">{company.name}</h1>
            <p className="mt-1 text-slate-500">{company.position}</p>
          </div>
          <span
            className={cn(
              "rounded-full px-3 py-1 text-xs font-medium",
              statusColors[company.status] || "bg-slate-100 text-slate-600",
            )}
          >
            {statusLabels[company.status] || company.status}
          </span>
        </div>

        <div className="mt-4 flex flex-wrap gap-4 text-sm text-slate-500">
          {company.applied_date && (
            <span className="flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              投递日期: {formatDate(company.applied_date)}
            </span>
          )}
          {company.next_event_date && (
            <span className="flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              下次事件: {company.next_event_type || "—"} · {formatDate(company.next_event_date)}
            </span>
          )}
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <button
            onClick={() => setShowAddInterview(true)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            <Plus className="h-4 w-4" />
            添加面试
          </button>
          <Link
            href={`/company/${id}/review`}
            className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
          >
            <FileText className="h-4 w-4" />
            面试复盘
          </Link>
          <Link
            href={`/company/${id}/prep`}
            className="inline-flex items-center gap-1.5 rounded-lg bg-amber-500 px-3 py-1.5 text-sm font-medium text-white hover:bg-amber-600"
          >
            <Lightbulb className="h-4 w-4" />
            生成备战计划
          </Link>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold text-slate-900">面试记录</h2>
        {interviews.length === 0 ? (
          <p className="py-8 text-center text-sm text-slate-400">暂无面试记录</p>
        ) : (
          <div className="space-y-3">
            {interviews.map((interview) => {
              const FormatIcon = formatIcons[interview.format || ""] || Calendar;
              return (
                <div
                  key={interview.id}
                  className="flex items-center gap-4 rounded-lg border border-slate-100 bg-slate-50 p-4"
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 text-sm font-semibold text-blue-700">
                    {interview.round}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-slate-900">
                        第 {interview.round} 轮
                      </span>
                      <span className="inline-flex items-center gap-1 rounded bg-white px-2 py-0.5 text-xs text-slate-500">
                        <FormatIcon className="h-3 w-3" />
                        {interview.format || "—"}
                      </span>
                    </div>
                    <div className="mt-1 text-xs text-slate-500">
                      {interview.interview_date && (
                        <span>{formatDate(interview.interview_date)}</span>
                      )}
                      {interview.interviewer && (
                        <span className="ml-2">· {interview.interviewer}</span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {showAddInterview && (
        <AddInterviewModal
          companyId={id}
          onClose={() => setShowAddInterview(false)}
          onAdded={loadCompany}
        />
      )}
    </div>
  );
}

function AddInterviewModal({
  companyId,
  onClose,
  onAdded,
}: {
  companyId: string;
  onClose: () => void;
  onAdded: () => void;
}) {
  const [round, setRound] = useState(1);
  const [interviewDate, setInterviewDate] = useState("");
  const [format, setFormat] = useState("video");
  const [interviewer, setInterviewer] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload: Record<string, unknown> = { round, format };
      if (interviewDate) payload.interview_date = interviewDate;
      if (interviewer.trim()) payload.interviewer = interviewer.trim();
      await interviewsApi.create(companyId, payload);
      onAdded();
      onClose();
    } catch {
      alert("添加失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">添加面试</h2>
          <button onClick={onClose} className="rounded-md p-1 text-slate-400 hover:bg-slate-100">
            <X className="h-4 w-4" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">轮次</label>
            <input
              type="number"
              min={1}
              value={round}
              onChange={(e) => setRound(Number(e.target.value))}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">日期</label>
            <input
              type="date"
              value={interviewDate}
              onChange={(e) => setInterviewDate(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">形式</label>
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            >
              <option value="phone">电话</option>
              <option value="video">视频</option>
              <option value="onsite">现场</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">面试官</label>
            <input
              type="text"
              value={interviewer}
              onChange={(e) => setInterviewer(e.target.value)}
              placeholder="可选"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
              添加
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
