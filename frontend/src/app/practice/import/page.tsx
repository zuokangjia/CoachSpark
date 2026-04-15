"use client";

import React, { useState } from "react";
import Link from "next/link";
import { practiceApi } from "@/lib/api-client";
import {
  ArrowLeft,
  Loader2,
  Upload,
  Plus,
} from "lucide-react";

export default function ImportQuestionsPage() {
  const [text, setText] = useState("");
  const [categoryName, setCategoryName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ imported_count: number; questions: any[] } | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <div className="mx-auto max-w-3xl">
      <Link href="/practice" className="mb-4 inline-flex items-center gap-1 text-sm text-text-secondary hover:text-text-primary">
        <ArrowLeft className="h-4 w-4" />
        返回题库
      </Link>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-text-primary">导入题目</h1>
        <p className="mt-1 text-sm text-text-secondary">
          粘贴大段文本，AI 自动解析并导入结构化题目
        </p>
      </div>

      <div className="space-y-4">
        <div className="rounded-xl border border-border bg-surface p-6">
          <div className="mb-4">
            <label className="mb-2 block text-sm font-medium text-text-primary">
              分类名称（可选）
            </label>
            <input
              value={categoryName}
              onChange={(e) => setCategoryName(e.target.value)}
              placeholder="例如：算法、React、手写代码..."
              className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus placeholder:text-text-muted"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-text-primary">
              题目文本
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={12}
              placeholder={`粘贴面试题目文本，例如：

React Fiber 架构解决了什么问题？
详细解释 React Fiber 架构的背景、解决的问题以及核心设计思想。

参考答案：
1. 解决的问题：同步渲染长时间阻塞主线程，无法中断和恢复
2. 核心设计：链表结构替代递归树、时间切片、优先级调度
...

手写防抖函数
实现一个防抖函数，支持 immediate 参数。

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
                  导入题目
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
                成功导入 {result.imported_count} 道题目
              </span>
            </div>
            <div className="space-y-2">
              {result.questions.map((q, idx) => (
                <div key={idx} className="rounded-lg border border-border bg-surface p-3">
                  <div className="text-sm font-medium text-text-primary line-clamp-1">
                    {q.title}
                  </div>
                  <div className="mt-1 flex items-center gap-2 text-xs text-text-muted">
                    <span>难度 {q.difficulty}</span>
                    <span>·</span>
                    <span>{q.knowledge_points?.length || 0} 个知识点</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="rounded-xl border border-border bg-surface p-6">
          <h3 className="text-sm font-medium text-text-primary mb-2">导入说明</h3>
          <ul className="space-y-1 text-sm text-text-secondary">
            <li>• 粘贴包含面试问题和答案的文本，AI 会自动解析</li>
            <li>• 支持识别：题目标题、题目描述、参考答案、知识点、公司标签</li>
            <li>• 题目难度会根据内容复杂度自动推断（1-5级）</li>
            <li>• 可以指定分类名称，也可以留空使用"未分类"</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
