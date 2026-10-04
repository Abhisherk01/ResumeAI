import type { Metadata } from "next";
import { Suspense } from "react";

import { VerifyEmailPanel } from "@/components/auth/verify-email-panel";

export const metadata: Metadata = { title: "Verify email - ResumeAI" };

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<p className="text-sm text-ink-soft">Loading...</p>}>
      <VerifyEmailPanel />
    </Suspense>
  );
}
