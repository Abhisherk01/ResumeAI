"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { describeApiError, describeUnknownError } from "@/components/auth/api-error-message";
import { AuthFormField } from "@/components/auth/auth-form-field";
import { useAuth } from "@/components/auth/auth-provider";
import { updateProfile } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { FormError } from "@/components/ui/form-error";
import { updateProfileSchema, type UpdateProfileInput } from "@/lib/auth/schemas";

/**
 * Display-name editor (P4-2). Two UX details worth their code:
 * - defaultValues prefill from the signed-in user, so the form is never
 *   empty and dirty-state ("Save" only when changed) comes free;
 * - on success the context updates via setUser, so the sidebar's name
 *   changes instantly without a router refresh.
 */
export function UpdateProfileForm() {
  const { user, setUser } = useAuth();
  const [formError, setFormError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<UpdateProfileInput>({
    resolver: zodResolver(updateProfileSchema),
    defaultValues: { name: user?.name ?? "" },
  });

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null);
    setSaved(false);
    try {
      const updated = await updateProfile(values);
      setUser(updated); // sidebar reflects the new name immediately
      setSaved(true);
    } catch (error) {
      setFormError(
        error instanceof ApiError ? describeApiError(error) : describeUnknownError()
      );
    }
  });

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-4">
      <div className="space-y-1">
        <h2 className="text-base font-semibold">Profile</h2>
        <p className="text-sm text-ink-soft">Your email address cannot be changed yet.</p>
      </div>
      <AuthFormField
        id="name"
        label="Display name"
        type="text"
        autoComplete="name"
        error={errors.name?.message}
        {...register("name")}
      />
      <FormError>{formError ?? undefined}</FormError>
      {saved && (
        <p role="status" className="text-sm text-success">
          Profile updated.
        </p>
      )}
      <Button type="submit" loading={isSubmitting} disabled={!isDirty}>
        Save changes
      </Button>
    </form>
  );
}
