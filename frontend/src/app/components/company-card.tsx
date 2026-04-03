"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import Link from "next/link";
import { Calendar, Clock } from "lucide-react";
import { formatDate, cn } from "@/lib/utils";

interface Company {
  id: string;
  name: string;
  position: string;
  status: string;
  applied_date: string | null;
  next_event_date: string | null;
  next_event_type: string | null;
}

export function CompanyCard({ company }: { company: Company }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: company.id });

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <Link href={`/company/${company.id}`}>
      <div
        ref={setNodeRef}
        style={style}
        {...attributes}
        {...listeners}
        className={cn(
          "cursor-grab rounded-lg border border-slate-200 bg-white p-3 active:cursor-grabbing",
          "hover:border-slate-300 hover:shadow-sm",
        )}
      >
        <h3 className="text-sm font-semibold text-slate-900">{company.name}</h3>
        <p className="mt-0.5 text-xs text-slate-500">{company.position}</p>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {company.applied_date && (
            <span className="inline-flex items-center gap-1 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-600">
              <Calendar className="h-3 w-3" />
              {formatDate(company.applied_date)}
            </span>
          )}
          {company.next_event_date && (
            <span className="inline-flex items-center gap-1 rounded bg-blue-50 px-1.5 py-0.5 text-[10px] text-blue-700">
              <Clock className="h-3 w-3" />
              {company.next_event_type || "事件"} · {formatDate(company.next_event_date)}
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
