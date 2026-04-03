import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateStr: string | null): string {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("zh-CN");
}

export const COLUMNS = [
  { id: "applied", title: "已投递", color: "bg-col-applied-bg border-col-applied-border" },
  { id: "interviewing", title: "面试中", color: "bg-col-interviewing-bg border-col-interviewing-border" },
  { id: "closed", title: "已结束", color: "bg-col-closed-bg border-col-closed-border" },
] as const;
