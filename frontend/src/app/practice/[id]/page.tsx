"use client";

import React, { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

export default function QuestionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const questionId = params.id as string;

  useEffect(() => {
    router.replace("/practice/drill");
  }, [router, questionId]);

  return (
    <div className="mx-auto max-w-3xl">
      <div className="flex h-64 flex-col items-center justify-center text-sm text-text-muted">
        <p>单题练习已移除，正在跳转到 AI 生成...</p>
        <Link href="/practice/drill" className="mt-2 text-brand hover:text-brand-hover">
          如果没有跳转，点击这里
        </Link>
      </div>
    </div>
  );
}