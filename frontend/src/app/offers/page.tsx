"use client";

import Link from "next/link";
import { ArrowLeft, Briefcase } from "lucide-react";

export default function OffersPage() {
  return (
    <div>
      <Link
        href="/"
        className="mb-4 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700"
      >
        <ArrowLeft className="h-4 w-4" />
        返回看板
      </Link>

      <div className="flex flex-col items-center justify-center rounded-xl border border-slate-200 bg-white py-24">
        <Briefcase className="mb-4 h-12 w-12 text-slate-300" />
        <h1 className="text-xl font-semibold text-slate-900">Offer 比较</h1>
        <p className="mt-2 text-sm text-slate-500">
          拿到 Offer 后再来比较吧
        </p>
      </div>
    </div>
  );
}
