"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import {
  describeApiError,
  describeUnknownError,
} from "@/components/auth/api-error-message";
import { AuthFormField } from "@/components/auth/auth-form-field";
import { requestPasswordReset } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { FormError } from "@/components/ui/form-error";
import {
  forgotPasswordSchema,
  type ForgotPasswordInput,
} from "@/lib/auth/schemas";

export function ForgotPasswordForm() {
  const [sent, setSent] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordInput>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null);
    try {
      await requestPasswordReset(values);
      setSent(true); // generic response: identical state for every outcome
    } catch (error) {
      setFormError(
        error instanceof ApiError
          ? describeApiError(error)
          : describeUnknownError()
      );
    }
  });

  if (sent) {
    return (
      <div className="space-y-3 text-center" role="status">
        <h1 className="text-xl font-semibold">Check your inbox</h1>
        <p className="text-sm text-ink-soft">
          If that email address has an account, a password reset link has been
          sent to it.
        </p>
        <Link href="/login" className="text-sm font-medium text-accent hover:underline">
          Back to sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="space-y-1">
        <h1 className="text-xl font-semibold">Forgot your password?</h1>
        <p className="text-sm text-ink-soft">
          Enter your email and we will send you a reset link.
        </p>
      </div>
      <form onSubmit={onSubmit} noValidate className="space-y-4">
        <AuthFormField
          id="email"
          label="Email"
          type="email"
          autoComplete="email"
          error={errors.email?.message}
          {...register("email")}
        />
        <FormError>{formError ?? undefined}</FormError>
        <Button type="submit" loading={isSubmitting} className="w-full">
          Send reset link
        </Button>
      </form>
      <p className="text-center text-sm text-ink-soft">
        Remembered it?{" "}
        <Link href="/login" className="font-medium text-accent hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}
