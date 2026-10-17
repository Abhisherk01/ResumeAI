"use client";

import Link from "next/link";
import { CheckCircle2, Circle } from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import { Card } from "@/components/ui/card";

const STEPS = [
  {
    id: "verify-email",
    label: "Verify your email address",
    href: null,
    done: (verified: boolean) => verified,
  },
  {
    id: "explore-themes",
    label: "Personalize your workspace with a theme",
    href: "/settings",
    done: () => false, // theme choice is client-side; treated as always open
  },
  {
    id: "upload-resume",
    label: "Upload your first resume",
    href: "/resumes",
    done: () => false,
  },
] as const;

/**
  * Onboarding checklist (P4-1). Email verification reflects real account
 * state; the other steps deep-link to the flows that ship with them
 * (Resumes for upload/analysis, Settings for the theme switcher).
 */
export function GettingStarted() {
  const { user } = useAuth();

  if (!user) return null; // unreachable under the (app) gate; defensive

  return (
    <Card title="Getting started" className="space-y-4">
      <ol className="space-y-3">
      {STEPS.map((step) => {
          const isDone = step.done(user.email_verified);
          const content = (
            <>
              {isDone ? (
                <CheckCircle2 className="h-4 w-4 shrink-0 text-success" aria-hidden="true" />
              ) : (
                <Circle className="h-4 w-4 shrink-0 text-ink-soft" aria-hidden="true" />
              )}
              {step.href ? (
                <Link
                  href={step.href}
                  className={
                    isDone
                      ? "text-ink-soft line-through hover:text-accent"
                      : "text-ink hover:text-accent"
                  }
                >
                  {step.label}
                </Link>
              ) : (
                <span className={isDone ? "text-ink-soft line-through" : "text-ink"}>
                  {step.label}
                </span>
              )}
            </>
          );
          return (
            <li key={step.id} className="flex items-center gap-3 text-sm">
              {step.href ? (
                <span className="flex w-full items-center gap-3">{content}</span>
              ) : (
                content
              )}
            </li>
          );
        })}
      </ol>
      <p className="text-xs text-ink-soft">
        Verification updates automatically. Upload and analyze under Resumes;
        pick your theme under Settings.
      </p>
    </Card>
  );
}
