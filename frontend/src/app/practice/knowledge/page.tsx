"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { practiceApi } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import {
  ArrowLeft,
  Loader2,
  Plus,
  Search,
  Trash2,
  Edit2,
  BookOpen,
  X,
} from "lucide-react";

type KnowledgeItem = {
  id: string;
  category: string;
  title: string;
  content: string;
  concepts: string[];
  examples: string[];
  tags: string[];
  difficulty_min: number;
  difficulty_max: number;
  created_at: string;
};

type Category = {
  id: string;
  name: string;
};

export default function KnowledgeBasePage() {
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [total, setTotal] = useState(0);

  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState<KnowledgeItem | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    category: "",
    title: "",
    content: "",
    concepts: "",
    examples: "",
    tags: "",
  });

  const loadItems = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (selectedCategory) params.category = selectedCategory;
      if (search) params.search = search;
      const res: any = await practiceApi.listKnowledge(params);
      setItems(res.data?.items || []);
      setTotal(res.data?.total || 0);
    } finally {
      setLoading(false);
    }
  }, [selectedCategory, search]);

  const loadCategories = useCallback(async () => {
    try {
      const res: any = await practiceApi.categories();
      setCategories(res.data?.items || []);
    } catch {}
  }, []);

  useEffect(() => {
    loadCategories();
  }, [loadCategories]);

  useEffect(() => {
    loadItems();
  }, [loadItems]);

  function openAddModal() {
    setEditingItem(null);
    setFormData({ category: selectedCategory || "", title: "", content: "", concepts: "", examples: "", tags: "" });
    setShowModal(true);
  }

  function openEditModal(item: KnowledgeItem) {
    setEditingItem(item);
    setFormData({
      category: item.category,
      title: item.title,
      content: item.content,
      concepts: item.concepts.join(", "),
      examples: item.examples.join(", "),
      tags: item.tags.join(", "),
    });
    setShowModal(true);
  }

  async function handleSubmit() {
    if (!formData.title.trim()) return;
    setSubmitting(true);
    try {
      const data = {
        category: formData.category || "未分类",
        title: formData.title,
        content: formData.content,
        concepts: formData.concepts.split(",").map(s => s.trim()).filter(Boolean),
        examples: formData.examples.split(",").map(s => s.trim()).filter(Boolean),
        tags: formData.tags.split(",").map(s => s.trim()).filter(Boolean),
      };
      if (editingItem) {
        await practiceApi.updateKnowledge(editingItem.id, data);
      } else {
        await practiceApi.createKnowledge(data);
      }
      setShowModal(false);
      loadItems();
      loadCategories();
    } catch (err) {
      console.error("Failed to save:", err);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("确定删除这条知识？")) return;
    try {
      await practiceApi.deleteKnowledge(id);
      loadItems();
    } catch (err) {
      console.error("Failed to delete:", err);
    }
  }

  return (
    <div className="mx-auto max-w-5xl">
      <Link href="/practice" className="mb-4 inline-flex items-center gap-1 text-sm text-text-secondary hover:text-text-primary">
        <ArrowLeft className="h-4 w-4" />
        返回练习
      </Link>

      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
            <BookOpen className="h-6 w-6 text-brand" />
            知识库
          </h1>
          <p className="mt-1 text-sm text-text-secondary">管理知识条目，用于生成练习题</p>
        </div>
        <button
          onClick={openAddModal}
          className="inline-flex items-center gap-2 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-text-inverse hover:bg-brand-hover"
        >
          <Plus className="h-4 w-4" />
          添加知识
        </button>
      </div>

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <Search className="h-4 w-4 text-text-muted" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索知识..."
            className="w-48 rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus placeholder:text-text-muted"
          />
        </div>
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus"
        >
          <option value="">全部分类</option>
          {categories.map((c) => (
            <option key={c.id} value={c.name}>{c.name}</option>
          ))}
        </select>
      </div>

      <div className="mb-3 text-sm text-text-secondary">
        共 {total} 条知识
      </div>

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-text-muted" />
        </div>
      ) : items.length === 0 ? (
        <div className="flex h-32 items-center justify-center text-sm text-text-muted">
          暂无知识条目，添加一些知识开始吧
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <div key={item.id} className="rounded-xl border border-border bg-surface p-4 hover:border-brand/60">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs px-2 py-0.5 rounded-full bg-brand-subtle text-brand-text">
                      {item.category}
                    </span>
                  </div>
                  <h3 className="text-base font-medium text-text-primary">{item.title}</h3>
                  {item.content && (
                    <p className="mt-1 text-sm text-text-secondary line-clamp-2">{item.content}</p>
                  )}
                  {item.concepts.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {item.concepts.slice(0, 5).map((c, i) => (
                        <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-surface-muted text-text-secondary">
                          {c}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => openEditModal(item)}
                    className="p-2 rounded-lg hover:bg-surface-muted text-text-muted hover:text-text-primary"
                  >
                    <Edit2 className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(item.id)}
                    className="p-2 rounded-lg hover:bg-surface-muted text-text-muted hover:text-error"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-surface rounded-xl border border-border w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b border-border">
              <h2 className="text-lg font-semibold text-text-primary">
                {editingItem ? "编辑知识" : "添加知识"}
              </h2>
              <button onClick={() => setShowModal(false)} className="p-1 hover:bg-surface-muted rounded">
                <X className="h-5 w-5 text-text-muted" />
              </button>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1">分类</label>
                <input
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  placeholder="例如：React、算法..."
                  className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1">标题 *</label>
                <input
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="知识点标题"
                  className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1">内容</label>
                <textarea
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  rows={4}
                  placeholder="详细知识点内容..."
                  className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus resize-y"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1">核心概念（逗号分隔）</label>
                <input
                  value={formData.concepts}
                  onChange={(e) => setFormData({ ...formData, concepts: e.target.value })}
                  placeholder="useState, useEffect, Hooks"
                  className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1">示例（逗号分隔）</label>
                <input
                  value={formData.examples}
                  onChange={(e) => setFormData({ ...formData, examples: e.target.value })}
                  placeholder="示例1, 示例2"
                  className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1">标签（逗号分隔）</label>
                <input
                  value={formData.tags}
                  onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                  placeholder="面试, 前端, JavaScript"
                  className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus"
                />
              </div>
            </div>
            <div className="flex justify-end gap-3 p-4 border-t border-border">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 rounded-lg border border-border text-sm font-medium text-text-primary hover:bg-surface-muted"
              >
                取消
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting || !formData.title.trim()}
                className="px-4 py-2 rounded-lg bg-brand text-sm font-medium text-text-inverse hover:bg-brand-hover disabled:opacity-50 flex items-center gap-2"
              >
                {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
                保存
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}