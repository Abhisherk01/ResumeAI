"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { describeApiError, describeUnknownError } from "@/components/auth/api-error-message";
import { AuthFormField } from "@/components/auth/auth-form-field";
import { changePassword } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { FormError } from "@/components/ui/form-error";
import {
  changePasswordSchema,
  type ChangePasswordInput,
  type ChangePasswordPayload,
} from "@/lib/auth/schemas";

/**
 * Authenticated password change (P4-3/P4-5). The interesting branch is the
 * 400 invalid_current_password: it must land INLINE on the current-password
 * field (the backend built this error code exactly for that), while every
 * other failure lands in the shared form error. On success the user is
 * told other sessions were signed out — the P4-3 semantics, stated plainly.
 */
export function ChangePasswordForm() {
  const [formError, setFormError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const {
    register,
    handleSubmit,
    setError,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ChangePasswordInput>({
    resolver: zodResolver(changePasswordSchema),
  });

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null);
    setSaved(false);
    const payload: ChangePasswordPayload = {
      current_password: values.current_password,
      new_password: values.new_password,
    };
    try {
      await changePassword(payload);
      reset(); // clear the fields — the old password is dead now
      setSaved(true);
    } catch (error) {
      if (error instanceof ApiError && error.code === "invalid_current_password") {
        setError("current_password", {
          type: "manual",
          message: "Current password is incorrect.",
        });
      } else {
        setFormError(
          error instanceof ApiError
            ? describeApiError(error)
            : describeUnknownError()
        );
      }
    }
  });

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-4">
      <div className="space-y-1">
        <h2 className="text-base font-semibold">Password</h2>
        <p className="text-sm text-ink-soft">
          Changing your password signs out all other devices.
        </p>
        <p className="text-xs text-ink-soft">
        Forgot it instead? Use &quot;Forgot password?&quot; on the sign-in page.
        </p>
      </div>
      <AuthFormField
        id="current_password"
        label="Current password"
        type="password"
        autoComplete="current-password"
        error={errors.current_password?.message}
        {...register("current_password")}
      />
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
        label="Confirm new password"
        type="password"
        autoComplete="new-password"
        error={errors.confirmPassword?.message}
        {...register("confirmPassword")}
      />
      <FormError>{formError ?? undefined}</FormError>
      {saved && (
        <p role="status" className="text-sm text-success">
          Password updated. Other sessions were signed out.
        </p>
      )}
      <Button type="submit" loading={isSubmitting}>Update password</Button>
    </form>
  );
}
