"use client";

import { useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import {
  describeApiError,
  describeUnknownError,
} from "@/components/auth/api-error-message";
import { AuthFormField } from "@/components/auth/auth-form-field";
import { confirmPasswordReset } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { FormError } from "@/components/ui/form-error";
import { passwordField } from "@/lib/auth/schemas";

// Form-local schema: validates the two password fields only. The token
// comes from the URL, not the form, so it is attached at call time (the
// schemas.ts resetPasswordSchema additionally models the full payload).
const resetFormSchema = z
  .object({
    new_password: passwordField,
    confirmPassword: z.string().min(1, "Please confirm the password."),
  })
  .refine((data) => data.new_password === data.confirmPassword, {
    message: "Passwords do not match.",
    path: ["confirmPassword"],
  });

type ResetFormValues = z.infer<typeof resetFormSchema>;

export function ResetPasswordPanel() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const [formError, setFormError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [linkInvalid, setLinkInvalid] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetFormValues>({ resolver: zodResolver(resetFormSchema) });

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null);
    try {
      await confirmPasswordReset({
        token,
        new_password: values.new_password,
      });
      setDone(true);
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.code === "token_invalid") {
          // Expired or already used: the form is useless now, route the
          // user to a fresh request instead of a red field.
          setLinkInvalid(true);
          return;
        }
        setFormError(describeApiError(error));
      } else {
        setFormError(describeUnknownError());
      }
    }
  });

  if (!token) {
    return (
      <div className="space-y-3 text-center">
        <h1 className="text-xl font-semibold">Reset your password</h1>
        <FormError>This link is missing its token.</FormError>
        <p>
          <Link
            href="/forgot-password"
            className="text-sm font-medium text-accent hover:underline"
          >
            Request a new reset email
          </Link>
        </p>
      </div>
    );
  }

  if (linkInvalid) {
    return (
      <div className="space-y-3 text-center">
        <h1 className="text-xl font-semibold">This link has expired</h1>
        <p className="text-sm text-ink-soft">
          Reset links are valid for 30 minutes and can be used once.
        </p>
        <p>
          <Link
            href="/forgot-password"
            className="text-sm font-medium text-accent hover:underline"
          >
            Request a new reset email
          </Link>
        </p>
      </div>
    );
  }

  if (done) {
    return (
      <div className="space-y-3 text-center" role="status">
        <h1 className="text-xl font-semibold">Password updated</h1>
        <p className="text-sm text-ink-soft">
          Your password has been changed and all sessions were signed out.
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
        <h1 className="text-xl font-semibold">Reset your password</h1>
        <p className="text-sm text-ink-soft">Choose a new password for your account.</p>
      </div>
      <form onSubmit={onSubmit} noValidate className="space-y-4">
        <AuthFormField
          id="new_password"
          label="New password"
          type="password"
          autoComplete="new-password"
          error={errors.new_password?.message}
          {...register("new_password")}
        />
        <AuthFormField
          id="confirmPassword"
          label="Confirm password"
          type="password"
          autoComplete="new-password"
          error={errors.confirmPassword?.message}
          {...register("confirmPassword")}
        />
        <FormError>{formError ?? undefined}</FormError>
        <Button type="submit" loading={isSubmitting} className="w-full">
          Update password
        </Button>
      </form>
    </div>
  );
}
