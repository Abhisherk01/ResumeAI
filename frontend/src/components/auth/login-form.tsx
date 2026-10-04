"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import {
  describeApiError,
  describeUnknownError,
} from "@/components/auth/api-error-message";
import { AuthFormField } from "@/components/auth/auth-form-field";
import { login } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { FormError } from "@/components/ui/form-error";
import { loginSchema, type LoginInput } from "@/lib/auth/schemas";

export function LoginForm() {
  const router = useRouter();
  const [formError, setFormError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginInput>({ resolver: zodResolver(loginSchema) });

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null);
    try {
      await login(values);
      // 7B-1: refresh so the (app) server gate re-reads the fresh cookie.
      router.push("/dashboard");
      router.refresh();
    } catch (error) {
      setFormError(
        error instanceof ApiError
          ? describeApiError(error)
          : describeUnknownError()
      );
    }
  });

  return (
    <div className="space-y-5">
      <div className="space-y-1">
        <h1 className="text-xl font-semibold">Sign in</h1>
        <p className="text-sm text-ink-soft">Welcome back. Sign in to continue.</p>
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
        <AuthFormField
          id="password"
          label="Password"
          type="password"
          autoComplete="current-password"
          error={errors.password?.message}
          {...register("password")}
        />
        <FormError>{formError ?? undefined}</FormError>
        <Button type="submit" loading={isSubmitting} className="w-full">
          Sign in
        </Button>
      </form>
      <div className="flex items-center justify-between text-sm">
        <Link href="/forgot-password" className="text-accent hover:underline">
          Forgot password?
        </Link>
        <Link href="/register" className="text-accent hover:underline">
          Create account
        </Link>
      </div>
    </div>
  );
}
