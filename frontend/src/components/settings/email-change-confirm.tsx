"use client";

/**
 * Consumes the emailed change token (Phase 10, D24): the link lands on
 * /settings?email-token=... . Fires ONCE (StrictMode-safe ref guard),
 * refreshes the shared user state when a session exists (silent when the
 * confirm is anonymous), and strips the token from the address bar so a
 * refresh or history walk can never replay it.
 */

import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";

import { describeApiError, describeUnknownError } from "@/components/auth/api-error-message";
import { useAuth } from "@/components/auth/auth-provider";
import { confirmEmailChange, getCurrentUser } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import { FormError } from "@/components/ui/form-error";

export function EmailChangeConfirm() {
  const params = useSearchParams();
  const token = params.get("email-token");
  const { setUser } = useAuth();
  const [status, setStatus] = useState<"idle" | "working" | "done" | "error">("idle");
  const [message, setMessage] = useState<string | null>(null);
  const startedRef = useRef(false);

  useEffect(() => {
    if (!token || startedRef.current) return;
    startedRef.current = true;
    setStatus("working");
    confirmEmailChange({ token })
      .then(async (result) => {
        setStatus("done");
        setMessage(result.message);
        try {
          setUser(await getCurrentUser());
        } catch {
          /* anonymous confirm: no session to refresh */
        }
      })
      .catch((error) => {
        setStatus("error");
        setMessage(
          error instanceof ApiError ? describeApiError(error) : describeUnknownError()
        );
      })
      .finally(() => {
        window.history.replaceState(null, "", "/settings");
      });
  }, [token, setUser]);

  if (!token) return null;

  return (
    <div role="status" aria-live="polite" className="space-y-2">
      {status === "working" && (
        <p className="text-sm text-ink-soft">Updating your email address...</p>
      )}
      {status === "done" && <p className="text-sm text-success">{message}</p>}
      {status === "error" && <FormError>{message ?? undefined}</FormError>}
    </div>
  );
}
