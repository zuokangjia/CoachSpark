"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function PracticeHistoryPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/practice/drills/history");
  }, [router]);

  return (
    <div className="mx-auto max-w-4xl">
      <div className="flex h-64 flex-col items-center justify-center text-sm text-text-muted">
        <p>正在跳转到练习记录...</p>
        <Link href="/practice/drills/history" className="mt-2 text-brand hover:text-brand-hover">
          如果没有跳转，点击这里
        </Link>
      </div>
    </div>
  );
}