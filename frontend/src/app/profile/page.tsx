"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { personaV2Api, profileApi, resumeApi } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import {
  User,
  GraduationCap,
  Briefcase,
  FolderKanban,
  Award,
  Plus,
  Trash2,
  Loader2,
  CheckCircle,
  ArrowLeft,
  Save,
  X,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react";

type PersonaReference = {
  snapshot_id?: string;
  version?: string;
  generated_at?: string;
  headline: string;
  dimensions?: {
    dimension: string;
    level: number;
    trend: "up" | "down" | "stable" | "new";
    confidence: number;
    evidence_count: number;
  }[];
  key_strengths: string[];
  key_weaknesses: string[];
  action_suggestions: string[];
};

type ExplainEvidence = {
  id: string;
  source_type: string;
  source_id: string;
  quote_text: string;
  score: number;
  confidence: number;
  event_time: string;
  signal_type: string;
  polarity?: number;
  round_no?: number;
  metadata?: Record<string, any>;
};

type SourceSummary = {
  label: string;
  count: number;
  avg_score: number;
  avg_confidence: number;
};

type ExplainResult = {
  dimension: string;
  level: number;
  trend: string;
  confidence: number;
  evidence: ExplainEvidence[];
  evidence_by_source?: Record<string, ExplainEvidence[]>;
  source_summary?: Record<string, SourceSummary>;
};

type SnapshotItem = {
  snapshot_id: string;
  version: string;
  headline: string;
  generated_at: string;
  source_event_id?: string;
};

type SnapshotCompareResult = {
  base_snapshot_id: string;
  target_snapshot_id: string;
  base_generated_at?: string;
  target_generated_at?: string;
  base_headline?: string;
  target_headline?: string;
  summary: string;
  changes: {
    dimension: string;
    change_type: "added" | "removed" | "updated";
    base_level?: number | null;
    target_level?: number | null;
    delta_level?: number | null;
    base_confidence?: number | null;
    target_confidence?: number | null;
    delta_confidence?: number | null;
    base_trend?: string;
    target_trend?: string;
  }[];
};

