/**
 * Zod mirrors of the backend's Pydantic schemas (Phase 3 Step 4, Decision D;
 * Phase 4 Step 1 adds the account schemas).
 *
 * The bounds are DUPLICATED ON PURPOSE, not shared: frontend and backend
 * deploy independently, and the backend copy remains the authority — this
 * layer exists for instant, offline feedback (8-128 password, name <= 100,
 * NIST 800-63B: length, no composition rules).
 *
 * resetPasswordSchema adds a confirmPassword field the backend doesn't
 * have — classic UX — and auth.ts sends only the fields the API expects.
 */

import { z } from "zod";

export const emailField = z.string().trim().min(1, "Email is required.").email(
  "Enter a valid email address."
);

export const passwordField = z
  .string()
  .min(8, "Password must be at least 8 characters.")
  .max(128, "Password must be at most 128 characters.");

export const registerSchema = z.object({
  email: emailField,
  password: passwordField,
  name: z
    .string()
    .trim()
    .min(1, "Name is required.")
    .max(100, "Name must be at most 100 characters."),
});

export const loginSchema = z.object({
  email: emailField,
  // Min 1 only: login must not leak the registration policy.
  password: z.string().min(1, "Password is required.").max(128),
});

export const forgotPasswordSchema = z.object({ email: emailField });

export const resetPasswordSchema = z
  .object({
    token: z.string().min(1, "Reset token is missing."),
    new_password: passwordField,
    confirmPassword: z.string().min(1, "Please confirm the password."),
  })
  .refine((data) => data.new_password === data.confirmPassword, {
    message: "Passwords do not match.",
    path: ["confirmPassword"],
  });

export const verifyEmailSchema = z.object({
  token: z.string().min(1, "Verification token is missing."),
});

/** Phase 4: display-name change mirrors UpdateProfileRequest (backend
 * trims too — the trim here is for instant feedback only). */
export const updateProfileSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, "Name is required.")
    .max(100, "Name must be at most 100 characters."),
});

/** Phase 4: password change mirrors ChangePasswordRequest. The backend
 * enforces min 1 on current (it only verifies it); the client demands
 * non-empty so the user gets feedback before a wasted round-trip. */
export const changePasswordSchema = z
  .object({
    current_password: z.string().min(1, "Current password is required.").max(128),
    new_password: passwordField,
    confirmPassword: z.string().min(1, "Please confirm the new password."),
  })
  .refine((data) => data.new_password === data.confirmPassword, {
    message: "Passwords do not match.",
    path: ["confirmPassword"],
  });

export type RegisterInput = z.infer<typeof registerSchema>;
export type LoginInput = z.infer<typeof loginSchema>;
export type ForgotPasswordInput = z.infer<typeof forgotPasswordSchema>;
export type VerifyEmailInput = z.infer<typeof verifyEmailSchema>;
/** The exact payload the backend endpoint expects (no confirmPassword). */
export type ResetPasswordPayload = {
  token: string;
  new_password: string;
};
export type UpdateProfileInput = z.infer<typeof updateProfileSchema>;
/** The exact payload for the password-change endpoint (no confirmPassword). */
export type ChangePasswordPayload = {
  current_password: string;
  new_password: string;
};

/** Full form shape for the password-change form (includes confirmPassword). */
export type ChangePasswordInput = z.infer<typeof changePasswordSchema>;
