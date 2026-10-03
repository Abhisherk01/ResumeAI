import Link from "next/link";
import { FileText } from "lucide-react";

import { cn } from "@/lib/utils";

export function Logo({ className }: { className?: string }) {
  return (
    <Link
      href="/"
      aria-label="ResumeAI home"
      className={cn("flex items-center gap-2 font-semibold text-ink", className)}
    >
      <span className="flex h-9 w-9 items-center justify-center rounded-neu bg-accent text-on-accent shadow-neu-raised-sm">
        <FileText className="h-5 w-5" aria-hidden="true" />
      </span>
      <span className="text-lg tracking-tight">ResumeAI</span>
    </Link>
  );
}
