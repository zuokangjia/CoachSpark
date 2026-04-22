"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { practiceApi } from "@/lib/api-client";
import {
  ArrowLeft,
  Loader2,
  Upload,
  Plus,
  BookOpen,
  Play,
} from "lucide-react";

type ImportResult = {
  imported_count: number;
  drill_id: string;
  drill_name: string;
  questions: {
    title: string;
    difficulty: number;
  }[];
};

export default function ImportKnowledgePage() {
  const router = useRouter();
  const [text, setText] = useState("");
  const [categoryName, setCategoryName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  async function handleImport() {
    if (!text.trim()) return;
    setSubmitting(true);
    setError(null);
    setResult(null);
    try {
      const res: any = await practiceApi.importText({
        text: text,
        category_name: categoryName || "未分类",
      });
      setResult(res.data);
      setText("");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "导入失败");
    } finally {
      setSubmitting(false);
    }
  }

  async function startDrill() {
    if (!result?.drill_id || starting) return;
    setStarting(true);
    try {
      const res: any = await practiceApi.startDrillSession(result.drill_id);
      router.push(`/practice/drills/session/${res.data.session_id}`);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "启动练习失败");
      setStarting(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <Link href="/practice" className="mb-4 inline-flex items-center gap-1 text-sm text-text-secondary hover:text-text-primary">
        <ArrowLeft className="h-4 w-4" />
        返回练习
      </Link>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-text-primary">导入知识内容</h1>
        <p className="mt-1 text-sm text-text-secondary">
          粘贴知识内容，AI 解析后存入知识库并生成练习题
        </p>
      </div>

      <div className="space-y-4">
        <div className="rounded-xl border border-border bg-surface p-6">
          <div className="mb-4">
            <label className="mb-2 block text-sm font-medium text-text-primary">
              知识领域（可选）
            </label>
            <input
              value={categoryName}
              onChange={(e) => setCategoryName(e.target.value)}
              placeholder="例如：React、算法、系统设计..."
              className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus placeholder:text-text-muted"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-text-primary">
              知识内容
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={10}
              placeholder={`粘贴面试相关知识内容，例如：

React Hooks 核心概念：
- useState：状态管理，返回 [state, setState]
- useEffect：副作用处理，默认在 mount 后执行
- useCallback：缓存回调函数，避免每次渲染重新创建
- useMemo：缓存计算结果

手写防抖函数：
function debounce(fn, delay) {
  let timer = null;
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => {
      fn.apply(this, args);
    }, delay);
  };
}

...`}
              className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus placeholder:text-text-muted font-mono"
            />
          </div>

          {error && (
            <div className="mt-3 rounded-lg bg-error-bg px-4 py-3 text-sm text-error-text">
              {error}
            </div>
          )}

          <div className="mt-4 flex justify-end">
            <button
              type="button"
              onClick={handleImport}
              disabled={submitting || !text.trim()}
              className="inline-flex items-center gap-2 rounded-lg bg-brand px-6 py-2.5 text-sm font-medium text-text-inverse hover:bg-brand-hover disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  解析中...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4" />
                  导入并生成练习
                </>
              )}
            </button>
          </div>
        </div>

        {result && (
          <div className="rounded-xl border border-success/30 bg-success/5 p-6">
            <div className="flex items-center gap-2 mb-4">
              <Plus className="h-5 w-5 text-success" />
              <span className="text-sm font-medium text-success">
                已导入 {result.imported_count} 道题目到知识库
              </span>
            </div>

            {result.drill_id && (
              <div className="mb-4 rounded-lg border border-brand/30 bg-brand/5 p-4">
                <div className="text-center mb-3">
                  <div className="text-sm text-text-secondary">{result.drill_name}</div>
                </div>
                <button
                  type="button"
                  onClick={startDrill}
                  disabled={starting}
                  className="w-full rounded-lg bg-brand py-2.5 text-sm font-medium text-text-inverse hover:bg-brand-hover disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {starting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      启动中...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      开始练习
                    </>
                  )}
                </button>
              </div>
            )}

            <div className="space-y-2">
              {result.questions.map((q, idx) => (
                <div key={idx} className="rounded-lg border border-border bg-surface p-3">
                  <div className="text-sm font-medium text-text-primary line-clamp-1">
                    {q.title}
                  </div>
                  <div className="mt-1 flex items-center gap-2 text-xs text-text-muted">
                    <span>难度 {q.difficulty}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="rounded-xl border border-border bg-surface p-6">
          <h3 className="text-sm font-medium text-text-primary mb-2">导入说明</h3>
          <ul className="space-y-1 text-sm text-text-secondary">
            <li>• 粘贴知识内容（概念、知识点、面试题等）</li>
            <li>• AI 自动解析并存储到知识库</li>
            <li>• 同时生成配套练习题</li>
            <li>• 可直接开始练习或稍后练习</li>
          </ul>
        </div>
      </div>
    </div>
  );
}