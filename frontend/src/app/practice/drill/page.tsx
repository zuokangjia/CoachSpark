"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { practiceApi } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import {
  ArrowLeft,
  Loader2,
  Sparkles,
  Zap,
  BookOpen,
  Play,
  ChevronRight,
} from "lucide-react";

type Category = {
  id: string;
  name: string;
  parent_id: string | null;
  description: string;
};

type GeneratedResult = {
  drill_id: string;
  drill_name: string;
  topic: string;
  user_level: number;
  generated_count: number;
  questions: {
    id: string;
    title: string;
    difficulty: number;
  }[];
};

const difficultyLabels = ["", "入门", "简单", "中等", "困难", "极难"];
const difficultyColors = ["", "text-green-500", "text-emerald-500", "text-yellow-500", "text-orange-500", "text-red-500"];

const levelHint: Record<number, string> = {
  1: "基础概念为主",
  2: "基础概念为主",
  3: "深度理解 + 简单应用",
  4: "场景分析 + 系统设计",
  5: "场景分析 + 系统设计",
};

export default function TopicDrillPage() {
  const router = useRouter();
  const [categories, setCategories] = useState<Category[]>([]);
  const [loadingCategories, setLoadingCategories] = useState(true);

  const [selectedTopic, setSelectedTopic] = useState("");
  const [customTopic, setCustomTopic] = useState("");
  const [numQuestions, setNumQuestions] = useState(3);
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<GeneratedResult | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadCategories = useCallback(async () => {
    setLoadingCategories(true);
    try {
      const res: any = await practiceApi.categories();
      setCategories(res.data?.items || []);
    } finally {
      setLoadingCategories(false);
    }
  }, []);

  useEffect(() => {
    loadCategories();
  }, [loadCategories]);

  async function handleGenerate() {
    const topic = selectedTopic === "custom" ? customTopic.trim() : selectedTopic;
    if (!topic) {
      setError("请选择或输入领域");
      return;
    }

    setGenerating(true);
    setError(null);
    setResult(null);

    try {
      const res: any = await practiceApi.generateDrill({
        topic,
        num_questions: numQuestions,
      });
      setResult(res.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "生成失败");
    } finally {
      setGenerating(false);
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

  const effectiveTopic = selectedTopic === "custom" ? customTopic.trim() : selectedTopic;
  const canGenerate = effectiveTopic && !generating;

  return (
    <div className="mx-auto max-w-3xl">
      <Link href="/practice" className="mb-4 inline-flex items-center gap-1 text-sm text-text-secondary hover:text-text-primary">
        <ArrowLeft className="h-4 w-4" />
        返回练习
      </Link>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
          <Zap className="h-6 w-6 text-brand" />
          AI 生成专项练习
        </h1>
        <p className="mt-1 text-sm text-text-secondary">
          基于选定领域，AI 自动生成针对性练习题
        </p>
      </div>

      <div className="rounded-xl border border-border bg-surface p-6 mb-6">
        <div className="mb-4">
          <label className="mb-2 block text-sm font-medium text-text-primary">
            选择知识领域
          </label>
          {loadingCategories ? (
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <Loader2 className="h-4 w-4 animate-spin" />
              加载中...
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  type="button"
                  onClick={() => {
                    setSelectedTopic(cat.name);
                    setCustomTopic("");
                  }}
                  className={cn(
                    "rounded-lg border px-3 py-1.5 text-sm transition-colors",
                    selectedTopic === cat.name && !customTopic
                      ? "border-brand bg-brand-subtle text-brand-text"
                      : "border-border bg-surface text-text-secondary hover:border-brand/60"
                  )}
                >
                  {cat.name}
                </button>
              ))}
              <button
                type="button"
                onClick={() => setSelectedTopic("custom")}
                className={cn(
                  "rounded-lg border px-3 py-1.5 text-sm transition-colors",
                  selectedTopic === "custom"
                    ? "border-brand bg-brand-subtle text-brand-text"
                    : "border-border bg-surface text-text-secondary hover:border-brand/60"
                )}
              >
                自定义
              </button>
            </div>
          )}

          {selectedTopic === "custom" && (
            <input
              value={customTopic}
              onChange={(e) => setCustomTopic(e.target.value)}
              placeholder="输入领域名称，如：React Hooks、Event Loop、系统设计..."
              className="mt-3 w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus placeholder:text-text-muted"
            />
          )}
        </div>

        <div className="mb-4">
          <label className="mb-2 block text-sm font-medium text-text-primary">
            题目数量
          </label>
          <div className="flex items-center gap-3">
            {[1, 2, 3, 5].map((n) => (
              <button
                key={n}
                type="button"
                onClick={() => setNumQuestions(n)}
                className={cn(
                  "rounded-lg border px-4 py-1.5 text-sm transition-colors",
                  numQuestions === n
                    ? "border-brand bg-brand-subtle text-brand-text"
                    : "border-border bg-surface text-text-secondary hover:border-brand/60"
                )}
              >
                {n} 道
              </button>
            ))}
          </div>
        </div>

        {effectiveTopic && (
          <div className="rounded-lg bg-surface-muted px-4 py-3 mb-4">
            <div className="text-xs text-text-muted mb-1">生成策略</div>
            <div className="text-sm text-text-secondary">
              领域：<span className="font-medium text-text-primary">{effectiveTopic}</span>
              {result && (
                <span className="ml-2">
                  · 预估水平：<span className="font-medium text-text-primary">Level {result.user_level}</span>
                  <span className="ml-1 text-text-muted">（{levelHint[result.user_level] || "中等难度"}）</span>
                </span>
              )}
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-lg bg-error-bg px-4 py-3 text-sm text-error-text mb-4">
            {error}
          </div>
        )}

        <button
          type="button"
          onClick={handleGenerate}
          disabled={!canGenerate}
          className="w-full rounded-lg bg-brand py-3 text-sm font-medium text-text-inverse hover:bg-brand-hover disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {generating ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              AI 生成中...
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              生成 {numQuestions} 道专项练习题
            </>
          )}
        </button>
      </div>

      {result && (
        <div className="space-y-4">
          <div className="rounded-xl border border-brand/30 bg-brand/5 p-6">
            <div className="text-center mb-4">
              <h2 className="text-lg font-semibold text-text-primary">
                {result.drill_name}
              </h2>
              <p className="mt-1 text-sm text-text-secondary">
                {result.generated_count} 道题目 · {effectiveTopic}
              </p>
            </div>
            <button
              type="button"
              onClick={startDrill}
              disabled={starting}
              className="w-full rounded-lg bg-brand py-3 text-sm font-medium text-text-inverse hover:bg-brand-hover disabled:opacity-50 flex items-center justify-center gap-2"
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

          <div className="space-y-3">
            {result.questions.map((q, idx) => (
              <div
                key={q.id}
                className="rounded-xl border border-border bg-surface p-4"
              >
                <div className="flex items-start gap-4">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-surface-muted text-sm font-medium text-text-muted">
                    {idx + 1}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={cn("text-sm font-medium", difficultyColors[q.difficulty])}>
                        {difficultyLabels[q.difficulty]}
                      </span>
                    </div>
                    <h3 className="text-base font-medium text-text-primary line-clamp-2">
                      {q.title}
                    </h3>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <button
            type="button"
            onClick={handleGenerate}
            disabled={generating}
            className="w-full rounded-lg border border-border py-3 text-sm font-medium text-text-secondary hover:bg-surface-muted disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <Sparkles className="h-4 w-4" />
            重新生成
          </button>
        </div>
      )}

      {!result && !generating && (
        <div className="rounded-xl border border-dashed border-border bg-surface/50 p-8 text-center">
          <BookOpen className="h-12 w-12 mx-auto text-text-muted mb-3" />
          <p className="text-sm text-text-muted">
            选择领域后点击生成，AI 将根据知识库创建练习题
          </p>
        </div>
      )}
    </div>
  );
}