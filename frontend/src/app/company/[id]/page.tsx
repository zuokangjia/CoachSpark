"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  Plus,
  Lightbulb,
  Loader2,
  Calendar,
  Video,
  Phone,
  MapPin,
  X,
  AlertTriangle,
  FileText,
  ChevronRight,
  BookOpen,
  Target,
  CheckCircle,
  ChevronDown,
} from "lucide-react";
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

interface WeakPointTracking {
  [key: string]: {
    count: number;
    first_round: number;
    last_round: number;
    is_persistent: boolean;
  };
}

interface ChainData {
  rounds: Array<{
    id: string;
    round: number;
    interview_date: string | null;
    format: string | null;
    interviewer: string | null;
    weak_points: string[];
    strong_points: string[];
    questions_count: number;
  }>;
  weak_point_tracking: WeakPointTracking;
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

const formatIcons: Record<string, typeof Phone> = {
  phone: Phone,
  video: Video,
  onsite: MapPin,
};

export default function CompanyDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [company, setCompany] = useState<Company | null>(null);
  const [chain, setChain] = useState<ChainData | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAddInterview, setShowAddInterview] = useState(false);
  const [showBrief, setShowBrief] = useState(false);
  const [briefData, setBriefData] = useState<any>(null);
  const [showRejection, setShowRejection] = useState(false);
  const [rejectionData, setRejectionData] = useState<any>(null);
  const [showStatusMenu, setShowStatusMenu] = useState(false);
  const [statusUpdating, setStatusUpdating] = useState(false);

  useEffect(() => {
    loadData();
  }, [id]);

  async function loadData() {
    setLoading(true);
    try {
      const [companyRes, chainRes] = await Promise.all([
        companiesApi.get(id),
        companiesApi.getChain(id),
      ]);
      setCompany(companyRes.data);
      setChain(chainRes.data);
    } catch {
      alert("加载失败");
    } finally {
      setLoading(false);
    }
  }

  async function updateStatus(newStatus: string) {
    setStatusUpdating(true);
    try {
      await companiesApi.update(id, { status: newStatus });
      setCompany((prev) => (prev ? { ...prev, status: newStatus } : null));
      setShowStatusMenu(false);
      if (newStatus === "rejected") {
        const res = await companiesApi.getRejectionAnalysis(id);
        setRejectionData(res.data);
        setShowRejection(true);
      }
    } catch {
      alert("状态更新失败");
    } finally {
      setStatusUpdating(false);
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

  const totalRounds = chain?.rounds.length ?? 0;

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

          <div className="relative">
            <button
              onClick={() => setShowStatusMenu(!showStatusMenu)}
              disabled={statusUpdating}
              className={cn(
                "inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium transition-colors",
                statusColors[company.status] || "bg-slate-100 text-slate-600",
              )}
            >
              {statusLabels[company.status] || company.status}
              <ChevronDown className="h-3 w-3" />
            </button>

            {showStatusMenu && (
              <div className="absolute right-0 z-50 mt-1 w-40 rounded-lg border border-slate-200 bg-white py-1 shadow-lg">
                {(["applied", "interviewing", "passed", "rejected"] as const).map(
                  (s) => (
                    <button
                      key={s}
                      onClick={() => updateStatus(s)}
                      className={cn(
                        "flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-slate-50",
                        company.status === s
                          ? "font-medium text-slate-900"
                          : "text-slate-600",
                      )}
                    >
                      <span
                        className={cn(
                          "h-2 w-2 rounded-full",
                          s === "applied"
                            ? "bg-blue-500"
                            : s === "interviewing"
                              ? "bg-amber-500"
                              : s === "passed"
                                ? "bg-green-500"
                                : "bg-red-500",
                        )}
                      />
                      {statusLabels[s]}
                    </button>
                  ),
                )}
              </div>
            )}
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-4 text-sm text-slate-500">
          {company.applied_date && (
            <span className="flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              投递日期: {formatDate(company.applied_date)}
            </span>
          )}
          <span className="flex items-center gap-1">
            <FileText className="h-4 w-4" />
            面试轮次: {totalRounds}
          </span>
          {company.next_event_date && (
            <span className="flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              下次事件: {company.next_event_type || "—"} ·{" "}
              {formatDate(company.next_event_date)}
            </span>
          )}
        </div>

        <div className="mt-4">
          <button
            onClick={() => setShowAddInterview(true)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            <Plus className="h-4 w-4" />
            添加面试
          </button>
        </div>
      </div>

      {chain && Object.keys(chain.weak_point_tracking).length > 0 && (
        <div className="mb-6 rounded-xl border border-red-200 bg-red-50/50 p-5">
          <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-red-800">
            <AlertTriangle className="h-4 w-4" />
            薄弱点追踪
          </h2>
          <div className="space-y-2">
            {Object.entries(chain.weak_point_tracking)
              .sort((a, b) => b[1].count - a[1].count)
              .map(([wp, data]) => (
                <div
                  key={wp}
                  className="flex items-center justify-between rounded-lg bg-white px-3 py-2"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-900">{wp}</span>
                    <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs text-red-700">
                      {data.count} 次
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-slate-500">
                    <span>
                      第 {data.first_round} → 第 {data.last_round} 轮
                    </span>
                    <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      <div className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold text-slate-900">面试链</h2>
        {!chain || chain.rounds.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-slate-400">
            <Calendar className="mb-3 h-10 w-10 text-slate-300" />
            <p className="text-sm">暂无面试记录</p>
            <p className="mt-1 text-xs">点击上方&quot;添加面试&quot;开始记录</p>
          </div>
        ) : (
          <div className="space-y-3">
            {chain.rounds.map((round) => {
              const FormatIcon = formatIcons[round.format || ""] || Calendar;
              const hasAnalysis = round.questions_count > 0;
              return (
                <div
                  key={round.id}
                  className="group relative rounded-lg border border-slate-100 bg-slate-50 p-4 transition-colors hover:border-slate-200 hover:bg-white"
                >
                  <div className="flex items-center gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 text-sm font-semibold text-blue-700">
                      {round.round}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-slate-900">
                          第 {round.round} 轮
                        </span>
                        <span className="inline-flex items-center gap-1 rounded bg-white px-2 py-0.5 text-xs text-slate-500">
                          <FormatIcon className="h-3 w-3" />
                          {round.format || "—"}
                        </span>
                        {hasAnalysis && (
                          <span className="rounded bg-green-100 px-1.5 py-0.5 text-[10px] font-medium text-green-700">
                            已复盘
                          </span>
                        )}
                      </div>
                      <div className="mt-1 text-xs text-slate-500">
                        {round.interview_date && (
                          <span>{formatDate(round.interview_date)}</span>
                        )}
                        {round.interviewer && (
                          <span className="ml-2">· {round.interviewer}</span>
                        )}
                      </div>
                      {round.weak_points.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {round.weak_points.map((wp) => (
                            <span
                              key={wp}
                              className="rounded bg-red-100 px-1.5 py-0.5 text-[10px] text-red-700"
                            >
                              {wp}
                            </span>
                          ))}
                        </div>
                      )}
                      {round.strong_points.length > 0 && (
                        <div className="mt-1 flex flex-wrap gap-1">
                          {round.strong_points.map((sp) => (
                            <span
                              key={sp}
                              className="rounded bg-green-100 px-1.5 py-0.5 text-[10px] text-green-700"
                            >
                              {sp}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="flex shrink-0 items-center gap-1.5 opacity-0 transition-opacity group-hover:opacity-100">
                      <Link
                        href={`/company/${id}/review?interview_id=${round.id}&round=${round.round}`}
                        className="inline-flex items-center gap-1 rounded-md bg-blue-50 px-2.5 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-100"
                      >
                        <FileText className="h-3.5 w-3.5" />
                        {hasAnalysis ? "查看复盘" : "写复盘"}
                      </Link>
                      <button
                        onClick={async () => {
                          try {
                            const res = await companiesApi.getBrief(
                              id,
                              round.round,
                            );
                            setBriefData(res.data);
                            setShowBrief(true);
                          } catch {
                            alert("加载失败");
                          }
                        }}
                        className="inline-flex items-center gap-1 rounded-md bg-green-50 px-2.5 py-1.5 text-xs font-medium text-green-700 hover:bg-green-100"
                      >
                        <BookOpen className="h-3.5 w-3.5" />
                        面试前速览
                      </button>
                      <Link
                        href={`/company/${id}/prep?round=${round.round + 1}`}
                        className="inline-flex items-center gap-1 rounded-md bg-amber-50 px-2.5 py-1.5 text-xs font-medium text-amber-700 hover:bg-amber-100"
                      >
                        <Lightbulb className="h-3.5 w-3.5" />
                        备战下一轮
                      </Link>
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
          onAdded={loadData}
        />
      )}

      {showBrief && briefData && (
        <BriefModal
          data={briefData}
          companyId={id}
          onClose={() => {
            setShowBrief(false);
            setBriefData(null);
          }}
        />
      )}

      {showRejection && rejectionData && (
        <RejectionModal
          data={rejectionData}
          onClose={() => {
            setShowRejection(false);
            setRejectionData(null);
          }}
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
  const [notes, setNotes] = useState("");
  const [expectedResultDate, setExpectedResultDate] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload: Record<string, unknown> = { round, format };
      if (interviewDate) payload.interview_date = interviewDate;
      if (interviewer.trim()) payload.interviewer = interviewer.trim();
      if (notes.trim()) payload.raw_notes = notes.trim();
      if (expectedResultDate)
        payload.expected_result_date = expectedResultDate;
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
          <button
            onClick={onClose}
            className="rounded-md p-1 text-slate-400 hover:bg-slate-100"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                轮次 <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                min={1}
                value={round}
                onChange={(e) => setRound(Number(e.target.value))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                形式
              </label>
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
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                日期
              </label>
              <input
                type="date"
                value={interviewDate}
                onChange={(e) => setInterviewDate(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                面试官
              </label>
              <input
                type="text"
                value={interviewer}
                onChange={(e) => setInterviewer(e.target.value)}
                placeholder="可选"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              面试笔记
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              placeholder="可选，也可以留到复盘时再填写..."
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              预计出结果日期
            </label>
            <input
              type="date"
              value={expectedResultDate}
              onChange={(e) => setExpectedResultDate(e.target.value)}
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

function BriefModal({
  data,
  companyId,
  onClose,
}: {
  data: any;
  companyId: string;
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg rounded-xl border border-slate-200 bg-white p-6 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">
            面试前速览 · 第 {data.next_round} 轮
          </h2>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-slate-400 hover:bg-slate-100"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-4">
          <div className="rounded-lg bg-blue-50 p-3 text-sm text-blue-800">
            <p className="font-semibold">{data.quick_review}</p>
          </div>

          {data.previous_weak_points.length > 0 && (
            <div>
              <h3 className="mb-2 text-sm font-semibold text-slate-700">
                薄弱点回顾
              </h3>
              <div className="space-y-1.5">
                {data.previous_weak_points.map(
                  (wp: { point: string; count: number; avg_score: number }, i: number) => (
                    <div
                      key={i}
                      className="flex items-center justify-between rounded-md bg-slate-50 px-3 py-2 text-sm"
                    >
                      <span className="text-slate-700">{wp.point}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-500">
                          出现 {wp.count} 次
                        </span>
                        <span
                          className={cn(
                            "rounded-full px-2 py-0.5 text-xs font-medium",
                            wp.avg_score >= 7
                              ? "bg-green-100 text-green-700"
                              : wp.avg_score >= 5
                                ? "bg-amber-100 text-amber-700"
                                : "bg-red-100 text-red-700",
                          )}
                        >
                          {wp.avg_score}/10
                        </span>
                      </div>
                    </div>
                  ),
                )}
              </div>
            </div>
          )}

          {data.next_round_prediction.length > 0 && (
            <div>
              <h3 className="mb-2 text-sm font-semibold text-slate-700">
                下一轮预测
              </h3>
              <div className="flex flex-wrap gap-1.5">
                {data.next_round_prediction.map((pred: string, i: number) => (
                  <span
                    key={i}
                    className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs text-blue-700"
                  >
                    {pred}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Link
              href={`/company/${companyId}/prep?round=${data.next_round}`}
              className="inline-flex items-center gap-1.5 rounded-lg bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600"
            >
              <Lightbulb className="h-4 w-4" />
              生成备战计划
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

function RejectionModal({
  data,
  onClose,
}: {
  data: any;
  onClose: () => void;
}) {
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
          <h2 className="text-lg font-semibold text-slate-900">拒绝分析</h2>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-slate-400 hover:bg-slate-100"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-4">
          {data.encouragement && (
            <p className="text-sm text-slate-600 italic">
              {data.encouragement}
            </p>
          )}

          {data.likely_reasons.length > 0 && (
            <div>
              <h3 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-red-700">
                <AlertTriangle className="h-4 w-4" />
                可能原因
              </h3>
              <div className="space-y-1.5">
                {data.likely_reasons.map((reason: string, i: number) => (
                  <div
                    key={i}
                    className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700"
                  >
                    {reason}
                  </div>
                ))}
              </div>
            </div>
          )}

          {data.next_focus.length > 0 && (
            <div>
              <h3 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-slate-700">
                <Target className="h-4 w-4" />
                下一步重点
              </h3>
              <div className="flex flex-wrap gap-1.5">
                {data.next_focus.map((wp: string, i: number) => (
                  <span
                    key={i}
                    className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs text-amber-700"
                  >
                    {wp}
                  </span>
                ))}
              </div>
            </div>
          )}

          {data.strengths_to_keep.length > 0 && (
            <div>
              <h3 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-green-700">
                <CheckCircle className="h-4 w-4" />
                保持优势
              </h3>
              <div className="flex flex-wrap gap-1.5">
                {data.strengths_to_keep.map((sp: string, i: number) => (
                  <span
                    key={i}
                    className="rounded-full bg-green-100 px-2.5 py-0.5 text-xs text-green-700"
                  >
                    {sp}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
