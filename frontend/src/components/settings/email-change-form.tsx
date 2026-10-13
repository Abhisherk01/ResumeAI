"use client";

/**
 * Email-change request form (Phase 10, D24). Two contracts copied from the
 * password-change form: invalid_current_password lands INLINE on the
 * current-password field, and EVERY other outcome - including a taken or
 * unknown target address (D24c) - shows the same check-your-inbox state,
 * because the backend's response is identical by design and this UI must
 * not leak what the API refuses to.
 */

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { describeApiError, describeUnknownError } from "@/components/auth/api-error-message";
import { AuthFormField } from "@/components/auth/auth-form-field";
import { requestEmailChange } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { FormError } from "@/components/ui/form-error";
import {
  requestEmailChangeSchema,
  type RequestEmailChangeInput,
} from "@/lib/auth/schemas";

export function EmailChangeForm() {
  const [formError, setFormError] = useState<string | null>(null);
  const [requested, setRequested] = useState(false);
  const {
    register,
    handleSubmit,
    setError,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<RequestEmailChangeInput>({
    resolver: zodResolver(requestEmailChangeSchema),
  });

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null);
    setRequested(false);
    try {
      await requestEmailChange(values);
      reset();
      setRequested(true);
    } catch (error) {
      if (error instanceof ApiError && error.code === "invalid_current_password") {
        setError("current_password", {
          type: "manual",
          message: "Current password is incorrect.",
        });
      } else {
        setFormError(
          error instanceof ApiError ? describeApiError(error) : describeUnknownError()
        );
      }
    }
  });

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-4">
      <div className="space-y-1">
        <h2 className="text-base font-semibold">Email address</h2>
        <p className="text-sm text-ink-soft">
          We send a confirmation link to the new address; the change applies
          only after you open it.
        </p>
      </div>
      <AuthFormField
        id="email_new_address"
        label="New email address"
        type="email"
        autoComplete="email"
        error={errors.new_email?.message}
        {...register("new_email")}
      />
      <AuthFormField
        id="email_current_password"
        label="Current password"
        type="password"
        autoComplete="current-password"
        error={errors.current_password?.message}
        {...register("current_password")}
      />
      <FormError>{formError ?? undefined}</FormError>
      {requested && (
        <p role="status" className="text-sm text-success">
          If that email address can be used, a confirmation link has been sent
          to it.
        </p>
      )}
      <Button type="submit" loading={isSubmitting}>
        Send confirmation link
      </Button>
    </form>
  );
}