export default function ProfilePage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [activeTab, setActiveTab] = useState<"basic" | "education" | "work" | "projects" | "skills" | "persona">("basic");

  // Basic
  const [full_name, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [summary, setSummary] = useState("");

  // Repeatable
  const [education, setEducation] = useState<any[]>([]);
  const [work_experience, setWorkExperience] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);

  // Tags
  const [skills, setSkills] = useState<string[]>([]);
  const [certifications, setCertifications] = useState<string[]>([]);
  const [skillInput, setSkillInput] = useState("");
  const [certInput, setCertInput] = useState("");

  const [personaLoading, setPersonaLoading] = useState(false);
  const [persona, setPersona] = useState<PersonaReference | null>(null);
  const [selectedDimension, setSelectedDimension] = useState<string>("");
  const [explainLoading, setExplainLoading] = useState(false);
  const [explainResult, setExplainResult] = useState<ExplainResult | null>(null);
  const [snapshotLoading, setSnapshotLoading] = useState(false);
  const [snapshots, setSnapshots] = useState<SnapshotItem[]>([]);
  const [compareBase, setCompareBase] = useState<string>("");
  const [compareTarget, setCompareTarget] = useState<string>("");
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareResult, setCompareResult] = useState<SnapshotCompareResult | null>(null);

  async function loadPersonaReference() {
      setPersonaLoading(true);
      try {
      const res: any = await personaV2Api.latest();
      setPersona(res.data || null);
      const firstDimension = res?.data?.dimensions?.[0]?.dimension || "";
      if (firstDimension) {
        setSelectedDimension(firstDimension);
        await loadDimensionExplain(firstDimension);
      }
      await loadSnapshots();
    } catch {
      setPersona(null);
    } finally {
      setPersonaLoading(false);
    }
  }

  async function loadSnapshots() {
    setSnapshotLoading(true);
    try {
      const res: any = await personaV2Api.snapshots(20);
      const items: SnapshotItem[] = Array.isArray(res?.data?.items) ? res.data.items : [];
      setSnapshots(items);
      if (!compareBase && items[0]) setCompareBase(items[0].snapshot_id);
      if (!compareTarget && items[1]) setCompareTarget(items[1].snapshot_id);
    } finally {
      setSnapshotLoading(false);
    }
  }

  async function runCompare() {
    if (!compareBase || !compareTarget || compareBase === compareTarget) return;
    setCompareLoading(true);
    try {
      const res: any = await personaV2Api.compare(compareBase, compareTarget);
      setCompareResult(res.data || null);
    } catch {
      setCompareResult(null);
    } finally {
      setCompareLoading(false);
    }
  }

  async function loadDimensionExplain(dimension: string) {
    setExplainLoading(true);
    try {
      const res: any = await personaV2Api.explain(dimension, 8);
      setExplainResult(res.data || null);
    } catch {
      setExplainResult(null);
    } finally {
      setExplainLoading(false);
    }
  }

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    resumeApi
      .get()
      .then((res: any) => {
        if (!mounted) return;
        const data = res.data || {};
        setFullName(data.full_name || "");
        setPhone(data.phone || "");
        setEmail(data.email || "");
        setSummary(data.summary || "");

        setSkills(Array.isArray(data.skills) ? data.skills.slice() : []);
        setCertifications(Array.isArray(data.certifications) ? data.certifications.slice() : []);

        setEducation(
          Array.isArray(data.education)
            ? data.education.map((e: any) => ({ id: crypto.randomUUID(), ...e }))
            : [],
        );

        setWorkExperience(
          Array.isArray(data.work_experience)
            ? data.work_experience.map((w: any) => ({ id: crypto.randomUUID(), ...w }))
            : [],
        );

        setProjects(
          Array.isArray(data.projects) ? data.projects.map((p: any) => ({ id: crypto.randomUUID(), ...p })) : [],
        );
      })
      .catch(() => {
        // silent fail
      })
      .finally(() => {
        setLoading(false);
      });

    loadPersonaReference();

    return () => {
      mounted = false;
    };
  }, []);

  // Education handlers
  function addEducation() {
    setEducation((prev) => [
      ...prev,
      { id: crypto.randomUUID(), school: "", degree: "", major: "", start_date: "", end_date: "", description: "" },
    ]);
  }
  function updateEducation(id: string, field: string, value: string) {
    setEducation((prev) => prev.map((e) => (e.id === id ? { ...e, [field]: value } : e)));
  }
  function removeEducation(id: string) {
    setEducation((prev) => prev.filter((e) => e.id !== id));
  }

  // Work handlers
  function addWork() {
    setWorkExperience((prev) => [
      ...prev,
      { id: crypto.randomUUID(), company: "", position: "", start_date: "", end_date: "", description: "", technologies: "" },
    ]);
  }
  function updateWork(id: string, field: string, value: string) {
    setWorkExperience((prev) => prev.map((w) => (w.id === id ? { ...w, [field]: value } : w)));
  }
  function removeWork(id: string) {
    setWorkExperience((prev) => prev.filter((w) => w.id !== id));
  }

  // Project handlers
  function addProject() {
    setProjects((prev) => [
      ...prev,
      { id: crypto.randomUUID(), name: "", description: "", role: "", start_date: "", end_date: "", technologies: "", achievements: "" },
    ]);
  }
  function updateProject(id: string, field: string, value: string) {
    setProjects((prev) => prev.map((p) => (p.id === id ? { ...p, [field]: value } : p)));
  }
  function removeProject(id: string) {
    setProjects((prev) => prev.filter((p) => p.id !== id));
  }

  // Tags handlers
  function handleSkillKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      const v = skillInput.trim();
      if (v && !skills.includes(v)) setSkills((s) => [...s, v]);
      setSkillInput("");
    }
  }
  function removeSkill(index: number) {
    setSkills((s) => s.filter((_, i) => i !== index));
  }

  function handleCertKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      const v = certInput.trim();
      if (v && !certifications.includes(v)) setCertifications((c) => [...c, v]);
      setCertInput("");
    }
  }
  function removeCert(index: number) {
    setCertifications((c) => c.filter((_, i) => i !== index));
  }

  async function handleSave() {
    setSaving(true);
    setSaved(false);
    try {
      const payload: any = {
        full_name: full_name || undefined,
        phone: phone || undefined,
        email: email || undefined,
        summary: summary || undefined,
        skills: skills,
        certifications: certifications,
        education: education.map(({ id, ...rest }) => rest),
        work_experience: work_experience.map(({ id, ...rest }) => rest),
        projects: projects.map(({ id, ...rest }) => rest),
      };
      await resumeApi.update(payload);
      await personaV2Api.rebuild();
      await loadPersonaReference();
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      // do not alert
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl">
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-text-muted" />
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl">
      <Link href="/" className="mb-4 inline-flex items-center gap-1 text-sm text-text-secondary hover:text-text-primary">
        <ArrowLeft className="h-4 w-4" />
        返回看板
      </Link>

      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">简历编辑</h1>
          <p className="mt-1 text-sm text-text-secondary">编辑你的简历，供匹配与面试使用</p>
        </div>
      </div>

      <div className="mb-4 flex items-center gap-2">
        <TabButton active={activeTab === "basic"} onClick={() => setActiveTab("basic")} icon={<User className="h-4 w-4" />} label="基本信息" />
        <TabButton active={activeTab === "education"} onClick={() => setActiveTab("education")} icon={<GraduationCap className="h-4 w-4" />} label="教育背景" />
        <TabButton active={activeTab === "work"} onClick={() => setActiveTab("work")} icon={<Briefcase className="h-4 w-4" />} label="工作经历" />
        <TabButton active={activeTab === "projects"} onClick={() => setActiveTab("projects")} icon={<FolderKanban className="h-4 w-4" />} label="项目经验" />
        <TabButton active={activeTab === "skills"} onClick={() => setActiveTab("skills")} icon={<Award className="h-4 w-4" />} label="技能证书" />
        <TabButton active={activeTab === "persona"} onClick={() => setActiveTab("persona")} icon={<Sparkles className="h-4 w-4" />} label="人物画像" />
      </div>

      <div className="rounded-xl border border-border bg-surface p-6">
        {activeTab === "basic" && (
          <div className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-text-secondary">姓名</label>
              <input value={full_name} onChange={(e) => setFullName(e.target.value)} placeholder="姓名" className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-text-secondary">电话</label>
                <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="手机" className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-text-secondary">邮箱</label>
                <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="电子邮箱" className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
              </div>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-text-secondary">简介</label>
              <textarea rows={4} value={summary} onChange={(e) => setSummary(e.target.value)} placeholder="一句话概述你的职业背景与目标" className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
            </div>
          </div>
        )}

        {activeTab === "education" && (
          <div className="space-y-4">
            {education.map((e, idx) => (
              <div key={e.id} className="rounded-lg border border-border bg-surface/50 p-4">
                <div className="mb-3 flex items-center justify-between">
                  <span className="text-sm font-medium text-text-primary">教育 {idx + 1}</span>
                  <button type="button" onClick={() => removeEducation(e.id)} className="rounded-md p-1 text-text-muted hover:bg-surface-muted hover:text-error">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>

                <div className="space-y-3">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-text-secondary">学校</label>
                    <input value={e.school} onChange={(ev) => updateEducation(e.id, "school", ev.target.value)} className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
                  </div>

                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="mb-1 block text-sm font-medium text-text-secondary">学位</label>
                      <input value={e.degree} onChange={(ev) => updateEducation(e.id, "degree", ev.target.value)} className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm font-medium text-text-secondary">专业</label>
                      <input value={e.major} onChange={(ev) => updateEducation(e.id, "major", ev.target.value)} className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm font-medium text-text-secondary">开始</label>
                      <input value={e.start_date} onChange={(ev) => updateEducation(e.id, "start_date", ev.target.value)} placeholder="YYYY-MM" className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="mb-1 block text-sm font-medium text-text-secondary">结束</label>
                      <input value={e.end_date} onChange={(ev) => updateEducation(e.id, "end_date", ev.target.value)} placeholder="YYYY-MM" className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm font-medium text-text-secondary">描述</label>
                      <textarea rows={3} value={e.description} onChange={(ev) => updateEducation(e.id, "description", ev.target.value)} className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
                    </div>
                  </div>
                </div>
              </div>
            ))}

            <button type="button" onClick={addEducation} className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-dashed border-border py-3 text-sm text-text-secondary hover:border-brand hover:text-brand">
              <Plus className="h-4 w-4" /> 添加教育经历
            </button>
          </div>
        )}

        {activeTab === "work" && (
          <div className="space-y-4">
            {work_experience.map((w, idx) => (
              <div key={w.id} className="rounded-lg border border-border bg-surface/50 p-4">
                <div className="mb-3 flex items-center justify-between">
                  <span className="text-sm font-medium text-text-primary">工作 {idx + 1}</span>
                  <button type="button" onClick={() => removeWork(w.id)} className="rounded-md p-1 text-text-muted hover:bg-surface-muted hover:text-error">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>

                <div className="space-y-3">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-text-secondary">公司</label>
                    <input value={w.company} onChange={(ev) => updateWork(w.id, "company", ev.target.value)} className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
                  </div>

                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="mb-1 block text-sm font-medium text-text-secondary">职位</label>
                      <input value={w.position} onChange={(ev) => updateWork(w.id, "position", ev.target.value)} className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm font-medium text-text-secondary">开始</label>
                      <input value={w.start_date} onChange={(ev) => updateWork(w.id, "start_date", ev.target.value)} placeholder="YYYY-MM" className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm font-medium text-text-secondary">结束</label>
                      <input value={w.end_date} onChange={(ev) => updateWork(w.id, "end_date", ev.target.value)} placeholder="YYYY-MM" className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
                    </div>
                  </div>

                  <div>
                    <label className="mb-1 block text-sm font-medium text-text-secondary">描述</label>
                    <textarea rows={3} value={w.description} onChange={(ev) => updateWork(w.id, "description", ev.target.value)} className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
                  </div>

                  <div>
                    <label className="mb-1 block text-sm font-medium text-text-secondary">技术栈 (逗号分隔)</label>
                    <input value={w.technologies} onChange={(ev) => updateWork(w.id, "technologies", ev.target.value)} placeholder="例如: React, Node.js" className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
                  </div>
                </div>
              </div>
            ))}

            <button type="button" onClick={addWork} className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-dashed border-border py-3 text-sm text-text-secondary hover:border-brand hover:text-brand">
              <Plus className="h-4 w-4" /> 添加工作经历
            </button>
          </div>
        )}

        {activeTab === "projects" && (
          <div className="space-y-4">
            {projects.map((p, idx) => (
              <div key={p.id} className="rounded-lg border border-border bg-surface/50 p-4">
                <div className="mb-3 flex items-center justify-between">
                  <span className="text-sm font-medium text-text-primary">项目 {idx + 1}</span>
                  <button type="button" onClick={() => removeProject(p.id)} className="rounded-md p-1 text-text-muted hover:bg-surface-muted hover:text-error">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>

                <div className="space-y-3">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-text-secondary">名称</label>
                    <input value={p.name} onChange={(ev) => updateProject(p.id, "name", ev.target.value)} className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
                  </div>

                  <div>
                    <label className="mb-1 block text-sm font-medium text-text-secondary">角色</label>
                    <input value={p.role} onChange={(ev) => updateProject(p.id, "role", ev.target.value)} className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="mb-1 block text-sm font-medium text-text-secondary">开始</label>
                      <input value={p.start_date} onChange={(ev) => updateProject(p.id, "start_date", ev.target.value)} placeholder="YYYY-MM" className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm font-medium text-text-secondary">结束</label>
                      <input value={p.end_date} onChange={(ev) => updateProject(p.id, "end_date", ev.target.value)} placeholder="YYYY-MM" className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
                    </div>
                  </div>

                  <div>
                    <label className="mb-1 block text-sm font-medium text-text-secondary">技术栈 (逗号分隔)</label>
                    <input value={p.technologies} onChange={(ev) => updateProject(p.id, "technologies", ev.target.value)} placeholder="例如: React, Docker" className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
                  </div>

                  <div>
                    <label className="mb-1 block text-sm font-medium text-text-secondary">成果 / 描述</label>
                    <textarea rows={3} value={p.achievements} onChange={(ev) => updateProject(p.id, "achievements", ev.target.value)} placeholder="项目亮点或成果" className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
                  </div>

                  <div>
                    <label className="mb-1 block text-sm font-medium text-text-secondary">描述</label>
                    <textarea rows={3} value={p.description} onChange={(ev) => updateProject(p.id, "description", ev.target.value)} className="w-full rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
                  </div>
                </div>
              </div>
            ))}

            <button type="button" onClick={addProject} className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-dashed border-border py-3 text-sm text-text-secondary hover:border-brand hover:text-brand">
              <Plus className="h-4 w-4" /> 添加项目经验
            </button>
          </div>
        )}

        {activeTab === "skills" && (
          <div className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-text-secondary">技能</label>
              <div className="flex flex-wrap gap-2">
                {skills.map((s, i) => (
                  <div key={s + i} className="inline-flex items-center gap-2 rounded-full bg-surface px-3 py-1 text-sm">
                    <span className="text-text-primary">{s}</span>
                    <button type="button" onClick={() => removeSkill(i)} className="rounded-full p-1 text-text-muted hover:bg-surface-muted">
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                ))}
                <input value={skillInput} onChange={(e) => setSkillInput(e.target.value)} onKeyDown={handleSkillKeyDown} placeholder="输入技能并按 Enter 添加" className="w-48 rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
              </div>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-text-secondary">证书</label>
              <div className="flex flex-wrap gap-2">
                {certifications.map((c, i) => (
                  <div key={c + i} className="inline-flex items-center gap-2 rounded-full bg-surface px-3 py-1 text-sm">
                    <span className="text-text-primary">{c}</span>
                    <button type="button" onClick={() => removeCert(i)} className="rounded-full p-1 text-text-muted hover:bg-surface-muted">
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                ))}
                <input value={certInput} onChange={(e) => setCertInput(e.target.value)} onKeyDown={handleCertKeyDown} placeholder="输入证书并按 Enter 添加" className="w-48 rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none focus:border-input-focus focus:ring-1 focus:ring-input-focus placeholder:text-text-muted" />
              </div>
            </div>
          </div>
        )}

        {activeTab === "persona" && (
          <div className="space-y-4">
            <div className="rounded-lg border border-border bg-surface/50 p-4">
              <div className="mb-2 flex items-center gap-2 text-text-primary">
                <Sparkles className="h-4 w-4 text-brand" />
                <span className="text-sm font-medium">人物画像参考</span>
              </div>
              {!personaLoading && persona?.version && (
                <p className="mb-2 text-xs text-text-muted">画像版本 {persona.version}{persona.generated_at ? ` · 生成时间 ${new Date(persona.generated_at).toLocaleString("zh-CN")}` : ""}</p>
              )}
              {personaLoading ? (
                <div className="flex items-center gap-2 text-sm text-text-secondary">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  正在生成画像...
                </div>
              ) : (
                <p className="text-sm leading-6 text-text-secondary">{persona?.headline || "暂无画像数据，请先保存简历并完成至少一次面试复盘。"}</p>
              )}
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="rounded-lg border border-border bg-surface/50 p-4">
                <div className="mb-2 flex items-center gap-2 text-sm font-medium text-text-primary">
                  <TrendingUp className="h-4 w-4 text-success" /> 核心优势
                </div>
                <div className="space-y-2 text-sm text-text-secondary">
                  {(persona?.key_strengths || []).length > 0 ? (
                    persona?.key_strengths.map((item, idx) => <div key={`${item}-${idx}`}>• {item}</div>)
                  ) : (
                    <div>暂无数据</div>
                  )}
                </div>
              </div>

              <div className="rounded-lg border border-border bg-surface/50 p-4">
                <div className="mb-2 flex items-center gap-2 text-sm font-medium text-text-primary">
                  <Target className="h-4 w-4 text-warning" /> 待提升点
                </div>
                <div className="space-y-2 text-sm text-text-secondary">
                  {(persona?.key_weaknesses || []).length > 0 ? (
                    persona?.key_weaknesses.map((item, idx) => <div key={`${item}-${idx}`}>• {item}</div>)
                  ) : (
                    <div>暂无数据</div>
                  )}
                </div>
              </div>
            </div>

            <div className="rounded-lg border border-border bg-surface/50 p-4">
              <div className="mb-2 text-sm font-medium text-text-primary">能力维度（点击查看证据）</div>
              <div className="space-y-2 text-sm text-text-secondary">
                {(persona?.dimensions || []).length > 0 ? (
                  persona?.dimensions?.map((item, idx) => (
                    <button
                      key={`${item.dimension}-${idx}`}
                      type="button"
                      onClick={() => {
                        setSelectedDimension(item.dimension);
                        loadDimensionExplain(item.dimension);
                      }}
                      className={cn(
                        "w-full rounded-md border px-3 py-2 text-left",
                        selectedDimension === item.dimension ? "border-brand bg-brand/10 text-text-primary" : "border-border text-text-secondary hover:border-brand/60",
                      )}
                    >
                      <div>{item.dimension}</div>
                      <div className="mt-1 text-xs text-text-muted">等级 {item.level}/5 · 趋势 {item.trend} · 置信度 {item.confidence} · 证据 {item.evidence_count}</div>
                    </button>
                  ))
                ) : (
                  <div>暂无数据</div>
                )}
              </div>
            </div>

            <div className="rounded-lg border border-border bg-surface/50 p-4">
              <div className="mb-2 text-sm font-medium text-text-primary">行动建议（可直接执行）</div>
              <div className="space-y-2 text-sm text-text-secondary">
                {(persona?.action_suggestions || []).length > 0 ? (
                  persona?.action_suggestions.map((item, idx) => <div key={`${item}-${idx}`}>• {item}</div>)
                ) : (
                  <div>暂无数据</div>
                )}
              </div>
            </div>

            <div className="rounded-lg border border-border bg-surface/50 p-4">
              <div className="mb-2 text-sm font-medium text-text-primary">证据明细 {selectedDimension ? `· ${selectedDimension}` : ""}</div>

              {explainLoading ? (
                <div className="flex items-center gap-2 text-sm text-text-secondary">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  正在加载证据...
                </div>
              ) : explainResult?.evidence_by_source ? (
                <div className="space-y-4">
                  {/* 两条线对比统计 */}
                  {explainResult.source_summary && Object.keys(explainResult.source_summary).length > 0 && (
                    <div className="grid grid-cols-2 gap-3">
                      {Object.entries(explainResult.source_summary).map(([source, stats]) => (
                        <div key={source} className="rounded-lg bg-surface-muted p-3">
                          <div className="text-sm font-medium text-text-primary mb-1">{stats.label}</div>
                          <div className="text-xs text-text-muted">
                            {stats.count} 条证据 · 平均分 {stats.avg_score} · 置信度 {stats.avg_confidence}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* 按来源分组展示证据 */}
                  {Object.entries(explainResult.evidence_by_source || {}).map(([source, evidences]) => {
                    const label = explainResult.source_summary?.[source]?.label || source;
                    return (
                      <div key={source}>
                        <div className="text-xs font-medium text-text-muted mb-2 uppercase tracking-wide">
                          {label}（{evidences.length} 条）
                        </div>
                        <div className="space-y-2">
                          {evidences.map((item, idx) => (
                            <div key={`${item.id}-${idx}`} className="rounded-md border border-border px-3 py-2">
                              <div className="flex items-center gap-2 text-xs">
                                <span className={cn(
                                  "px-1.5 py-0.5 rounded text-xs font-medium",
                                  item.signal_type === "strength" ? "bg-success/20 text-success" : "bg-error/20 text-error"
                                )}>
                                  {item.signal_type === "strength" ? "强" : "弱"}
                                </span>
                                <span className="text-text-muted">分数 {item.score}</span>
                                <span className="text-text-muted">置信度 {item.confidence}</span>
                              </div>
                              <div className="mt-1 text-xs text-text-muted line-clamp-2">{item.quote_text}</div>
                              <div className="mt-1 text-xs text-text-muted">
                                {item.event_time ? new Date(item.event_time).toLocaleString("zh-CN") : ""}
                                {item.metadata?.from ? ` · ${item.metadata.from}` : ""}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (explainResult?.evidence || []).length > 0 ? (
                <div className="space-y-2">
                  {explainResult?.evidence.map((item, idx) => (
                    <div key={`${item.id}-${idx}`} className="rounded-md border border-border px-3 py-2">
                      <div className="text-text-primary">{item.signal_type} · 分数 {item.score} · 置信度 {item.confidence}</div>
                      <div className="mt-1 text-xs text-text-muted">{item.quote_text}</div>
                      <div className="mt-1 text-xs text-text-muted">来源 {item.source_type} · {item.event_time ? new Date(item.event_time).toLocaleString("zh-CN") : ""}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-text-muted">暂无数据</div>
              )}
            </div>

            <div className="rounded-lg border border-border bg-surface/50 p-4">
              <div className="mb-2 text-sm font-medium text-text-primary">画像版本对比</div>
              {snapshotLoading ? (
                <div className="flex items-center gap-2 text-sm text-text-secondary">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  正在加载快照...
                </div>
              ) : snapshots.length === 0 ? (
                <div className="text-sm text-text-secondary">暂无快照</div>
              ) : (
                <>
                  <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
                    <select
                      value={compareBase}
                      onChange={(e) => setCompareBase(e.target.value)}
                      className="rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none"
                    >
                      <option value="">选择基准快照</option>
                      {snapshots.map((s) => (
                        <option key={`base-${s.snapshot_id}`} value={s.snapshot_id}>
                          {new Date(s.generated_at).toLocaleString("zh-CN")} · {s.snapshot_id.slice(0, 8)}
                        </option>
                      ))}
                    </select>

                    <select
                      value={compareTarget}
                      onChange={(e) => setCompareTarget(e.target.value)}
                      className="rounded-lg border border-input-border bg-input-bg px-3 py-2 text-sm text-text-primary outline-none"
                    >
                      <option value="">选择目标快照</option>
                      {snapshots.map((s) => (
                        <option key={`target-${s.snapshot_id}`} value={s.snapshot_id}>
                          {new Date(s.generated_at).toLocaleString("zh-CN")} · {s.snapshot_id.slice(0, 8)}
                        </option>
                      ))}
                    </select>

                    <button
                      type="button"
                      onClick={runCompare}
                      disabled={compareLoading || !compareBase || !compareTarget || compareBase === compareTarget}
                      className="rounded-lg bg-brand px-3 py-2 text-sm font-medium text-text-inverse disabled:opacity-50"
                    >
                      {compareLoading ? "对比中..." : "执行对比"}
                    </button>
                  </div>

                  {compareResult && (
                    <div className="mt-3 space-y-2">
                      <div className="text-xs text-text-muted">{compareResult.summary}</div>
                      {(compareResult.changes || []).length > 0 ? (
                        compareResult.changes.map((c, idx) => (
                          <div key={`${c.dimension}-${idx}`} className="rounded-md border border-border px-3 py-2">
                            <div className="text-text-primary">{c.dimension} · {c.change_type}</div>
                            <div className="mt-1 text-xs text-text-muted">
                              等级 {c.base_level ?? "-"} → {c.target_level ?? "-"}
                              {typeof c.delta_level === "number" ? `（Δ ${c.delta_level >= 0 ? `+${c.delta_level}` : c.delta_level}）` : ""}
                              ，置信度 {c.base_confidence ?? "-"} → {c.target_confidence ?? "-"}
                              {typeof c.delta_confidence === "number" ? `（Δ ${c.delta_confidence >= 0 ? `+${c.delta_confidence}` : c.delta_confidence}）` : ""}
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="text-sm text-text-secondary">无差异</div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Sticky save bar */}
      <div className="fixed bottom-4 left-0 right-0 flex justify-center pointer-events-none">
        <div className="mx-auto w-full max-w-4xl rounded-lg border border-border bg-surface p-3 pointer-events-auto">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {saving && <Loader2 className="h-4 w-4 animate-spin text-text-muted" />}
              {saved && (
                <div className="inline-flex items-center gap-1 text-sm text-success-text">
                  <CheckCircle className="h-4 w-4 text-success" /> 已保存
                </div>
              )}
            </div>
            <div>
              <button onClick={handleSave} disabled={saving} className="inline-flex items-center gap-1.5 rounded-lg bg-brand px-6 py-2.5 text-sm font-medium text-text-inverse hover:bg-brand-hover disabled:opacity-50">
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                保存
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function TabButton({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: React.ReactNode; label: string }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium",
        active ? "bg-brand text-text-inverse" : "text-text-secondary hover:text-text-primary",
      )}
    >
      <span className="opacity-90">{icon}</span>
      <span>{label}</span>
    </button>
  );
}
