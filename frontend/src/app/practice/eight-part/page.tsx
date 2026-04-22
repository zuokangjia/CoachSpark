"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { practiceApi } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import {
  ArrowLeft,
  Loader2,
  MessageSquare,
  ChevronRight,
  BookOpen,
  Star,
} from "lucide-react";

type TemplateCategory = {
  name: string;
  count: number;
};

type Template = {
  id: string;
  category: string;
  title: string;
  content: string;
  answer_template: string;
  difficulty: number;
  tips: string[];
};

const difficultyLabels = ["", "入门", "简单", "中等", "困难", "极难"];
const difficultyColors = ["", "text-green-500", "text-emerald-500", "text-yellow-500", "text-orange-500", "text-red-500"];

const categoryIcons: Record<string, string> = {
  "自我介绍": "👋",
  "项目经历": "💼",
  "技术深度": "⚡",
  "系统设计": "🏗️",
  "算法": "🧩",
  "HR问题": "💬",
  "反问": "❓",
};

export default function EightPartPracticePage() {
  const router = useRouter();
  const [categories, setCategories] = useState<TemplateCategory[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loadingCategories, setLoadingCategories] = useState(true);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [showAnswer, setShowAnswer] = useState(false);
  const [userAnswer, setUserAnswer] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const loadCategories = useCallback(async () => {
    setLoadingCategories(true);
    try {
      const res: any = await practiceApi.getEightPartCategories();
      setCategories(res.data?.items || []);
    } finally {
      setLoadingCategories(false);
    }
  }, []);

  const loadTemplates = useCallback(async (category: string) => {
    setLoadingTemplates(true);
    try {
      const res: any = await practiceApi.listEightPartTemplates({ category });
      setTemplates(res.data?.items || []);
    } finally {
      setLoadingTemplates(false);
    }
  }, []);

  useEffect(() => {
    loadCategories();
  }, [loadCategories]);

  useEffect(() => {
    if (selectedCategory) {
      loadTemplates(selectedCategory);
    }
  }, [selectedCategory, loadTemplates]);

  function selectCategory(cat: string) {
    setSelectedCategory(cat);
    setSelectedTemplate(null);
    setShowAnswer(false);
    setUserAnswer("");
  }

  function selectTemplate(tpl: Template) {
    setSelectedTemplate(tpl);
    setShowAnswer(false);
    setUserAnswer("");
  }

  function toggleAnswer() {
    setShowAnswer(!showAnswer);
  }

  async function submitPractice() {
    if (!userAnswer.trim()) return;
    setSubmitting(true);
    await new Promise((r) => setTimeout(r, 500));
    setSubmitting(false);
    setUserAnswer("");
    alert("答案已提交！评估功能开发中...");
  }

  return (
    <div className="mx-auto max-w-4xl">
      <Link href="/practice" className="mb-4 inline-flex items-center gap-1 text-sm text-text-secondary hover:text-text-primary">
        <ArrowLeft className="h-4 w-4" />
        返回练习
      </Link>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
          <MessageSquare className="h-6 w-6 text-brand" />
          八股专项练习
        </h1>
        <p className="mt-1 text-sm text-text-secondary">
          固定面试题型的标准答案框架
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <div className="space-y-4">
          <div className="rounded-xl border border-border bg-surface p-4">
            <h2 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2">
              <Star className="h-4 w-4 text-brand" />
              选择分类
            </h2>
            {loadingCategories ? (
              <div className="flex items-center gap-2 text-sm text-text-muted py-4">
                <Loader2 className="h-4 w-4 animate-spin" />
                加载中...
              </div>
            ) : (
              <div className="space-y-1">
                {categories.map((cat) => (
                  <button
                    key={cat.name}
                    type="button"
                    onClick={() => selectCategory(cat.name)}
                    className={cn(
                      "w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors",
                      selectedCategory === cat.name
                        ? "bg-brand-subtle text-brand-text"
                        : "text-text-secondary hover:bg-surface-muted"
                    )}
                  >
                    <span className="flex items-center gap-2">
                      <span>{categoryIcons[cat.name] || "📁"}</span>
                      {cat.name}
                    </span>
                    <span className="text-xs text-text-muted">{cat.count}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {selectedCategory && (
            <div className="rounded-xl border border-border bg-surface p-4">
              <h2 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2">
                <BookOpen className="h-4 w-4 text-brand" />
                {selectedCategory} 题目
              </h2>
              {loadingTemplates ? (
                <div className="flex items-center gap-2 text-sm text-text-muted py-4">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  加载中...
                </div>
              ) : (
                <div className="space-y-2">
                  {templates.map((tpl) => (
                    <button
                      key={tpl.id}
                      type="button"
                      onClick={() => selectTemplate(tpl)}
                      className={cn(
                        "w-full text-left px-3 py-2 rounded-lg text-sm transition-colors",
                        selectedTemplate?.id === tpl.id
                          ? "bg-brand-subtle text-brand-text"
                          : "text-text-secondary hover:bg-surface-muted"
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <span className="truncate">{tpl.title}</span>
                        <span className={cn("text-xs", difficultyColors[tpl.difficulty])}>
                          {difficultyLabels[tpl.difficulty]}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="md:col-span-2">
          {selectedTemplate ? (
            <div className="rounded-xl border border-border bg-surface p-6">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-2xl">{categoryIcons[selectedTemplate.category] || "📁"}</span>
                <div>
                  <h2 className="text-lg font-semibold text-text-primary">
                    {selectedTemplate.title}
                  </h2>
                  <span className={cn("text-xs", difficultyColors[selectedTemplate.difficulty])}>
                    {difficultyLabels[selectedTemplate.difficulty]}
                  </span>
                </div>
              </div>

              <div className="rounded-lg bg-surface-muted p-4 mb-4">
                <h3 className="text-sm font-medium text-text-primary mb-2">题目</h3>
                <p className="text-sm text-text-secondary leading-relaxed">
                  {selectedTemplate.content}
                </p>
              </div>

              {selectedTemplate.tips && selectedTemplate.tips.length > 0 && (
                <div className="rounded-lg border border-brand/20 bg-brand/5 p-4 mb-4">
                  <h3 className="text-sm font-medium text-brand-text mb-2">提示</h3>
                  <ul className="space-y-1">
                    {selectedTemplate.tips.map((tip, i) => (
                      <li key={i} className="text-sm text-text-secondary flex items-start gap-2">
                        <span className="text-brand mt-0.5">•</span>
                        {tip}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-text-primary">你的回答</h3>
                  <button
                    type="button"
                    onClick={toggleAnswer}
                    className="text-xs text-brand hover:text-brand-hover"
                  >
                    {showAnswer ? "隐藏答案" : "查看答案"}
                  </button>
                </div>
                <textarea
                  value={userAnswer}
                  onChange={(e) => setUserAnswer(e.target.value)}
                  placeholder="在这里输入你的回答..."
                  rows={6}
                  className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus placeholder:text-text-muted resize-none"
                />
              </div>

              <button
                type="button"
                onClick={submitPractice}
                disabled={!userAnswer.trim() || submitting}
                className="w-full rounded-lg bg-brand py-3 text-sm font-medium text-text-inverse hover:bg-brand-hover disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    提交中...
                  </>
                ) : (
                  "提交回答"
                )}
              </button>

              {showAnswer && (
                <div className="mt-4 rounded-lg border border-green-200 bg-green-50 p-4">
                  <h3 className="text-sm font-medium text-green-700 mb-2">参考答案框架</h3>
                  <pre className="text-sm text-green-800 whitespace-pre-wrap font-sans leading-relaxed">
                    {selectedTemplate.answer_template}
                  </pre>
                </div>
              )}
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-border bg-surface/50 p-8 text-center">
              <MessageSquare className="h-12 w-12 mx-auto text-text-muted mb-3" />
              <p className="text-sm text-text-muted">
                左侧选择分类和题目，开始练习
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
