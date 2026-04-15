"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { practiceApi } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import {
  ArrowLeft,
  Loader2,
  Search,
  Target,
  Lightbulb,
  Building2,
} from "lucide-react";

type Question = {
  id: string;
  category_id: string;
  category_name: string;
  title: string;
  content: string;
  difficulty: number;
  knowledge_points: string[];
  company_tags: string[];
  question_type: string;
  options: string[] | null;
  hints: string[];
};

type Category = {
  id: string;
  name: string;
  parent_id: string | null;
  description: string;
};

const difficultyLabels = ["", "入门", "简单", "中等", "困难", "极难"];
const difficultyColors = ["", "text-green-500", "text-emerald-500", "text-yellow-500", "text-orange-500", "text-red-500"];

export default function PracticePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [total, setTotal] = useState(0);

  const [category, setCategory] = useState("");
  const [difficulty, setDifficulty] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [recommendLoading, setRecommendLoading] = useState(false);
  const [recommended, setRecommended] = useState<Question[]>([]);

  const loadQuestions = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (category) params.set("category", category);
      if (difficulty) params.set("difficulty", String(difficulty));
      if (search) params.set("search", search);

      const res: any = await practiceApi.list(params.toString());
      setQuestions(res.data?.items || []);
      setTotal(res.data?.total || 0);
    } finally {
      setLoading(false);
    }
  }, [category, difficulty, search]);

  const loadCategories = useCallback(async () => {
    try {
      const res: any = await practiceApi.categories();
      setCategories(res.data?.items || []);
    } catch {
      // silent
    }
  }, []);

  const loadRecommend = useCallback(async () => {
    setRecommendLoading(true);
    try {
      const res: any = await practiceApi.recommend(3);
      setRecommended(res.data?.recommended_questions || []);
    } catch {
      // silent
    } finally {
      setRecommendLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCategories();
    loadRecommend();
  }, [loadCategories, loadRecommend]);

  useEffect(() => {
    loadQuestions();
  }, [loadQuestions]);

  function handleSearchKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      loadQuestions();
    }
  }

  return (
    <div className="mx-auto max-w-4xl">
      <Link href="/" className="mb-4 inline-flex items-center gap-1 text-sm text-text-secondary hover:text-text-primary">
        <ArrowLeft className="h-4 w-4" />
        返回看板
      </Link>

      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">题目训练</h1>
          <p className="mt-1 text-sm text-text-secondary">选择题目进行练习，提升面试技能</p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/practice/drill"
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-text-inverse hover:bg-brand-hover"
          >
            专项强化
          </Link>
          <Link
            href="/practice/import"
            className="inline-flex items-center gap-1.5 rounded-lg border border-brand/30 bg-brand-subtle px-4 py-2 text-sm font-medium text-brand-text hover:bg-brand-subtle/80"
          >
            导入题目
          </Link>
        </div>
      </div>

      {/* 推荐区域 */}
      {(recommended.length > 0 || recommendLoading) && (
        <div className="mb-6 rounded-xl border border-brand/30 bg-brand/5 p-4">
          <div className="mb-3 flex items-center gap-2 text-text-primary">
            <Target className="h-4 w-4 text-brand" />
            <span className="text-sm font-medium">基于薄弱点推荐</span>
          </div>
          {recommendLoading ? (
            <div className="flex items-center gap-2 text-sm text-text-secondary">
              <Loader2 className="h-4 w-4 animate-spin" />
              正在加载推荐...
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
              {recommended.map((q) => (
                <button
                  key={q.id}
                  type="button"
                  onClick={() => router.push(`/practice/${q.id}`)}
                  className="rounded-lg border border-border bg-surface p-3 text-left hover:border-brand/60"
                >
                  <div className="text-sm font-medium text-text-primary line-clamp-2">{q.title}</div>
                  <div className="mt-1 flex items-center gap-2 text-xs text-text-muted">
                    <span className={difficultyColors[q.difficulty]}>{difficultyLabels[q.difficulty]}</span>
                    <span>·</span>
                    <span>{q.category_name}</span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 筛选栏 */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <Search className="h-4 w-4 text-text-muted" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={handleSearchKeyDown}
            placeholder="搜索题目..."
            className="w-48 rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus placeholder:text-text-muted"
          />
        </div>

        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus"
        >
          <option value="">全部分类</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>

        <select
          value={difficulty ?? ""}
          onChange={(e) => setDifficulty(e.target.value ? Number(e.target.value) : null)}
          className="rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus"
        >
          <option value="">全部难度</option>
          {[1, 2, 3, 4, 5].map((d) => (
            <option key={d} value={d}>{difficultyLabels[d]} ({d})</option>
          ))}
        </select>
      </div>

      {/* 结果统计 */}
      <div className="mb-3 text-sm text-text-secondary">
        共 {total} 道题目
      </div>

      {/* 题目列表 */}
      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-text-muted" />
        </div>
      ) : questions.length === 0 ? (
        <div className="flex h-32 items-center justify-center text-sm text-text-muted">
          暂无题目，请先添加题库数据
        </div>
      ) : (
        <div className="space-y-3">
          {questions.map((q) => (
            <div
              key={q.id}
              className="rounded-xl border border-border bg-surface p-4 hover:border-brand/60"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className={cn("text-sm font-medium", difficultyColors[q.difficulty])}>
                      {difficultyLabels[q.difficulty]}
                    </span>
                    <span className="text-xs text-text-muted">·</span>
                    <span className="text-sm text-text-secondary">{q.category_name}</span>
                  </div>
                  <h3 className="mt-1 text-base font-medium text-text-primary line-clamp-2">
                    {q.title}
                  </h3>
                  <p className="mt-1 text-sm text-text-secondary line-clamp-2">{q.content}</p>

                  {/* 知识点标签 */}
                  {q.knowledge_points.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {q.knowledge_points.slice(0, 4).map((kp, idx) => (
                        <span key={`${kp}-${idx}`} className="inline-flex items-center gap-1 rounded-full bg-surface-muted px-2 py-0.5 text-xs text-text-secondary">
                          <Lightbulb className="h-3 w-3" />
                          {kp}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* 公司标签 */}
                  {q.company_tags.length > 0 && (
                    <div className="mt-1 flex flex-wrap gap-1">
                      {q.company_tags.slice(0, 3).map((tag, idx) => (
                        <span key={`${tag}-${idx}`} className="inline-flex items-center gap-1 rounded-full bg-surface-muted px-2 py-0.5 text-xs text-text-muted">
                          <Building2 className="h-3 w-3" />
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <button
                  type="button"
                  onClick={() => router.push(`/practice/${q.id}`)}
                  className="shrink-0 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-text-inverse hover:bg-brand-hover"
                >
                  练习
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
