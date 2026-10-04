"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

import {
  describeApiError,
  describeUnknownError,
} from "@/components/auth/api-error-message";
import { verifyEmail } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { FormError } from "@/components/ui/form-error";

type VerifyState =
  | { kind: "verifying" }
  | { kind: "success" }
  | { kind: "error"; message: string; retryable: boolean };

export function VerifyEmailPanel() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const [state, setState] = useState<VerifyState>({ kind: "verifying" });
  const autoRanRef = useRef(false);

  const runVerify = useCallback(async () => {
    setState({ kind: "verifying" });
    try {
      await verifyEmail({ token });
      setState({ kind: "success" });
    } catch (error) {
      if (error instanceof ApiError) {
        setState({
          kind: "error",
          message: describeApiError(error),
          // Only transient failures get a retry button; an invalid or used
          // token is permanently dead, so retrying would mislead.
          retryable: error.code === "network" || error.code === "rate_limited",
        });
      } else {
        setState({
          kind: "error",
          message: describeUnknownError(),
          retryable: true,
        });
      }
    }
  }, [token]);

  useEffect(() => {
    if (!token) {
      setState({
        kind: "error",
        message: "This link is missing its token.",
        retryable: false,
      });
      return;
    }
    // Auto-submit exactly once (guards React StrictMode double-invoke in dev).
    if (autoRanRef.current) return;
    autoRanRef.current = true;
    void runVerify();
  }, [token, runVerify]);

  if (state.kind === "verifying") {
    return (
      <div className="space-y-2 text-center">
        <h1 className="text-xl font-semibold">Verifying your email</h1>
        <p className="text-sm text-ink-soft" role="status">
          One moment, we are confirming your link...
        </p>
      </div>
    );
  }

  if (state.kind === "success") {
    return (
      <div className="space-y-3 text-center" role="status">
        <h1 className="text-xl font-semibold">Email verified</h1>
        <p className="text-sm text-ink-soft">
          Your email address is confirmed. You can sign in now.
        </p>
        <Link href="/login" className="text-sm font-medium text-accent hover:underline">
          Back to sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-3 text-center">
      <h1 className="text-xl font-semibold">We could not verify your email</h1>
      <FormError>{state.message}</FormError>
      {state.retryable && (
        <Button
          type="button"
          variant="secondary"
          onClick={() => void runVerify()}
        >
          Try again
        </Button>
      )}
      <p>
        <Link href="/login" className="text-sm font-medium text-accent hover:underline">
          Back to sign in
        </Link>
      </p>
    </div>
  );
}
