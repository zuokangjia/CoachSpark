"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { X, Loader2, Target } from "lucide-react";
import { companiesApi } from "@/lib/api-client";
import { useCompanyStore } from "@/lib/store/company-store";

interface AddCompanyModalProps {
  onClose: () => void;
  onAdded?: () => void;
}

export function AddCompanyModal({ onClose, onAdded }: AddCompanyModalProps) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [position, setPosition] = useState("");
  const [jdText, setJdText] = useState("");
  const [appliedDate, setAppliedDate] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const { addCompany, fetchCompanies } = useCompanyStore();

  function handleAnalyzeFirst() {
    sessionStorage.setItem("pending_company", JSON.stringify({
      name: name.trim(),
      position: position.trim(),
      jd_text: jdText.trim(),
      applied_date: appliedDate,
    }));
    router.push("/match");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() || !position.trim()) {
      alert("请填写公司名和岗位名");
      return;
    }

    setSubmitting(true);
    try {
      const payload: Record<string, unknown> = {
        name: name.trim(),
        position: position.trim(),
        status: "applied",
      };
      if (jdText.trim()) payload.jd_text = jdText.trim();
      if (appliedDate) payload.applied_date = appliedDate;

      const res = await companiesApi.create(payload);
      addCompany(res.data);
      onAdded?.();
      onClose();
    } catch (err) {
      alert("创建失败，请重试");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-overlay backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-xl border border-border bg-surface p-6 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-text-primary">添加公司</h2>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-text-muted hover:bg-surface-secondary hover:text-text-secondary"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-text-secondary">
              公司名
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="例如：Google"
              className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted"
              autoFocus
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-text-secondary">
              岗位名
            </label>
            <input
              type="text"
              value={position}
              onChange={(e) => setPosition(e.target.value)}
              placeholder="例如：Software Engineer"
              className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-text-secondary">
              岗位描述 (JD)
            </label>
            <textarea
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              rows={4}
              placeholder="粘贴岗位描述..."
              className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-text-secondary">
              投递日期
            </label>
            <input
              type="date"
              value={appliedDate}
              onChange={(e) => setAppliedDate(e.target.value)}
              className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus"
            />
          </div>

          <div className="flex justify-between gap-2 pt-2">
            <button
              type="button"
              onClick={handleAnalyzeFirst}
              disabled={!jdText.trim()}
              className="inline-flex items-center gap-1.5 rounded-lg border border-brand/30 bg-brand-subtle px-4 py-2 text-sm font-medium text-brand-text hover:bg-brand-subtle/80 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <Target className="h-4 w-4" />
              先分析匹配度
            </button>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={onClose}
                className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text-secondary hover:bg-surface-secondary"
              >
                取消
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="inline-flex items-center gap-1.5 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-text-inverse hover:bg-brand-hover disabled:opacity-50"
              >
                {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
                添加
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
