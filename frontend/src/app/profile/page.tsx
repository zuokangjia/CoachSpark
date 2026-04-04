"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { resumeApi } from "@/lib/api-client";
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
} from "lucide-react";

export default function ProfilePage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [activeTab, setActiveTab] = useState<"basic" | "education" | "work" | "projects" | "skills">("basic");

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
