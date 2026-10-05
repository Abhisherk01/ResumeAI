"use client";

import Link from "next/link";
import { CheckCircle2, Circle, Upload } from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import { Card } from "@/components/ui/card";

const STEPS = [
  {
    id: "verify-email",
    label: "Verify your email address",
    done: (verified: boolean) => verified,
  },
  {
    id: "explore-themes",
    label: "Personalize your workspace with a theme",
    done: () => false, // theme choice is client-side; treated as always open
  },
  {
    id: "upload-resume",
    label: "Upload your first resume",
    done: () => false, // Phase 5
  },
] as const;

/**
 * Onboarding checklist (P4-1): an honest empty state. Email verification
 * reflects real account state; the resume step points at Phase 5 and says
 * so, instead of pretending an upload flow exists.
 */
export function GettingStarted() {
  const { user } = useAuth();

  if (!user) return null; // unreachable under the (app) gate; defensive

  return (
    <Card title="Getting started" className="space-y-4">
      <ol className="space-y-3">
        {STEPS.map((step) => {
          const isDone = step.done(user.email_verified);
          const isUpload = step.id === "upload-resume";
          const content = (
            <>
              {isDone ? (
                <CheckCircle2 className="h-4 w-4 shrink-0 text-success" aria-hidden="true" />
              ) : (
                <Circle className="h-4 w-4 shrink-0 text-ink-soft" aria-hidden="true" />
              )}
              <span className={isDone ? "text-ink-soft line-through" : "text-ink"}>
                {step.label}
              </span>
              {isUpload && (
                <span className="ml-auto inline-flex items-center gap-1 rounded-neu bg-base px-2 py-0.5 text-xs text-ink-soft shadow-neu-inset">
                  <Upload className="h-3 w-3" aria-hidden="true" />
                  Phase 5
                </span>
              )}
            </>
          );
          return (
            <li key={step.id} className="flex items-center gap-3 text-sm">
              {isUpload ? (
                <span className="flex w-full items-center gap-3">{content}</span>
              ) : (
                content
              )}
            </li>
          );
        })}
      </ol>
      <p className="text-xs text-ink-soft">
        Resume upload and AI analysis arrive in Phase 5-6. This checklist
        updates as you complete each step.
      </p>
    </Card>
  );
}
