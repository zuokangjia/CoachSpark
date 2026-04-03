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
  { id: "applied", title: "已投递", color: "bg-blue-50 border-blue-200" },
  { id: "interviewing", title: "面试中", color: "bg-amber-50 border-amber-200" },
  { id: "closed", title: "已结束", color: "bg-gray-50 border-gray-200" },
] as const;
