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
import { register as registerAccount } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { FormError } from "@/components/ui/form-error";
import { registerSchema, type RegisterInput } from "@/lib/auth/schemas";

export function RegisterForm() {
  const [sent, setSent] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterInput>({ resolver: zodResolver(registerSchema) });

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null);
    try {
      await registerAccount(values);
      // 7B-2: no session exists yet; the email is the next step. The
      // backend response is generic by design, so one inbox state covers
      // every outcome.
      setSent(true);
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
          If this email address can be verified, a verification link has been
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
        <h1 className="text-xl font-semibold">Create your account</h1>
        <p className="text-sm text-ink-soft">Start analyzing resumes in minutes.</p>
      </div>
      <form onSubmit={onSubmit} noValidate className="space-y-4">
        <AuthFormField
          id="name"
          label="Name"
          type="text"
          autoComplete="name"
          error={errors.name?.message}
          {...register("name")}
        />
        <AuthFormField
          id="email"
          label="Email"
          type="email"
          autoComplete="email"
          error={errors.email?.message}
          {...register("email")}
        />
        <AuthFormField
          id="password"
          label="Password"
          type="password"
          autoComplete="new-password"
          error={errors.password?.message}
          {...register("password")}
        />
        <FormError>{formError ?? undefined}</FormError>
        <Button type="submit" loading={isSubmitting} className="w-full">
          Create account
        </Button>
      </form>
      <p className="text-center text-sm text-ink-soft">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-accent hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}
